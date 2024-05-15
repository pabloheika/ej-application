from django.urls import path
from ..views import clusters

app_name = "ej_clusters"
conversation_url = "<int:conversation_id>/<slug:slug>/"

urlpatterns = [
    path(
        conversation_url + "clusters/",
        clusters.ClustersIndexView.as_view(),
        name="index",
    ),
    path(
        conversation_url + "clusters/edit/",
        clusters.ClustersEditView.as_view(),
        name="edit",
    ),
    path(
        conversation_url + "stereotypes/",
        clusters.StereotypeVotesView.as_view(),
        name="stereotype_votes",
    ),
    path(
        conversation_url + "stereotypes/stereotype-votes-ordenation",
        clusters.StereotypeVotesOrdenationView.as_view(),
        name="stereotype_votes_ordenation",
    ),
    path(
        conversation_url + "stereotypes/stereotype-votes/create",
        clusters.StereotypeVotesCreateView.as_view(),
        name="stereotype_votes_create",
    ),
    path(
        conversation_url + "clusters/ctrl/",
        clusters.CtrlView.as_view(),
        name="ctrl",
    ),
]
