from rest_framework.test import APIClient
from ej_conversations.tests.conftest import get_authorized_api_client, API_V1_URL

PHONE_NUMBER = "61982734758"


class TestGetRoutesProfile:
    def test_phone_number_endpoint(self, db, user):
        profile = user.get_profile()
        profile.phone_number = PHONE_NUMBER
        profile.save()
        api = get_authorized_api_client({"email": user.email, "password": "password"})
        path = API_V1_URL + "/profiles/phone-number/"
        response = api.get(path)
        assert response.status_code == 200
        response_data = response.json()
        assert response_data.get("phone_number") == PHONE_NUMBER

    def test_set_phone_number_endpoint(self, db, user):
        profile = user.get_profile()
        profile.phone_number = PHONE_NUMBER
        profile.save()
        api = get_authorized_api_client({"email": user.email, "password": "password"})
        path = API_V1_URL + "/profiles/set-phone-number/"
        response = api.post(path, {"phone_number": "61981178174"})
        assert response.status_code == 200
        response_data = response.json()
        assert response_data.get("phone_number") == "61981178174"

    def test_get_phone_number_endpoint_with_anonymous(self):
        api = APIClient()
        path = API_V1_URL + "/profiles/phone-number/"
        response = api.get(path)
        assert response.status_code == 401

    def test_set_phone_number_endpoint_with_anonymous(self):
        api = APIClient()
        path = API_V1_URL + "/profiles/set-phone-number/"
        response = api.post(path, {})
        assert response.status_code == 401
