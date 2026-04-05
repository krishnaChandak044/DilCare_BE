from django.urls import path

from .views import (
    FamilyLiveLocationsView,
    FamilyLocationHistoryView,
    FamilyPermissionListView,
    FamilyPermissionUpdateView,
    GeofenceEventListView,
    LocationShareSettingsView,
    MyLatestLocationView,
    UploadLocationPingView,
    UserGeofenceDetailView,
    UserGeofenceListCreateView,
)

app_name = "location"

urlpatterns = [
    path("settings/", LocationShareSettingsView.as_view(), name="location-settings"),
    path("pings/", UploadLocationPingView.as_view(), name="location-ping-upload"),
    path("me/latest/", MyLatestLocationView.as_view(), name="location-my-latest"),
    path("family/live/", FamilyLiveLocationsView.as_view(), name="location-family-live"),
    path("family/<int:member_id>/history/", FamilyLocationHistoryView.as_view(), name="location-family-history"),
    path("permissions/", FamilyPermissionListView.as_view(), name="location-permissions-list"),
    path("permissions/<uuid:pk>/", FamilyPermissionUpdateView.as_view(), name="location-permissions-update"),
    path("geofences/", UserGeofenceListCreateView.as_view(), name="location-geofence-list-create"),
    path("geofences/<uuid:pk>/", UserGeofenceDetailView.as_view(), name="location-geofence-detail"),
    path("geofences/events/", GeofenceEventListView.as_view(), name="location-geofence-events"),
]
