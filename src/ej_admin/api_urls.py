from django.urls import path
from .api import SearchedBoardsAPIView

urlpatterns = [
    path(
        "environment/searched-boards/",
        SearchedBoardsAPIView.as_view(),
        name="api_searched_boards",
    ),
]
