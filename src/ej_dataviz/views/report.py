import json
from django.core.paginator import Paginator
from django.shortcuts import render
from django.views.generic import DetailView
from sidekick import import_later

from ej.decorators import can_access_dataviz_class_view
from ej_conversations.models import Conversation, Comment
from ej_dataviz.utils import get_clusters, get_comments_dataframe, get_user_dataframe
from ej_dataviz.views.filters import (
    CommentsReportClustersFilter,
    CommentsReportSearchFilter,
    ReportOrderByFilter,
    UsersReportClustersFilter,
    UsersReportSearchFilter,
)
from ej_users.models import User

pd = import_later("pandas")


class ReportsBaseView(DetailView):
    """
    Common implementation for a conversation reports.
    """

    model = Conversation

    def get_dataframe(self, conversation: Conversation):
        pass

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversation = context["object"]
        clusters = get_clusters(conversation)
        context["clusters"] = clusters

        dataframe = self.get_dataframe(conversation)
        context["page"] = self.paginate(dataframe, self.request.GET.get("page") or 1)
        return context

    @can_access_dataviz_class_view
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)

    def paginate(
        self,
        df=pd.DataFrame(),
        page_number: int = 1,
        page_size: int = 10,
    ):
        """
        creates a Django Paginator instance using dataframe rows.

        :param page_number: a integer with the Paginator page.
        :param conversation: a Conversation instance
        """
        dataframe_rows = df.values
        if len(dataframe_rows) > 0:
            paginator = Paginator(dataframe_rows, page_size)
            return paginator.get_page(page_number)
        return Paginator(dataframe_rows, 1).page(1)


class CommentReportFilterView(ReportsBaseView):
    """
    Returns conversation comments based on filter params.
    """

    model = Conversation
    template_name = "ej_dataviz/reports/includes/comments/table.jinja2"

    def get_dataframe(self, conversation):
        return get_comments_dataframe(conversation, "")

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
        comments_df = comments_df.reset_index()

        context["page"] = self.paginate(comments_df, self.request.GET.get("page") or 1)
        context["comments"] = json.dumps(comments_df.to_json(orient="records"))
        return context


class CommentReportDetailView(ReportsBaseView):
    """
    Returns comment report page.
    """

    template_name = "ej_dataviz/reports/comments.jinja2"

    def get_dataframe(self, conversation):
        comments_df = get_comments_dataframe(conversation, "")
        comments_df = comments_df.reset_index()
        return comments_df

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversation = context["object"]
        dataframe = self.get_dataframe(conversation)
        context["comments"] = json.dumps(dataframe.to_json(orient="records"))
        return context


class UsersReportDetailView(ReportsBaseView):
    """
    Returns user report page.
    """

    template_name = "ej_dataviz/reports/users.jinja2"
    model = Conversation

    def get_dataframe(self, conversation):
        return get_user_dataframe(conversation)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversation = context["object"]
        dataframe = self.get_dataframe(conversation)
        context["users"] = json.dumps(dataframe.to_json(orient="records"))
        return context


class UsersReportFilterView(ReportsBaseView):
    """
    Returns conversation users based on filter params.
    """

    model = Conversation
    template_name = "ej_dataviz/reports/includes/users/table.jinja2"

    def get_dataframe(self, conversation):
        return get_user_dataframe(conversation)

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
        context["page"] = self.paginate(users_df, self.request.GET.get("page") or 1)
        context["users"] = json.dumps(users_df.to_json(orient="records"))
        return context


class ReportDetailView(DetailView):
    def post(self, *args, **kwargs):
        context = self.get_context_data()
        return render(self.request, self.template_name, context)

    def get_context_data(self, *args, **kwargs):
        current_index = int(self.request.POST["current_index"][0])
        objects = json.loads(self.request.POST["objects"])

        return {
            "current_index": current_index,
            "previous": self.previous(current_index, objects),
            "next": self.next(current_index, objects),
            "objects": json.dumps(self.request.POST["objects"]),
            "current_object": objects[current_index],
        }

    def next(self, current_index, objects):
        """
        Get next object from list according to current index
        """
        next_index = current_index + 1
        next = None

        try:
            next = objects[next_index][self.identifier]
        except IndexError:
            pass
        return next

    def previous(self, current_index, objects):
        """
        Get previous object from list according to current index
        """
        previous_index = current_index - 1
        previous = None

        try:
            previous = objects[previous_index][self.identifier]
        except IndexError:
            pass

        if previous_index < 0:
            previous = None
        return previous


class UserDetailView(ReportDetailView):
    """
    Returns user report page.
    """

    template_name = "ej_dataviz/reports/includes/users/modal.jinja2"
    model = Conversation

    def get_context_data(self, *args, **kwargs):
        self.identifier = "email"
        user_email = self.request.POST["user_email"]
        user = User.objects.get(email=user_email)
        conversation = self.get_object()
        conversation.for_user = user

        return {
            **super().get_context_data(**kwargs),
            "user": user,
            "conversation": conversation,
        }


class CommentDetailView(ReportDetailView):
    """
    Returns comment report page.
    """

    template_name = "ej_dataviz/reports/includes/comments/modal.jinja2"
    model = Comment

    def get_context_data(self, *args, **kwargs):
        self.identifier = "comment"
        comment = self.get_object()

        return {
            **super().get_context_data(**kwargs),
            "comment": comment,
        }
