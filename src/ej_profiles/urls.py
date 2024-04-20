from django.urls import path
from . import views

app_name = "ej_profiles"

urlpatterns = [
    path(
        "",
        views.DetailView.as_view(),
        name="detail",
    ),
    path(
        "edit/",
        views.EditView.as_view(),
        name="edit",
    ),
    path(
        "home/",
        views.HomeView.as_view(),
        name="home",
    ),
    path(
        "tour/",
        views.TourView.as_view(),
        name="tour",
    ),
    path(
        "tour/?step=<step>",
        views.TourView.as_view(),
        name="tour",
    ),
]
