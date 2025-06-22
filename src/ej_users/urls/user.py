from django.urls import path
from ..views import user
from ..api import RecoverPasswordAPIView

app_name = "ej_users"

urlpatterns = [
    path(
        "login/",
        user.LoginView.as_view(),
        name="login",
    ),
    path(
        "register/",
        user.RegisterView.as_view(),
        name="register",
    ),
    path(
        "recover-password/",
        user.RecoverPasswordView.as_view(),
        name="recover-password",
    ),
    path(
        "recover-password/<str:token>/",
        user.RecoverPasswordToken.as_view(),
        name="recover-password-token",
    ),
    path(
        "login/api-key/",
        user.api_key,
        name="api-key",
    ),
    path("api/v1/recover-password/", 
         RecoverPasswordAPIView.as_view(), 
         name="recover-password-api"),
]
