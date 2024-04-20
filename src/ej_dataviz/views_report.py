from django.core.paginator import Paginator
from django.views.generic import DetailView
from sidekick import import_later
from django.utils.translation import gettext_lazy as _

from ej.decorators import can_access_dataviz_class_view
from ej_conversations.models import Conversation
from ej_dataviz.models import (
    CommentsReportClustersFilter,
    CommentsReportOrderByFilter,
    CommentsReportSearchFilter,
)

from .utils import get_clusters, get_comments_dataframe

pd = import_later("pandas")


class CommentReportBaseView(DetailView):
    """
    Implements common behaviors for ej_dataviz views.
    """

    template_name = "ej_dataviz/reports/includes/comments/table.jinja2"
    model = Conversation

    @can_access_dataviz_class_view
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)

    def paginate_comments(
        self,
        conversation: Conversation,
        comments_df=pd.DataFrame(),
        page_number: int = 1,
        page_size: int = 10,
    ):
        """
        creates a Django Paginator instance using conversation comments as list of items.

        :param page_number: a integer with the Paginator page.
        :param conversation: a Conversation instance
        """
        if not isinstance(comments_df, pd.DataFrame):
            comments_df = get_comments_dataframe(conversation.comments, "")
        comments = comments_df.values
        if len(comments) > 0:
            paginator = Paginator(comments, page_size)
            return paginator.get_page(page_number)
        return Paginator(comments, 1).page(1)

    def paginate_users(
        self, conversation: Conversation, users_df=pd.DataFrame(), page_number: int = 1
    ):
        """
        creates a Django Paginator instance using conversation comments as list of items.

        :param page_number: a integer with the Paginator page.
        :param conversation: a Conversation instance
        """
        if not isinstance(users_df, pd.DataFrame):
            users_df = self.get_user_dataframe(conversation.comments)
        users = users_df.values
        # TODO: Fix the page number calculation
        if len(users) > 0:
            paginator = Paginator(users, 10)
            return paginator.get_page(page_number)
        return Paginator(users, 1).page(1)


class CommentReportFilterView(CommentReportBaseView):
    """
    Returns conversation comments based on filter params.
    """

    model = Conversation
    template_name = "ej_dataviz/reports/includes/comments/table.jinja2"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        conversation = context["object"]
        search_text = self.request.GET.get("search")
        order_by = self.request.GET.get("order-by")
        ascending = self.request.GET.get("sort", False) == "asc"

        cluster_ids = self.request.GET.getlist("clusters")
        comments_df = CommentsReportClustersFilter(cluster_ids, conversation).filter()
        comments_df = CommentsReportSearchFilter(
            search_text, conversation.comments, comments_df
        ).filter()
        comments_df = CommentsReportOrderByFilter(
            order_by, conversation.comments, comments_df, ascending
        ).filter()
        context["page"] = self.paginate_comments(
            conversation, comments_df, self.request.GET.get("page") or 1
        )
        return context


class CommentReportDetailView(CommentReportBaseView):
    """
    Returns comment report page.
    """

    template_name = "ej_dataviz/reports/comments.jinja2"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversation = context["object"]
        clusters = get_clusters(conversation)
        context["clusters"] = clusters
        context["page"] = self.paginate_comments(
            conversation, None, page_number=self.request.GET.get("page") or 1
        )
        return context


class UserReportDetailView(CommentReportBaseView):
    """
    Returns user report page.
    """

    template_name = "ej_dataviz/reports/users.jinja2"
    model = Conversation

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversation = context["object"]
        users_df = self.get_user_dataframe(conversation)
        clusters = get_clusters(conversation)
        context["clusters"] = clusters
        context["page"] = self.paginate_users(
            conversation, users_df, self.request.GET.get("page") or 1
        )
        return context

    def get_user_dataframe(self, conversation: Conversation, page_number: int = 1):
        """
        creates a Django Paginator instance using conversation comments as list of items.

        :param page_number: a integer with the Paginator page.
        :param conversation: a Conversation instance
        """
        users_df = conversation.users.statistics_summary_dataframe(
            normalization=100, convergence=False, conversation=conversation
        )
        users_df.insert(
            0,
            _("participant"),
            users_df[["email"]].agg("\n".join, axis=1),
            True,
        )
        users_df.drop(["email", "name", _("Phone number")], inplace=True, axis=1)
        users_df = users_df.sort_values("agree", ascending=False)
        return users_df
