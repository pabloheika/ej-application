from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from ej_profiles.models import Profile
from ej_users.serializers import UserAuthSerializer, UsersSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .manager import convert_anonymous_participation_to_regular_user
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

        user = None
        try:
            if "secret_id" in request.data:
                user = User.objects.get(secret_id=request.data["secret_id"])
            elif "email" in request.data:
                user = User.objects.get(email=request.data["email"])
            else:
                return Response(
                    {"error": _("Email or secret_id is required.")}, status=400
                )
        except User.DoesNotExist:
            return Response({"error": _("User was not found.")}, status=404)

        if user and not user.check_password(request.data["password"]):
            return Response({"error": _("The password is incorrect")}, status=400)

        try:
            tokens = EJTokens(user)
            response_data = (
                {"name": user.name, "email": user.email, **tokens.data}
                if "secret_id" in request.data
                else tokens.data
            )
            return Response(response_data)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UsersSerializer

    permission_classes_by_action = {"create": [AllowAny], "list": [IsAdminUser]}

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[AllowAny],
        url_path="user",
    )
    def get_user(self, request):
        email = request.query_params.get("email")
        secret_id = request.query_params.get("secret_id")

        if email:
            user = get_object_or_404(User, email=email)
        elif secret_id:
            user = get_object_or_404(User, secret_id=secret_id)
        else:
            return Response({"error": "Email ou secret_id é necessário."}, status=400)

        serializer = self.get_serializer(user)
        return Response(serializer.data)

    def handle_unique_secret_id_error(self, serializer, request):
        if serializer.errors.get("secret_id")[0].code == "invalid":
            anonymous_user = User.objects.get(secret_id=request.data["secret_id"])
            anonymous_user.secret_id = None
            anonymous_user.save()

            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                anonymous_user.secret_id = request.data["secret_id"]
                anonymous_user.save()
                return Response(serializer.errors, status=400)

            user = serializer.save()
            self.check_profile_and_convert(anonymous_user, user, request)
            return self.build_user_response(user)
        return None

    def check_profile_and_convert(self, anonymous_user, user, request):
        self.check_profile(user, request)
        user = convert_anonymous_participation_to_regular_user(anonymous_user, user)
        user.save()

    def handle_invalid_email_error(self, request):
        user_secret = User.objects.get(secret_id=request.data["secret_id"])
        user_email = User.objects.get(email=request.data["email"])
        if user_secret != user_email:
            user_secret.secret_id = None
            user_secret.save()
            user_email.secret_id = request.data["secret_id"]
            user_email.save()

            self.check_profile_and_convert(user_secret, user_email, request)
            return self.build_user_response(user_email)
        return None

    def build_user_response(self, user):
        tokens = EJTokens(user)
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "secret_id": user.secret_id,
            "anonymous": user.anonymous,
            **tokens.data,
        }

    def create(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            secret_id_error = serializer.errors.get("secret_id")
            email_error = serializer.errors.get("email")
            if secret_id_error and not email_error:
                response = self.handle_unique_secret_id_error(serializer, request)
                if response:
                    return Response(response)
            elif secret_id_error and email_error and email_error[0].code == "invalid":
                response = self.handle_invalid_email_error(request)
                if response:
                    return Response(response)
            return Response(serializer.errors, status=400)

        user = serializer.save()
        self.check_profile(user, request)
        return Response(self.build_user_response(user))

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
