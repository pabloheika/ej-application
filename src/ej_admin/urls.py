from django.urls import include, path
from . import views
from . import api

app_name = "ej_admin"

urlpatterns = [
    path(
        "",
        views.index,
        name="index",
    ),
    path(
        "recent-boards/",
        views.recent_boards,
        name="recent_boards",
    ),
    path(
        "searched-users/",
        views.searched_users,
        name="searched_users",
    ),
    path(
        "searched-boards/",
        views.searched_boards,
        name="searched_boards",
    ),
    path(
        "searched-conversations/",
        views.searched_conversations,
        name="searched_conversations",
    ),
    path(
        "favorite-boards/",
        views.get_favorite_boards,
        name="favorite_boards",
    ),
    path(
        "api/admin/environment/searched-boards/",
        api.SearchedBoardsAPIView.as_view(),
        name="api_searched_boards",
    ),
    path("api/admin/environment/", include("ej_admin.api_urls")),
]
