import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from ej_users.models import User
from ej_boards.models import Board

@pytest.mark.django_db
def test_searched_boards_api_permission():
    client = APIClient()
    url = "/api/admin/environment/searched-boards/"
    response = client.get(url)
    assert response.status_code == 403  # Não autenticado/sem permissão

@pytest.mark.django_db
def test_searched_boards_api_authenticated():
    user = User.objects.create_user("admin@admin.com", "password")
    user.user_permissions.add_by_codename('can_access_environment_management')
    client = APIClient()
    client.force_authenticate(user=user)
    Board.objects.create(slug="test1", owner=user, title="Board 1", description="desc")
    url = "/api/admin/environment/searched-boards/?searchString=test1&orderBy=date&sort=desc&page=1&numEntries=10"
    response = client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert data["count"] == 1
    assert data["results"][0]["slug"] == "test1"

@pytest.mark.django_db
def test_searched_boards_api_pagination():
    user = User.objects.create_user("admin@admin.com", "password")
    user.user_permissions.add_by_codename('can_access_environment_management')
    client = APIClient()
    client.force_authenticate(user=user)
    for i in range(15):
        Board.objects.create(slug=f"board{i}", owner=user, title=f"Board {i}", description="desc")
    url = "/api/admin/environment/searched-boards/?numEntries=5"
    response = client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 15
    assert len(data["results"]) == 5
