"""
Accounts — API Views for auth and profile management.
"""
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, UserProfileSerializer, LinkCodeSerializer


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


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/v1/user/profile/  → Retrieve profile
    PUT  /api/v1/user/profile/  → Update profile
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


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
