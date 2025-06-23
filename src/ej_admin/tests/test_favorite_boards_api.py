import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from ej_users.models import User
from ej_boards.models import Board
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

def ensure_permission():
    Permission = pytest.importorskip('django.contrib.auth.models').Permission
    ContentType = pytest.importorskip('django.contrib.contenttypes.models').ContentType
    ct, _ = ContentType.objects.get_or_create(app_label='ej', model='user')
    perm, _ = Permission.objects.get_or_create(
        codename='can_access_environment_management',
        name='Can access environment management',
        content_type=ct
    )
    return perm

@pytest.mark.django_db
def test_favorite_boards_api_permission_redirect():
    client = APIClient()
    url = "/api/admin/environment/favorite-boards/"
    response = client.get(url)
    # Não autenticado: espera 401 Unauthorized (padrão DRF)
    assert response.status_code == 401

@pytest.mark.django_db
def test_favorite_boards_api_authenticated_no_permission():
    user = User.objects.create_user("admin@admin.com", "password")
    client = APIClient()
    client.force_authenticate(user=user)
    url = "/api/admin/environment/favorite-boards/"
    response = client.get(url)
    # Autenticado, mas sem permissão: espera 403
    assert response.status_code == 403

@pytest.mark.django_db
def test_favorite_boards_api_authenticated_empty():
    user = User.objects.create_user("admin@admin.com", "password")
    perm = ensure_permission()
    user.user_permissions.add(perm)
    client = APIClient()
    client.force_authenticate(user=user)
    url = "/api/admin/environment/favorite-boards/"
    response = client.get(url)
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.django_db
def test_favorite_boards_api_authenticated_with_favorites():
    user = User.objects.create_user("admin@admin.com", "password")
    perm = ensure_permission()
    user.user_permissions.add(perm)
    client = APIClient()
    client.force_authenticate(user=user)
    board1 = Board.objects.create(slug="fav1", owner=user, title="Board Fav 1", description="desc")
    board2 = Board.objects.create(slug="fav2", owner=user, title="Board Fav 2", description="desc")
    # Adiciona aos favoritos
    user.favorite_boards.add(board1)
    user.favorite_boards.add(board2)
    url = "/api/admin/environment/favorite-boards/"
    response = client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    slugs = [b["slug"] for b in data]
    assert "fav1" in slugs and "fav2" in slugs

@pytest.mark.django_db
def test_favorite_boards_api_authenticated_with_invalid_board():
    user = User.objects.create_user("admin@admin.com", "password")
    perm = ensure_permission()
    user.user_permissions.add(perm)
    client = APIClient()
    client.force_authenticate(user=user)
    # Não adiciona nenhum board aos favoritos
    url = "/api/admin/environment/favorite-boards/"
    response = client.get(url)
    assert response.status_code == 200
    assert response.json() == []
