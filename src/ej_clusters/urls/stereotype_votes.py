from django.urls import path
from ..views import stereotype_votes


app_name = "ej_clusters"
conversation_url = "<int:conversation_id>/<slug:slug>/"


urlpatterns = [
    path(
        conversation_url + "stereotypes/",
        stereotype_votes.StereotypeVotesView.as_view(),
        name="list",
    ),
    path(
        conversation_url + "stereotypes/stereotype-votes/create",
        stereotype_votes.StereotypeVotesCreateView.as_view(),
        name="create",
    ),
    path(
        conversation_url + "stereotypes/stereotype-votes/<int:pk>/delete",
        stereotype_votes.StereotypeVotesDeleteView.as_view(),
        name="delete",
    ),
    path(
        conversation_url + "stereotypes/stereotype-votes/<int:pk>/update",
        stereotype_votes.StereotypeVotesUpdateView.as_view(),
        name="update",
    ),
]
