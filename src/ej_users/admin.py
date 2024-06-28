from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(AuthUserAdmin):
    list_display = ("name", "email", "is_superuser", "secret_id", "anonymous")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "name",
                    "display_name",
                    "password",
                    "secret_id",
                    "anonymous",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {"classes": ("wide",), "fields": ("email", "name", "password1", "password2")},
        ),
    )
    search_fields = ["name", "email"]
    ordering = ["email"]
