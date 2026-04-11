"""
Accounts — API Views for auth and profile management.
Enhanced with settings, devices, logout, and change password.
"""
from rest_framework import generics, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenObtainPairView
from django.utils import timezone

from .models import UserSettings, UserDevice, Notification, NotificationPreference
from .serializers import (
    RegisterSerializer,
    UserProfileSerializer,
    LinkCodeSerializer,
    UserSettingsSerializer,
    UserDeviceSerializer,
    LogoutSerializer,
    ChangePasswordSerializer,
    NotificationSerializer,
    NotificationPreferenceSerializer,
)


class RegisterView(generics.CreateAPIView):
    """
    POST /api/v1/auth/register/
    Creates a new user account and returns JWT tokens.
    """
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_register"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens immediately
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "message": "Registration successful",
                "user": UserProfileSerializer(user).data,
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    Blacklists the refresh token to logout the user.
    """
    permission_classes = [IsAuthenticated]


    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            refresh_token = RefreshToken(serializer.validated_data["refresh"])
            refresh_token.blacklist()
            return Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)
        except TokenError:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/v1/user/profile/  → Retrieve profile with settings
    PATCH /api/v1/user/profile/  → Update profile
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class SettingsView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/v1/user/settings/  → Get user settings
    PATCH /api/v1/user/settings/  → Update settings
    """
    serializer_class = UserSettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Get or create settings for the user
        settings, _ = UserSettings.objects.get_or_create(user=self.request.user)
        return settings


class ChangePasswordView(APIView):
    """
    POST /api/v1/user/change-password/
    Change the user's password.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)


class LinkCodeView(APIView):
    """
    GET  /api/v1/user/link-code/  → Get current link code
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = LinkCodeSerializer(request.user)
        return Response(serializer.data)


class RegenerateLinkCodeView(APIView):
    """
    POST /api/v1/user/link-code/regenerate/  → Generate a new link code
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        new_code = request.user.regenerate_link_code()
        return Response({"parent_link_code": new_code})


class DeviceListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/user/devices/  → List user's devices
    POST /api/v1/user/devices/  → Register a new device token
    """
    serializer_class = UserDeviceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserDevice.objects.filter(user=self.request.user, is_active=True)


class DeviceDeleteView(APIView):
    """
    DELETE /api/v1/user/devices/{token}/  → Deactivate a device
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, token):
        try:
            device = UserDevice.objects.get(
                user=request.user,
                device_token=token
            )
            device.is_active = False
            device.save(update_fields=['is_active'])
            return Response(status=status.HTTP_204_NO_CONTENT)
        except UserDevice.DoesNotExist:
            return Response(
                {"error": "Device not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class MeView(APIView):
    """
    GET /api/v1/user/me/  → Quick endpoint to check auth status
    Returns minimal user info.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": str(user.id),
            "email": user.email,
            "name": f"{user.first_name} {user.last_name}".strip() or "",
            "is_authenticated": True,
        })


class LoginView(TokenObtainPairView):
    """
    POST /api/v1/auth/login/
    JWT login endpoint with scoped rate limiting.
    """
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_login"

class NotificationViewSet(viewsets.ViewSet):
    """ViewSet for notification management."""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def register_token(self, request):
        """
        POST /api/v1/notifications/register_token/
        Register device token for push notifications.
        """
        try:
            token = request.data.get('device_token')
            platform = request.data.get('platform', 'android')
            app_version = request.data.get('app_version', '')

            if not token:
                return Response(
                    {'success': False, 'error': 'device_token required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update or create device token record
            device, created = UserDevice.objects.update_or_create(
                user=request.user,
                device_token=token,
                defaults={
                    'device_type': platform,
                    'is_active': True,
                }
            )

            return Response({
                'success': True,
                'message': 'Device token registered',
                'device_id': str(device.id),
            })

        except Exception as e:
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def history(self, request):
        """
        GET /api/v1/notifications/history/?limit=20&offset=0
        Get notification history for the user.
        """
        try:
            limit = int(request.query_params.get('limit', 20))
            offset = int(request.query_params.get('offset', 0))
            unread_only = request.query_params.get('unread_only', 'false').lower() == 'true'

            notifications = Notification.objects.filter(user=request.user)

            if unread_only:
                notifications = notifications.filter(read=False)

            total = notifications.count()
            notifications = notifications[offset:offset+limit]

            serializer = NotificationSerializer(notifications, many=True)

            return Response({
                'success': True,
                'total': total,
                'count': len(notifications),
                'offset': offset,
                'limit': limit,
                'notifications': serializer.data,
            })

        except Exception as e:
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def mark_as_read(self, request):
        """
        POST /api/v1/notifications/mark_as_read/
        Mark one or more notifications as read.
        """
        try:
            notification_ids = request.data.get('notification_ids', [])

            if not notification_ids:
                return Response(
                    {'success': False, 'error': 'notification_ids required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            updated = Notification.objects.filter(
                user=request.user,
                id__in=notification_ids
            ).update(
                read=True,
                read_at=timezone.now()
            )

            return Response({
                'success': True,
                'message': f'{updated} notifications marked as read',
                'updated_count': updated,
            })

        except Exception as e:
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def log_interaction(self, request):
        """
        POST /api/v1/notifications/log_interaction/
        Log notification interaction (opened/dismissed).
        """
        try:
            notification_id = request.data.get('notification_id')
            interaction_type = request.data.get('interaction_type', 'opened')

            if not notification_id:
                return Response(
                    {'success': False, 'error': 'notification_id required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            notification = Notification.objects.filter(
                user=request.user,
                id=notification_id
            ).first()

            if notification:
                if interaction_type == 'opened':
                    notification.mark_as_opened()
                elif interaction_type == 'read':
                    notification.mark_as_read()

            return Response({'success': True})

        except Exception as e:
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get', 'patch'])
    def preferences(self, request):
        """
        GET /api/v1/notifications/preferences/
        Get or update user notification preferences.
        """
        try:
            prefs, created = NotificationPreference.objects.get_or_create(
                user=request.user
            )

            if request.method == 'GET':
                serializer = NotificationPreferenceSerializer(prefs)
                return Response({
                    'success': True,
                    'preferences': serializer.data,
                })

            elif request.method == 'PATCH':
                serializer = NotificationPreferenceSerializer(
                    prefs,
                    data=request.data,
                    partial=True
                )
                if serializer.is_valid():
                    serializer.save()
                    return Response({
                        'success': True,
                        'message': 'Preferences updated',
                        'preferences': serializer.data,
                    })
                else:
                    return Response(
                        {'success': False, 'errors': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        except Exception as e:
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        """
        DELETE /api/v1/notifications/clear_all/
        Delete all notifications for the user.
        """
        try:
            count, _ = Notification.objects.filter(user=request.user).delete()
            return Response({
                'success': True,
                'message': f'Deleted {count} notifications',
                'deleted_count': count,
            })

        except Exception as e:
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )