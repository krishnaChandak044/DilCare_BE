import math
from datetime import timedelta

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from family.models import FamilyLink, FamilyMembership

from .models import (
    FamilyLocationPermission,
    GeofenceEvent,
    LocationShareSetting,
    UserGeofence,
    UserLocationPing,
)
from .serializers import (
    FamilyHistoryQuerySerializer,
    FamilyLiveLocationSerializer,
    FamilyLocationPermissionSerializer,
    GeofenceEventSerializer,
    LocationShareSettingSerializer,
    UserGeofenceSerializer,
    UserLocationPingCreateSerializer,
    UserLocationPingSerializer,
    apply_precision,
    ensure_permission_for_link,
    resolve_precision_mode,
)


def _haversine_distance_m(lat1, lon1, lat2, lon2):
    earth_radius_m = 6371000
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    delta_phi = math.radians(float(lat2) - float(lat1))
    delta_lambda = math.radians(float(lon2) - float(lon1))

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return earth_radius_m * c


def _evaluate_geofence_events(user, ping):
    geofences = UserGeofence.objects.filter(user=user, is_active=True)
    created_events = []

    for geofence in geofences:
        distance_m = _haversine_distance_m(
            geofence.center_latitude,
            geofence.center_longitude,
            ping.latitude,
            ping.longitude,
        )
        is_inside = distance_m <= geofence.radius_m

        last_event = GeofenceEvent.objects.filter(
            geofence=geofence,
            user=user,
        ).order_by("-occurred_at").first()

        was_inside = bool(last_event and last_event.event_type == "enter")

        if is_inside and not was_inside and geofence.notify_on_enter:
            event = GeofenceEvent.objects.create(
                geofence=geofence,
                user=user,
                ping=ping,
                event_type="enter",
                distance_m=distance_m,
            )
            created_events.append(event)

        if (not is_inside) and was_inside and geofence.notify_on_exit:
            event = GeofenceEvent.objects.create(
                geofence=geofence,
                user=user,
                ping=ping,
                event_type="exit",
                distance_m=distance_m,
            )
            created_events.append(event)

    return created_events


class LocationShareSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        settings_obj, _ = LocationShareSetting.objects.get_or_create(user=request.user)
        return Response(LocationShareSettingSerializer(settings_obj).data)

    def patch(self, request):
        settings_obj, _ = LocationShareSetting.objects.get_or_create(user=request.user)
        serializer = LocationShareSettingSerializer(settings_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UploadLocationPingView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "location_ping_upload"

    def post(self, request):
        serializer = UserLocationPingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ping = serializer.save(user=request.user)
        geofence_events = _evaluate_geofence_events(request.user, ping)

        return Response(
            {
                "ping": UserLocationPingSerializer(ping).data,
                "geofence_events_created": len(geofence_events),
            },
            status=status.HTTP_201_CREATED,
        )


class MyLatestLocationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        latest = UserLocationPing.objects.filter(user=request.user).order_by("-recorded_at").first()
        if not latest:
            return Response({"detail": "No location pings yet."}, status=status.HTTP_404_NOT_FOUND)
        return Response(UserLocationPingSerializer(latest).data)


class FamilyPermissionListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FamilyLocationPermissionSerializer

    def get_queryset(self):
        links = FamilyLink.objects.filter(parent=self.request.user, is_active=True).select_related("child")
        permission_ids = []
        for link in links:
            permission = ensure_permission_for_link(link)
            permission_ids.append(permission.id)
        return FamilyLocationPermission.objects.filter(id__in=permission_ids).select_related("family_link__child")


class FamilyPermissionUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FamilyLocationPermissionSerializer
    queryset = FamilyLocationPermission.objects.select_related("family_link")

    def get_object(self):
        obj = super().get_object()
        if obj.family_link.parent != self.request.user:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You can only manage permissions for your own family links.")
        return obj


class FamilyLiveLocationsView(APIView):
    """
    GET /api/v1/location/family/live/
    Latest locations for other members in the same family group (Family + FamilyMembership).
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "location_live"

    def get(self, request):
        max_age_minutes = request.query_params.get("max_age_minutes", "30")
        try:
            max_age_minutes = max(1, min(720, int(max_age_minutes)))
        except (ValueError, TypeError):
            max_age_minutes = 30

        try:
            my_membership = FamilyMembership.objects.select_related("family").get(user=request.user)
        except FamilyMembership.DoesNotExist:
            return Response([])

        payload = []
        now = timezone.now()

        others = (
            FamilyMembership.objects.filter(family=my_membership.family)
            .exclude(user=request.user)
            .select_related("user")
        )

        for m in others:
            member_user = m.user
            share_settings, _ = LocationShareSetting.objects.get_or_create(user=member_user)
            if not share_settings.sharing_enabled:
                continue

            latest_ping = (
                UserLocationPing.objects.filter(user=member_user).order_by("-recorded_at").first()
            )
            if not latest_ping:
                continue

            age = now - latest_ping.recorded_at
            window_m = min(max_age_minutes, share_settings.live_visibility_minutes)
            is_live = age <= timedelta(minutes=window_m)
            if not is_live:
                continue

            precision_mode = share_settings.share_precision
            latitude, longitude = apply_precision(latest_ping.latitude, latest_ping.longitude, precision_mode)

            display_name = member_user.get_full_name() or member_user.email
            rel_label = (m.nickname or "").strip() or m.get_role_display()

            payload.append(
                {
                    "member_id": member_user.id,
                    "member_name": display_name,
                    "parent_id": member_user.id,
                    "parent_name": display_name,
                    "phone": member_user.phone or "",
                    "nickname": m.nickname or "",
                    "role": m.role,
                    "relationship": rel_label,
                    "latitude": latitude,
                    "longitude": longitude,
                    "accuracy_m": latest_ping.accuracy_m,
                    "speed_kmh": latest_ping.speed_kmh,
                    "battery_level": latest_ping.battery_level,
                    "is_charging": latest_ping.is_charging,
                    "recorded_at": latest_ping.recorded_at,
                    "is_live": is_live,
                    "precision_applied": precision_mode,
                }
            )

        serializer = FamilyLiveLocationSerializer(payload, many=True)
        return Response(serializer.data)


class FamilyLocationHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "location_history"

    def get(self, request, member_id):
        link = FamilyLink.objects.select_related("parent").filter(
            child=request.user,
            parent_id=member_id,
            is_active=True,
        ).first()
        if not link:
            return Response(
                {"detail": "You do not have access to this member's location history."},
                status=status.HTTP_403_FORBIDDEN,
            )

        permission = ensure_permission_for_link(link)
        if not permission.can_view_history:
            return Response(
                {"detail": "History sharing is disabled for this member."},
                status=status.HTTP_403_FORBIDDEN,
            )

        query_serializer = FamilyHistoryQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        hours = query_serializer.validated_data["hours"]
        limit = query_serializer.validated_data["limit"]

        share_settings, _ = LocationShareSetting.objects.get_or_create(user=link.parent)
        if not share_settings.sharing_enabled:
            return Response(
                {"detail": "Location sharing is disabled by this member."},
                status=status.HTTP_403_FORBIDDEN,
            )

        effective_hours = min(
            hours,
            permission.history_window_hours,
            share_settings.history_retention_hours,
        )

        since = timezone.now() - timedelta(hours=effective_hours)
        pings = (
            UserLocationPing.objects.filter(user=link.parent, recorded_at__gte=since)
            .order_by("-recorded_at")[:limit]
        )

        precision_mode = resolve_precision_mode(share_settings, permission)
        history_items = []
        for ping in pings:
            latitude, longitude = apply_precision(ping.latitude, ping.longitude, precision_mode)
            history_items.append(
                {
                    "id": ping.id,
                    "latitude": latitude,
                    "longitude": longitude,
                    "accuracy_m": ping.accuracy_m,
                    "speed_kmh": ping.speed_kmh if permission.can_view_speed else None,
                    "battery_level": ping.battery_level if permission.can_view_battery else None,
                    "is_charging": ping.is_charging if permission.can_view_battery else None,
                    "source": ping.source,
                    "is_mocked": ping.is_mocked,
                    "recorded_at": ping.recorded_at,
                }
            )

        return Response(
            {
                "member_id": link.parent_id,
                "member_name": link.parent.get_full_name() or link.parent.email,
                "relationship": link.get_relationship_display(),
                "effective_window_hours": effective_hours,
                "precision_applied": precision_mode,
                "count": len(history_items),
                "items": history_items,
            }
        )


class UserGeofenceListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserGeofenceSerializer

    def get_queryset(self):
        return UserGeofence.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserGeofenceDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserGeofenceSerializer

    def get_queryset(self):
        return UserGeofence.objects.filter(user=self.request.user)


class GeofenceEventListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GeofenceEventSerializer

    def get_queryset(self):
        return GeofenceEvent.objects.filter(user=self.request.user).select_related("geofence")
