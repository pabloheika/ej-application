from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from ej_profiles.models import Profile
from ej_users.serializers import UserAuthSerializer, UsersSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from dataclasses import dataclass
from typing import Any


@dataclass
class EJTokens:

    """
    Manage EJ API authentication tokens.
    """

    user: Any
    access_token: str = ""
    refresh_token: str = ""
    data = {}

    def __post_init__(self):
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.refresh_token = str(refresh)
        self.data = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
        }


class TokenViewSet(viewsets.ViewSet):
    serializer_class = UserAuthSerializer

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def login(self, request):
        # TODO: migrates all EJ API clients to token/token_refresh endpoints.
        return self.token(request)

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[AllowAny],
        url_path="refresh-token",
    )
    def refresh_token(self, request):
        view = TokenRefreshView()
        view.request = request
        view.format_kwarg = "json"
        return view.post(request)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def token(self, request):

        serializer = UserAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        try:
            user = User.objects.get(email=request.data["email"])
        except User.DoesNotExist:
            return Response({"error": _("User was not found.")}, status=500)

        checked_password = user.check_password(request.data["password"])
        if not checked_password:
            return Response({"error": _("The password is incorrect")}, status=400)

        try:
            tokens = EJTokens(user)
            return Response(tokens.data)
        except Exception as e:
            return Response({"error": e}, status=500)


class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UsersSerializer

    permission_classes_by_action = {"create": [AllowAny], "list": [IsAdminUser]}

    def create(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        user = serializer.save()
        self.check_profile(user, request)
        tokens = EJTokens(user)
        response = {"id": user.id, "name": user.name, "email": user.email, **tokens.data}
        return Response(response)

    def check_profile(self, user, request):
        phone_number = request.data.get("phone_number", None)
        profile, _ = Profile.objects.get_or_create(user=user)

        if phone_number:
            profile.phone_number = phone_number
            profile.save()

    def get_permissions(self):
        try:
            # return permission_classes depending on `action`
            return [
                permission()
                for permission in self.permission_classes_by_action[self.action]
            ]
        except KeyError:
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]
