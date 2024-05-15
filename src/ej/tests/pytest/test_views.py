import pytest
from constance import config
from django.urls import reverse
from django.test import Client
from ej.testing import UrlTester
from ej_conversations.tests.test_views import ConversationSetup


class TestBasicUrls(UrlTester):
    # Urls visible to every one (even without login)
    public_urls = ["/login/"]


class TestViews(ConversationSetup):
    def test_index_route_logged_user(self, logged_admin):
        response = logged_admin.get(reverse("index"))
        assert response.status_code == 302
        assert response.url == reverse("profile:home")

    @pytest.mark.django_db
    def test_index_anonymous_user(self, rf):
        client = Client()
        response = client.get(reverse("index"))
        assert response.status_code == 302
        assert response.url == config.EJ_LANDING_PAGE_DOMAIN


class TestAccessViews(ConversationSetup):
    def test_access_docs_anonymous_user(self):
        client = Client()
        response = client.get("/docs/")
        assert response.status_code == 200

    def test_access_admin_anonymous_user(self):
        client = Client()
        response = client.get("/admin/")
        assert response.status_code == 302
        assert response.url == "/admin/login/?next=/admin/"

    def test_access_admin_user(self, logged_admin):
        response = logged_admin.get("/admin/")
        assert b"Site administration | Django site admin" in response.content
        assert response.status_code == 200
