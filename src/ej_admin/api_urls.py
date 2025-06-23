from django.urls import path
from .api import SearchedBoardsAPIView, FavoriteBoardsAPIView

urlpatterns = [
    path(
        "environment/searched-boards/",
        SearchedBoardsAPIView.as_view(),
        name="api_searched_boards",
    ),
    path(
        "environment/favorite-boards/",
        FavoriteBoardsAPIView.as_view(),
        name="api_favorite_boards",
    ),
]
