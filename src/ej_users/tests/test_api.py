from ej_users.models import User
from ej_conversations.tests.conftest import API_V1_URL
from rest_framework.test import APIClient


class TestUserAPI:
    def test_generate_access_token(self, db, user):
        api = APIClient()
        response = api.post(
            API_V1_URL + "/token/",
            {"email": user.email, "password": "password"},
            format="json",
        )
        data = response.json()
        assert response.status_code == 200
        assert data["access_token"]
        assert data["refresh_token"]

    def test_refresh_token(self, db, user):
        api = APIClient()
        response = api.post(
            API_V1_URL + "/token/",
            {"email": user.email, "password": "password"},
            format="json",
        )
        data = response.json()
        old_access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        response = api.post(
            API_V1_URL + "/refresh-token/",
            {"refresh": refresh_token},
            format="json",
        )
        data = response.json()
        assert data["access"]
        assert data["access"] != old_access_token

    def test_registration_auth_valid_user(self, client, db):
        client.post(
            API_V1_URL + "/users/",
            data={
                "name": "David Silva",
                "email": "david@example.com",
                "password": "pass123",
                "password_confirm": "pass123",
            },
            content_type="application/json",
        )
        user = User.objects.get(email="david@example.com")
        assert user.name == "David Silva"
        assert user.email == "david@example.com"

    def test_registration_rest_auth_incorrect_confirm_password(self, client, db):
        response = client.post(
            API_V1_URL + "/users/",
            data={
                "name": "jonatas Silva",
                "email": "jonatassilva@example.com",
                "password": "pass123",
                "password_confirm": "pass1234",
            },
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_registration_rest_auth_missing_password(self, client, db):
        response = client.post(
            API_V1_URL + "/users/",
            data={
                "name": "jonatas Silva",
                "email": "jonatasgomes@mail.com",
                "password_confirm": "pass123",
            },
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_user_endpoint_post_with_already_created_user(self, client, db):
        User.objects.create_user("user@user.com", "password")
        response = client.post(
            API_V1_URL + "/users/",
            data={
                "email": "user@user.com",
            },
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_get_token_after_user_registration(self, client, db):
        response = client.post(
            API_V1_URL + "/users/",
            data={
                "name": "tester",
                "email": "tester@example.com",
                "password": "pass123",
                "password_confirm": "pass123",
            },
            content_type="application/json",
        )
        assert response.json()["access_token"]
        assert response.status_code == 201

    def test_missing_credentials_in_login_should_return_error(self, client, db):
        User.objects.create_user("user@user.com", "password")
        response = client.post(
            API_V1_URL + "/users/",
            data={
                "email": "user@user.com",
            },
            content_type="application/json",
        )
        assert response.status_code == 400

        response = client.post(
            API_V1_URL + "/login/",
            data={"password": "password"},
            content_type="application/json",
        )
        assert response.status_code == 400

        response = client.post(
            API_V1_URL + "/login/",
            data={"email": "user@user.com", "password": ""},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_get_token_after_user_login(self, client, db):
        User.objects.create_user("user@user.com", "password")
        response = client.post(
            "/api/v1/login/",
            data={"email": "user@user.com", "password": "password"},
            content_type="application/json",
        )

        assert response.json()["access_token"]
        assert response.status_code == 200

    def test_create_user_with_secret_id(self, client, db):
        NAME = "Giovanni Giampauli"
        EMAIL = "giovanni@example.com"
        PASSWORD = "pass123"
        SECRET_ID = "123456"
        client.post(
            API_V1_URL + "/users/",
            data={
                "name": NAME,
                "email": EMAIL,
                "password": PASSWORD,
                "password_confirm": PASSWORD,
                "secret_id": SECRET_ID,
            },
            content_type="application/json",
        )
        user = User.objects.get(email=EMAIL)
        assert user.name == NAME
        assert user.email == EMAIL
        assert user.secret_id == SECRET_ID

    def test_create_auth_user(self, client, db):
        NAME_ANONYMOUS = "anonymous user"
        NAME_AUTH = "Giovanni Giampauli"
        EMAIL_AUTH = "giovanni@example.com"
        EMAIL_ANONYMOUS = "anonymous@example.com"
        PASSWORD = "pass123"
        SECRET_ID = "123456"

        response = client.post(
            API_V1_URL + "/users/",
            data={
                "name": NAME_ANONYMOUS,
                "email": EMAIL_ANONYMOUS,
                "password": PASSWORD,
                "password_confirm": PASSWORD,
                "secret_id": SECRET_ID,
            },
            content_type="application/json",
        )

        assert response.status_code == 201

        client.post(
            API_V1_URL + "/users/",
            data={
                "name": NAME_AUTH,
                "email": EMAIL_AUTH,
                "password": PASSWORD,
                "password_confirm": PASSWORD,
                "secret_id": SECRET_ID,
            },
            content_type="application/json",
        )

        assert response.status_code == 201

        user = User.objects.get(email=EMAIL_AUTH)
        assert user.name == NAME_AUTH
        assert user.email == EMAIL_AUTH
        assert user.secret_id == SECRET_ID

        user = User.objects.get(secret_id=SECRET_ID)
        assert user.name == NAME_AUTH
        assert user.email == EMAIL_AUTH
        assert user.secret_id == SECRET_ID

        user = None
        try:
            user = User.objects.get(email=EMAIL_ANONYMOUS)
        except:
            pass
        assert user is None

    def test_create_auth_user_after_both_accounts(self, client, db):
        NAME_ANONYMOUS = "anonymous user"
        NAME_AUTH = "Giovanni Giampauli"
        EMAIL_AUTH = "giovanni@example.com"
        EMAIL_ANONYMOUS = "anonymous@example.com"
        PASSWORD = "pass123"
        SECRET_ID = "123456"

        response = client.post(
            API_V1_URL + "/users/",
            data={
                "name": NAME_ANONYMOUS,
                "email": EMAIL_ANONYMOUS,
                "password": PASSWORD,
                "password_confirm": PASSWORD,
                "secret_id": SECRET_ID,
            },
            content_type="application/json",
        )

        assert response.status_code == 201

        response = client.post(
            API_V1_URL + "/users/",
            data={
                "name": NAME_AUTH,
                "email": EMAIL_AUTH,
                "password": PASSWORD,
                "password_confirm": PASSWORD,
            },
            content_type="application/json",
        )

        assert response.status_code == 201

        response = client.post(
            API_V1_URL + "/users/",
            data={
                "name": NAME_AUTH,
                "email": EMAIL_AUTH,
                "password": PASSWORD,
                "password_confirm": PASSWORD,
                "secret_id": SECRET_ID,
            },
            content_type="application/json",
        )

        assert response.status_code == 201

        user = User.objects.get(email=EMAIL_AUTH)
        assert user.name == NAME_AUTH
        assert user.email == EMAIL_AUTH
        assert user.secret_id == SECRET_ID

        user = User.objects.get(secret_id=SECRET_ID)
        assert user.name == NAME_AUTH
        assert user.email == EMAIL_AUTH
        assert user.secret_id == SECRET_ID

        user = None
        try:
            user = User.objects.get(email=EMAIL_ANONYMOUS)
        except:
            pass
        assert user is None

    def test_get_token_by_secret_id(self, client, db):
        NAME = "anonymous user"
        EMAIL = "anonymous@example.com"
        PASSWORD = "pass123"
        SECRET_ID = "123456"

        response = client.post(
            API_V1_URL + "/users/",
            data={
                "name": NAME,
                "email": EMAIL,
                "password": PASSWORD,
                "password_confirm": PASSWORD,
                "secret_id": SECRET_ID,
            },
            content_type="application/json",
        )

        assert response.status_code == 201

        response = client.post(
            API_V1_URL + "/token/",
            data={
                "secret_id": SECRET_ID,
                "password": PASSWORD,
            },
            content_type="application/json",
        )

        assert response.status_code == 200
        assert response.json()["access_token"]
