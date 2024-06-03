from django.core.paginator import Paginator
from django.views.generic import DetailView
from sidekick import import_later

from ej.decorators import can_access_dataviz_class_view
from ej_conversations.models import Conversation, Comment
from ej_users.models import User
from ej_dataviz.models import (
    CommentsReportClustersFilter,
    CommentsReportSearchFilter,
    ReportOrderByFilter,
    UsersReportClustersFilter,
    UsersReportSearchFilter,
)

from .utils import get_clusters, get_comments_dataframe, get_user_dataframe

pd = import_later("pandas")


class CommentReportBaseView(DetailView):
    """
    Implements common behaviors for ej_dataviz views.
    """

    template_name = "ej_dataviz/reports/includes/comments/table.jinja2"
    model = Conversation
    report_type = None

    def set_dataframe_by_report_type(self):
        if self.report_type == Comment:
            self.get_dataframe = get_comments_dataframe
        if self.report_type == User:
            self.get_dataframe = get_user_dataframe

    @can_access_dataviz_class_view
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)

    def paginate(
        self,
        conversation: Conversation,
        df=pd.DataFrame(),
        page_number: int = 1,
        page_size: int = 10,
    ):
        """
        creates a Django Paginator instance using conversation comments as list of items.

        :param page_number: a integer with the Paginator page.
        :param conversation: a Conversation instance
        """
        self.set_dataframe_by_report_type()

        if not isinstance(df, pd.DataFrame):
            df = self.get_dataframe(conversation, "")
        objects = df.values
        if len(objects) > 0:
            paginator = Paginator(objects, page_size)
            return paginator.get_page(page_number)
        return Paginator(objects, 1).page(1)


class CommentReportFilterView(CommentReportBaseView):
    """
    Returns conversation comments based on filter params.
    """

    model = Conversation
    template_name = "ej_dataviz/reports/includes/comments/table.jinja2"
    report_type = Comment

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        conversation = context["object"]
        search_text = self.request.GET.get("search")
        order_by = self.request.GET.get("order-by")
        ascending = self.request.GET.get("sort", False) == "asc"

        cluster_ids = self.request.GET.getlist("clusters")
        comments_df = CommentsReportClustersFilter(
            cluster_ids=cluster_ids, conversation=conversation
        ).filter()
        comments_df = CommentsReportSearchFilter(search_text, comments_df).filter()
        comments_df = ReportOrderByFilter(
            order_by, comments_df, ascending, "comment"
        ).filter()
        context["page"] = self.paginate(
            conversation, comments_df, self.request.GET.get("page") or 1
        )
        return context


class ReportDetailView(CommentReportBaseView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversation = context["object"]
        clusters = get_clusters(conversation)
        context["clusters"] = clusters
        context["page"] = self.paginate(
            conversation, None, self.request.GET.get("page") or 1
        )
        return context


class CommentReportDetailView(ReportDetailView):
    """
    Returns comment report page.
    """

    template_name = "ej_dataviz/reports/comments.jinja2"
    report_type = Comment


class UsersReportDetailView(ReportDetailView):
    """
    Returns user report page.
    """

    template_name = "ej_dataviz/reports/users.jinja2"
    model = Conversation
    report_type = User


class UsersReportFilterView(CommentReportBaseView):
    """
    Returns conversation users based on filter params.
    """

    model = Conversation
    template_name = "ej_dataviz/reports/includes/users/table.jinja2"
    report_type = User

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        conversation = context["object"]
        search_text = self.request.GET.get("search")
        order_by = self.request.GET.get("order-by")
        ascending = self.request.GET.get("sort", False) == "asc"
        cluster_ids = self.request.GET.getlist("clusters")
        users_df = UsersReportClustersFilter(cluster_ids, conversation).filter()
        users_df = UsersReportSearchFilter(search_text, users_df).filter()
        users_df = ReportOrderByFilter(order_by, users_df, ascending, "name").filter()
        context["page"] = self.paginate(
            conversation, users_df, self.request.GET.get("page") or 1
        )
        return context
