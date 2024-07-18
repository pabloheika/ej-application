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
        assert response.status_code == 200

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
