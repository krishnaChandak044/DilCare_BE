"""
Accounts — API Views for auth and profile management.
Enhanced with settings, devices, logout, and change password.
"""
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import UserSettings, UserDevice
from .serializers import (
    RegisterSerializer,
    UserProfileSerializer,
    LinkCodeSerializer,
    UserSettingsSerializer,
    UserDeviceSerializer,
    LogoutSerializer,
    ChangePasswordSerializer,
)


class RegisterView(generics.CreateAPIView):
    """
    POST /api/v1/auth/register/
    Creates a new user account and returns JWT tokens.
    """
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

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
