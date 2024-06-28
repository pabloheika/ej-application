from datetime import datetime, timedelta
from logging import getLogger

from boogie.apps.users.models import AbstractUser
from django.utils.text import slugify
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

from .manager import UserManager
from .utils import random_name, token_factory

log = getLogger("ej")


class User(AbstractUser):
    """
    Default user model for EJ platform.
    """

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    email = models.EmailField(
        _("email address"), unique=True, help_text=_("Your e-mail address")
    )
    display_name = models.CharField(
        max_length=50,
        default=random_name,
        help_text=_("Name used to publicly identify user"),
    )
    username = property(lambda self: self.name or self.email.replace("@", "__"))
    agree_with_terms = models.BooleanField(
        default=False, help_text=_("Agree with terms"), verbose_name=_("Agree with terms")
    )
    agree_with_privacy_policy = models.BooleanField(
        default=False,
        help_text=_("Agree with privacy policy"),
        verbose_name=_("Agree with privacy policy"),
    )

    secret_id = models.CharField(
        max_length=128, blank=True, null=True, unique=True, help_text=_("Unique ID")
    )

    anonymous = models.BooleanField(
        default=False, help_text=_("Anonymous user"), verbose_name=_("Anonymous user")
    )

    objects = UserManager()

    class Meta:
        swappable = "AUTH_USER_MODEL"

    @staticmethod
    def create_user_default_board(instance):
        from ej_boards.models import Board

        try:
            board_default = Board.objects.get(slug=slugify(instance.email))
        except Exception:
            board_default = Board(
                slug=instance.email,
                owner=instance,
                title=_("Explore"),
                description="Default user board",
                palette="brand",
            )
            board_default.save()
        return board_default

    def default_board_url(self):
        return "/" + slugify(self.email[:50]) + "/conversations"

    @staticmethod
    def creates_request_session_key(request):
        """
        creates the request session key, if not exists.
        This is necessary for anonymous participation.
        """
        if not request.session.session_key:
            request.session.create()
        return request

    @staticmethod
    def get_or_create_from_session(conversation, request):
        """
        get or creates new user from request session if conversation has
        anonymous_votes_limit attribute bigger then 0 and user is anonymous.
        """
        user = request.user
        if user.is_anonymous and conversation.anonymous_votes_limit:
            request = User.creates_request_session_key(request)
            session_key = request.session.session_key
            user, _ = User.objects.get_or_create(
                email=f"anonymoususer-{session_key}@mail.com",
                defaults={
                    "password": session_key,
                    "agree_with_terms": False,
                },
            )
        return user


class PasswordResetToken(TimeStampedModel):
    """
    Expiring token for password recovery.
    """

    url = models.CharField(
        _("User token"), max_length=50, unique=True, default=token_factory
    )
    is_used = models.BooleanField(default=False)
    user = models.ForeignKey("User", on_delete=models.CASCADE)

    @property
    def is_expired(self):
        time_now = datetime.now(timezone.utc)
        return (time_now - self.created).total_seconds() > 600

    def use(self, commit=True):
        self.is_used = True
        if commit:
            self.save(update_fields=["is_used"])


def clean_expired_tokens():
    """
    Clean up used and expired tokens.
    """
    threshold = datetime.now(timezone.utc) - timedelta(seconds=600)
    expired = PasswordResetToken.objects.filter(created__lte=threshold)
    used = PasswordResetToken.objects.filter(is_used=True)
    (used | expired).delete()


def remove_account(user):
    """
    Remove user's account:

    * Mark the account as inactive.
    * Remove all information from user profile.
    * Assign a random e-mail.
    * Set user name to Anonymous.

    # TODO:
    * Remove all boards?
    * Remove all conversations created by the user?
    """
    if hasattr(user, "profile"):
        remove_profile(user)

    # Handle user object
    email = user.email
    user.is_active = False
    user.is_superuser = False
    user.is_staff = False
    user.name = _("Anonymous")
    user.save()

    # Remove e-mail overriding django validator
    new_email = f"anonymous-{user.id}@deleted-account"
    User.objects.filter(id=user.id).update(email=new_email)
    log.info(f"{email} removed account")


def remove_profile(user):
    """
    Erase profile information.
    """

    profile = user.profile.__class__(user=user, id=user.profile.id)
    profile.save()
