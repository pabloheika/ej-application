from django.urls import path
from . import views_dataviz
from . import views_report

app_name = "ej_dataviz"
conversation_url = "<int:conversation_id>/<slug:slug>/"
report_url = "<int:conversation_id>/<slug:slug>/report/"

reports_urlpatterns = [
    path(
        report_url + "comments/",
        views_report.CommentReportDetailView.as_view(),
        name="comments",
    ),
    path(
        report_url + "comments/filter",
        views_report.CommentReportFilterView.as_view(),
        name="comments-filter",
    ),
    path(
        report_url + "users/",
        views_report.UsersReportDetailView.as_view(),
        name="users",
    ),
    path(
        report_url + "users/filter",
        views_report.UsersReportFilterView.as_view(),
        name="users-filter",
    ),
]

dataviz_urlpatterns = [
    path(
        report_url + "votes-over-time/",
        views_dataviz.votes_over_time,
        name="votes_over_time",
    ),
    path(
        report_url + "data/votes.<fmt>",
        views_dataviz.votes_data,
        name="votes_data",
    ),
    path(
        report_url + "data/cluster-<int:cluster_id>/votes.<fmt>",
        views_dataviz.votes_data_cluster,
        name="votes_data_cluster",
    ),
    path(
        report_url + "data/users.<fmt>",
        views_dataviz.users_data,
        name="users_data",
    ),
    path(
        report_url + "data/comments.<fmt>",
        views_dataviz.comments_data,
        name="comments_data",
    ),
    path(
        conversation_url + "dashboard/",
        views_dataviz.index,
        name="dashboard",
    ),
    path(
        conversation_url + "dashboard/cluster",
        views_dataviz.ClusterDetailView.as_view(),
        name="cluster-detail",
    ),
    path(
        conversation_url + "scatter/",
        views_dataviz.scatter,
        name="scatter",
    ),
    path(
        conversation_url + "scatter/pca.json/",
        views_dataviz.scatter_pca_json,
        name="scatter_pca_json",
    ),
    path(
        conversation_url + "scatter/group-<groupby>.json",
        views_dataviz.scatter_group,
        name="scatter_group",
    ),
    path(
        conversation_url + "dashboard/words.json",
        views_dataviz.words,
        name="words",
    ),
]

urlpatterns = [*dataviz_urlpatterns, *reports_urlpatterns]
