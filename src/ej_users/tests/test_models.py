import pytest
from boogie.testing.pytest import ModelTester
from ej.testing import EjRecipes
from ej_users import password_reset_token
from ej_users.models import (
    User,
    PasswordResetToken,
    UserSecretIdManager,
    clean_expired_tokens,
)
from ej_users.mommy_recipes import UserRecipes


class TestUser(UserRecipes, ModelTester):
    model = User
    representation = "user@domain.com"


class TestUserSecretIdManager:
    def test_try_to_merge_users_without_secret_id(self, user, another_user):

        unique_user = another_user
        with pytest.raises(Exception):
            UserSecretIdManager.merge_unique_user_with(user, unique_user.email)

    def test_merge_temp_user_with_unique_user(
        self, db, vote, comments, user, another_user
    ):
        unique_user = another_user

        user.secret_id = User.encode_secret_id("someothersecretid")
        user.save()

        user_votes_count = user.votes.all().count()
        user_comments_count = user.comments.all().count()

        assert unique_user.votes.all().count() == 0
        assert unique_user.comments.all().count() == 0
        assert unique_user.secret_id is None

        UserSecretIdManager.merge_unique_user_with(user, unique_user.email)

        with pytest.raises(User.DoesNotExist):
            User.objects.get(email=user.email)

        unique_user = User.objects.get(email=unique_user.email)
        assert User.decode_secret_id(unique_user.secret_id) == "someothersecretid"
        assert unique_user.votes.all().count() == user_votes_count
        assert unique_user.comments.all().count() == user_comments_count


class TestUserManager(EjRecipes):
    def test_can_create_and_fetch_simple_user(self, db):
        user = User.objects.create_user("name@server.com", "1234", name="name")
        assert user.name == "name"
        assert user.password != "1234"
        assert not user.is_superuser
        assert User.objects.get_by_email("name@server.com") == user

    def test_can_create_and_fetch_superuser(self, db):
        user = User.objects.create_superuser("name@server.com", "1234", name="name")
        assert user.name == "name"
        assert user.password != "1234"
        assert user.is_superuser
        assert User.objects.get_by_email("name@server.com") == user

        # Check unhappy paths
        with pytest.raises(ValueError):
            User.objects.create_superuser("name@server.com", "1234", is_superuser=False)
        with pytest.raises(ValueError):
            User.objects.create_superuser("name@server.com", "1234", is_staff=False)

    def test_generate_username(self):
        user = User(email="email@at.com")
        assert user.username == "email__at.com"


class TestPasswordResetToken(EjRecipes):
    def test_expiration(self, user):
        token = PasswordResetToken(user=user)
        assert not token.is_expired

    def test_password_reset_token(self, user):
        token = password_reset_token(user, commit=False)
        assert token.user == user
        assert token.url

    def test_clean_expired_tokens(self, user_db):
        token = password_reset_token(user_db)
        assert PasswordResetToken.objects.filter(user=user_db).exists()
        token.use()
        clean_expired_tokens()
        assert not PasswordResetToken.objects.filter(user=user_db).exists()
