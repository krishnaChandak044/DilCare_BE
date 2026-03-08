"""
User URL routes — /api/v1/user/
"""
from django.urls import path
from accounts.views import (
    ProfileView,
    LinkCodeView,
    RegenerateLinkCodeView,
    SettingsView,
    ChangePasswordView,
    DeviceListCreateView,
    DeviceDeleteView,
    MeView,
)

urlpatterns = [
    path("me/", MeView.as_view(), name="user-me"),
    path("profile/", ProfileView.as_view(), name="user-profile"),
    path("settings/", SettingsView.as_view(), name="user-settings"),
    path("change-password/", ChangePasswordView.as_view(), name="user-change-password"),
    path("link-code/", LinkCodeView.as_view(), name="user-link-code"),
    path("link-code/regenerate/", RegenerateLinkCodeView.as_view(), name="user-link-code-regenerate"),
    path("devices/", DeviceListCreateView.as_view(), name="user-devices"),
    path("devices/<str:token>/", DeviceDeleteView.as_view(), name="user-device-delete"),
]
