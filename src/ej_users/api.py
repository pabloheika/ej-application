from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from ej_users.serializers import RecoverPasswordRequestSerializer, UserAuthSerializer, UsersSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, UserSecretIdManager
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from dataclasses import dataclass
from typing import Any
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import get_template
from django.urls import reverse
from django.contrib.auth import get_user_model
from ej_users.models import PasswordResetToken
import logging

log = logging.getLogger("ej")
User = get_user_model()


@dataclass
class EJTokens:
    """
    Manage EJ API authentication tokens.
    """

    user: Any
    access_token: str = ""
    refresh_token: str = ""
    data = {}
    user_data = {}

    def __post_init__(self):
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.refresh_token = str(refresh)
        self.data = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "has_completed_registration": self.user.has_completed_registration,
        }
        self.user_data = {
            "id": self.user.id,
            "name": self.user.name,
            "email": self.user.email,
            **self.data,
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
        """
        Returns an access_token and refresh_token for an user.
        """
        serializer = UserAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        try:
            user = UserSecretIdManager.get_user(request.data)
        except User.DoesNotExist:
            return Response({"error": _("User was not found.")}, status=404)

        if not user.check_password(request.data.get("password")):
            return Response({"error": _("The password is incorrect")}, status=400)

        try:
            tokens = EJTokens(user)
            return Response(tokens.data)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class UsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UsersSerializer

    permission_classes_by_action = {
        "create": [AllowAny],
        "update": [AllowAny],
        "list": [IsAdminUser],
    }

    def update(self, request, pk=None):

        if pk.isdigit():
            return Response(status=501)

        try:
            temporary_user: User = UserSecretIdManager.get_user({"secret_id": pk})
        except User.DoesNotExist as e:
            return Response({"error": str(e)}, status=404)

        if temporary_user.has_completed_registration:
            return Response(
                {"error": _("User already has completed the registration process.")},
                status=403,
            )

        UserSecretIdManager.merge_unique_user_with(temporary_user, request.data)
        return Response({"status": "ok"}, status=200)

    def create(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        user = serializer.save()
        tokens = EJTokens(user)
        return Response(tokens.user_data, status=201)

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


class RecoverPasswordAPIView(APIView):
    """
    POST /api/v1/users/recover-password/
    Body: { "email": "user@email.com" }
    Always returns 200 with a generic message.
    """
    permission_classes = []

    def post(self, request):
        serializer = RecoverPasswordRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = User.objects.filter(email=email).first()
        if user:
            token = PasswordResetToken(user)
            from_email = settings.DEFAULT_FROM_EMAIL
            if getattr(settings, "DEFAULT_FROM_NAME", None):
                from_email = f"{settings.DEFAULT_FROM_NAME} <{from_email}>"
            path = reverse("auth:recover-password-token", kwargs={"token": token.url})
            template = get_template("ej_users/recover-password-message.jinja2")
            url = f"{request.scheme}://{request.get_host()}{path}"
            email_body = template.render({"url": url}, request=request)
            send_mail(
                subject=_("Please reset your password"),
                message=email_body,
                from_email=from_email,
                recipient_list=[email],
            )
            log.info(f"user {user} requested a password reset.")
        else:
            log.info(f"Password reset requested for non-existent email: {email}")

        return Response(
            {"message": _("If the email exists, a password reset link was sent.")},
            status=status.HTTP_200_OK,
        )
