"""JWT authentication views: register, login, refresh, logout.

Uses djangorestframework-simplejwt under the hood with custom responses.
"""

from django.contrib.auth import get_user_model
from rest_framework import permissions, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer

from .serializers import (
    LoginSerializer,
    LogoutSerializer,
    PublicUserSerializer,
    RefreshSerializer,
    RegisterSerializer,
)
from .utils import generate_user_tokens

User = get_user_model()


class RegisterView(APIView):
    """Register a new user account (client role by default)."""

    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        tags=["auth"],
        request=RegisterSerializer,
        responses={
            201: inline_serializer(
                name="RegisterResponse",
                fields={
                    "access_token": serializers.CharField(),
                    "refresh_token": serializers.CharField(),
                    "user": PublicUserSerializer(),
                },
            )
        },
        description="Register a new user and return JWT tokens along with the public user payload.",
    )
    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Optionally auto-login on registration by returning tokens
        tokens = generate_user_tokens(user)
        data = {
            **tokens,
            "user": PublicUserSerializer(user).data,
        }
        return Response(data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Authenticate user with phone_number and password, return JWT tokens."""

    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        tags=["auth"],
        request=LoginSerializer,
        responses={
            200: inline_serializer(
                name="LoginResponse",
                fields={
                    "access_token": serializers.CharField(),
                    "refresh_token": serializers.CharField(),
                    "user": PublicUserSerializer(),
                },
            )
        },
        description="Login with phone_number and password to obtain JWT tokens.",
    )
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        payload = serializer.save()
        # payload already includes access_token, refresh_token, user
        return Response(payload, status=status.HTTP_200_OK)


class TokenRefreshView(APIView):
    """Renew access token using a valid refresh token."""

    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        tags=["auth"],
        request=RefreshSerializer,
        responses={200: inline_serializer(name="RefreshResponse", fields={"access_token": serializers.CharField()})},
        description="Exchange a valid refresh token for a new access token.",
    )
    def post(self, request, *args, **kwargs):
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            refresh = RefreshToken(serializer.validated_data["refresh"])  # type: ignore[arg-type]
            access_token = str(refresh.access_token)
            return Response({"access_token": access_token}, status=status.HTTP_200_OK)
        except TokenError as exc:  # includes expired/blacklisted
            raise InvalidToken(detail={"detail": "Invalid or expired refresh token.", "code": "invalid_refresh"}) from exc


class LogoutView(APIView):
    """Invalidate a refresh token by blacklisting it (logout)."""

    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(
        tags=["auth"],
        request=LogoutSerializer,
        responses={200: inline_serializer(name="LogoutResponse", fields={"detail": serializers.CharField()})},
        description="Blacklist a refresh token to log the user out.",
    )
    def post(self, request, *args, **kwargs):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = RefreshToken(serializer.validated_data["refresh"])  # type: ignore[arg-type]
            token.blacklist()
        except TokenError as exc:
            raise InvalidToken(detail={"detail": "Invalid or already blacklisted token.", "code": "invalid_token"}) from exc
        return Response({"detail": "Logged out successfully."}, status=status.HTTP_200_OK)
