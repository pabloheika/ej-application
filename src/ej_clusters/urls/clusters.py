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
        conversation_url + "clusters/ctrl/",
        clusters.CtrlView.as_view(),
        name="ctrl",
    ),
]
