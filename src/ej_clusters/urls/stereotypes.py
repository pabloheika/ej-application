from django.urls import path
from ..views import stereotypes

app_name = "ej_cluster"
stereotype_url = "<int:pk>"

urlpatterns = [
    path(
        "",
        stereotypes.StereotypeListView.as_view(),
        name="list",
    ),
    path(
        "create/<int:clusterization_id>",
        stereotypes.StereotypeCreateView.as_view(),
        name="create",
    ),
    path(
        f"{stereotype_url}/edit/",
        stereotypes.StereotypeEditView.as_view(),
        name="edit",
    ),
    path(
        f"{stereotype_url}/delete/",
        stereotypes.StereotypeDeleteView.as_view(),
        name="delete",
    ),
]
