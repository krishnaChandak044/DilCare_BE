"""
User URL routes — /api/v1/user/
"""
from django.urls import path
from accounts.views import ProfileView, LinkCodeView, RegenerateLinkCodeView

urlpatterns = [
    path("profile/", ProfileView.as_view(), name="user-profile"),
    path("link-code/", LinkCodeView.as_view(), name="user-link-code"),
    path("link-code/regenerate/", RegenerateLinkCodeView.as_view(), name="user-link-code-regenerate"),
]
