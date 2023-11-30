from logging import getLogger
from typing import Any, Dict

from django.db import transaction
from django.db.models import F
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseServerError, JsonResponse
from django.urls import reverse
from django.shortcuts import render
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView

from ej_boards.models import Board
from ej_conversations.rules import max_comments_per_conversation
from ej_users.models import SignatureFactory

from . import forms, models
from .models import Conversation, Comment
from ej_users.models import User
from .utils import (
    check_promoted,
    conversation_admin_menu_links,
    handle_detail_favorite,
    handle_detail_comment,
    handle_detail_vote,
)

from ej.decorators import (
    can_add_conversations,
    can_edit_conversation,
    can_moderate_conversation,
    can_acess_list_view,
    is_superuser,
    check_conversation_overdue,
)

from .decorators import create_session_key, user_can_post_anonymously
from ej.components.menu import apps_custom_menu_links

log = getLogger("ej")


class ConversationView(ListView):
    def get_queryset(self) -> QuerySet[Any]:
        user = self.request.user
        board_slug = self.kwargs.get("board_slug", None)
        annotations = ("n_votes", "n_comments", "n_user_votes", "first_tag", "n_favorites", "author_name")

        if board_slug:
            board = Board.objects.get(slug=board_slug)
            queryset = board.conversations.annotate_attr(board=board)
        else:
            queryset = Conversation.objects.filter(is_promoted=True)

        return queryset.cache_annotations(*annotations, user=user).order_by("-created")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        return super().get_context_data(**kwargs)


class PublicConversationView(ConversationView):
    template_name = template_name = "ej_conversations/list.jinja2"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        user = self.request.user
        user_boards = []
        if user.is_authenticated:
            user_signature = SignatureFactory.get_user_signature(user)
            max_conversation_per_user = user_signature.get_conversation_limit()
            user_boards = Board.objects.filter(owner=user)
        else:
            max_conversation_per_user = 0

        return {
            "conversations": self.get_queryset(),
            "user_boards": user_boards,
            "conversations_limit": max_conversation_per_user,
        }


@method_decorator([login_required, can_acess_list_view], name="dispatch")
class PrivateConversationView(ConversationView):
    template_name = "ej_conversations/conversation-list.jinja2"

    def get_queryset(self) -> QuerySet[Any]:
        user = self.request.user
        board_slug = self.kwargs.get("board_slug", None)
        annotations = ("n_votes", "n_comments", "n_user_votes", "first_tag", "n_favorites", "author_name")

        if board_slug:
            board = Board.objects.get(slug=board_slug)
            queryset = board.conversations.annotate_attr(board=board)
        else:
            queryset = Conversation.objects.filter(is_promoted=True)

        return queryset.cache_annotations(*annotations, user=user).order_by("-created")

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        user = self.request.user
        board_slug = self.kwargs.get("board_slug", None)
        board = Board.objects.get(slug=board_slug)
        user_signature = SignatureFactory.get_user_signature(user)
        max_conversation_per_user = user_signature.get_conversation_limit()
        user_boards = Board.objects.filter(owner=user)

        return {
            "conversations": self.get_queryset(),
            "title": _(board.title),
            "subtitle": _("Participate voting and creating comments!"),
            "conversations_limit": max_conversation_per_user,
            "board": board,
            "user_boards": user_boards,
        }


@method_decorator([check_conversation_overdue], name="dispatch")
class ConversationDetailView(DetailView):
    form_class = forms.CommentForm
    model = Conversation
    template_name = "ej_conversations/conversation-detail.jinja2"
    ctx = {}

    def get(self, request, *args, **kwargs):
        if request.GET.get("comment-addition"):
            return render(request, "ej_conversations/comments/add-comment.jinja2", self.get_context_data())
        if request.GET.get("comment-addition-cancel"):
            return render(request, "ej_conversations/comments/card.jinja2", self.get_context_data())
        return super().get(request, *args, **kwargs)

    @user_can_post_anonymously
    def post(self, request, conversation_id, slug, board_slug, *args, **kwargs):
        conversation = self.get_object()
        request.user = User.creates_from_request_session(conversation, request)
        action = request.POST["action"]
        if action == "vote":
            self.ctx = handle_detail_vote(request)
            return render(request, "ej_conversations/comments/card.jinja2", self.get_context_data())
        elif action == "comment":
            self.ctx = handle_detail_comment(request, conversation)
            return render(request, "ej_conversations/comments/card.jinja2", self.get_context_data())
        elif action == "favorite":
            self.ctx = handle_detail_favorite(request, conversation)
        else:
            log.warning(f"user {request.user.id} se nt invalid POST request: {request.POST}")
            return HttpResponseServerError("invalid action")

        return render(request, self.template_name, self.get_context_data())

    @create_session_key
    def get_context_data(self, **kwargs):
        conversation = self.get_object()
        user = self.request.user
        max_comments = max_comments_per_conversation(conversation, user)
        conversation.set_request(self.request)

        if not user.is_anonymous:
            n_comments = user.comments.filter(conversation=conversation).count()
            n_user_final_votes = conversation.current_comment_count(user)
        else:
            n_comments = 0
            n_user_final_votes = 0

        return {
            "conversation": conversation,
            "comment": conversation.next_comment_with_id(user, None),
            "menu_links": conversation_admin_menu_links(conversation, user),
            "comment_form": self.form_class(conversation=conversation),
            "user_is_author": conversation.author == user,
            "user_progress_percentage": conversation.user_progress_percentage(user),
            "n_comments": n_comments,
            "max_comments": max_comments,
            "n_user_final_votes": n_user_final_votes,
            "apps_menu_links": apps_custom_menu_links(conversation),
            **self.ctx,
        }


@method_decorator([login_required, can_acess_list_view, can_add_conversations], name="dispatch")
class ConversationCreateView(CreateView):
    template_name = "ej_conversations/conversation-create.jinja2"
    form_class = forms.ConversationForm

    def post(self, request, board_slug, *args, **kwargs):
        form = self.form_class(request=request)
        kwargs["board"] = self.get_board()

        if form.is_valid():
            with transaction.atomic():
                conversation = form.save_comments(self.request.user, **kwargs)

            return redirect(reverse("boards:conversation-detail", kwargs=conversation.get_url_kwargs()))

        return render(request, "ej_conversations/conversation-create.jinja2", self.get_context_data())

    def get_context_data(self, **kwargs):
        user = self.request.user
        user_boards = Board.objects.filter(owner=user)

        return {
            "form": self.form_class(request=self.request),
            "board": self.get_board(),
            "user_boards": user_boards,
        }

    def get_board(self) -> Board:
        board_slug = self.kwargs["board_slug"]
        return Board.objects.get(slug=board_slug)


@method_decorator([login_required, can_edit_conversation], name="dispatch")
class ConversationEditView(UpdateView):
    model = Conversation
    template_name = "ej_conversations/conversation-edit.jinja2"
    form_class = forms.ConversationForm

    def post(self, request, conversation_id, slug, board_slug, *args, **kwargs):
        conversation = self.get_object()
        board = Board.objects.get(slug=board_slug)
        form = self.form_class(request=request, instance=conversation)

        if form.is_valid_post():
            form.save(board=board, **kwargs)
            page = request.POST.get("next")
            url = self.get_redirect_url(conversation, page)
            return redirect(url)

        return render(request, self.template_name, self.get_context_data())

    def get_redirect_url(self, conversation, page):
        if page == "stereotypes":
            args = conversation.get_url_kwargs()
            return reverse("boards:cluster-stereotype_votes", kwargs=args)
        elif page == "moderate":
            return conversation.patch_url("conversation:moderate")
        elif conversation.is_promoted:
            return conversation.get_absolute_url()
        else:
            return reverse("boards:dataviz-dashboard", kwargs=conversation.get_url_kwargs())

    def get_context_data(self, **kwargs: Any):
        conversation = self.get_object()
        user = self.request.user

        return {
            "conversation": conversation,
            "form": self.form_class(request=self.request, instance=conversation),
            "menu_links": conversation_admin_menu_links(conversation, user),
            "can_publish": user.has_perm("ej_conversations.can_publish_promoted"),
            "board": conversation.board,
        }


@method_decorator([login_required, can_edit_conversation, can_moderate_conversation], name="dispatch")
class ConversationModerateView(UpdateView):
    model = Conversation
    template_name = "ej_conversations/conversation-moderate.jinja2"
    status = models.Comment.STATUS

    def post(self, request, conversation_id, slug, board_slug, *args, **kwargs):
        payload = request.POST
        for status in [self.status.approved, self.status.pending, self.status.rejected]:
            if status in payload:
                comments_ids = payload.getlist(status)
                Comment.objects.filter(id__in=comments_ids).update(status=Comment.STATUS_MAP[status])

        return render(request, self.template_name, self.get_context_data())

    def get_context_data(self, **kwargs):
        conversation = self.get_object()

        comments = conversation.comments.annotate(annotation_author_name=F("author__name"))
        approved, pending, rejected = [
            comments.filter(status=_status).order_by("-created")
            for _status in [self.status.approved, self.status.pending, self.status.rejected]
        ]

        created_comments = comments.filter(author=conversation.author).order_by("-created")

        return {
            "conversation": conversation,
            "approved": approved,
            "pending": pending,
            "rejected": rejected,
            "created": created_comments,
            "menu_links": conversation_admin_menu_links(conversation, self.request.user),
            "comment_saved": False,
        }


@method_decorator([login_required, can_edit_conversation, can_moderate_conversation], name="dispatch")
class NewCommentView(UpdateView):
    model = Conversation
    template_name = "ej_conversations/conversation-moderate.jinja2"

    def post(self, request, conversation_id, slug, board_slug, *args, **kwargs):
        comments = request.POST.getlist("comment")
        with transaction.atomic():
            for comment in comments:
                if len(comment) > 2:
                    comment = Comment.objects.create(
                        content=comment,
                        conversation=self.get_object(),
                        author=request.user,
                        status=models.Comment.STATUS.approved,
                    )
        return render(request, self.template_name, self.get_context_data())

    def get_context_data(self, **kwargs):
        conversation = self.get_object()

        status = models.Comment.STATUS
        comments = conversation.comments.annotate(annotation_author_name=F("author__name"))
        approved, pending, rejected = [
            comments.filter(status=_status)
            for _status in [status.approved, status.pending, status.rejected]
        ]
        created_comments = comments.filter(author=conversation.author).order_by("-created")

        return {
            "conversation": conversation,
            "approved": approved,
            "pending": pending,
            "rejected": rejected,
            "created": created_comments,
            "menu_links": conversation_admin_menu_links(conversation, self.request.user),
            "apps_menu_links": apps_custom_menu_links(conversation),
            "comment_saved": True,
        }


@login_required
@can_edit_conversation
@can_moderate_conversation
def delete_comment(request, conversation_id, slug, board_slug):
    comment_id = request.POST.get("comment_id")
    comment = Comment.objects.get(id=int(comment_id))

    if comment.author == request.user:
        comment.delete()

    return HttpResponse(status=200)


@login_required
@can_edit_conversation
@can_moderate_conversation
def check_comment(request, conversation_id, slug, board_slug):
    comment_content = request.POST.get("comment_content")
    try:
        Comment.objects.get(content=comment_content, conversation_id=conversation_id)
        return HttpResponse(status=200)
    except Comment.DoesNotExist:
        return HttpResponse(status=204)


@login_required
@is_superuser
def update_favorite_boards(request, board_slug):
    user = request.user
    board = Board.objects.get(slug=board_slug)

    try:
        update_option = request.GET.get("updateOption", None)
        if update_option == "add":
            user.favorite_boards.add(board)
        elif update_option == "remove":
            user.favorite_boards.remove(board)
        else:
            return HttpResponse(status=404)
    except Exception:
        return HttpResponse(status=404)

    return HttpResponse(status=200)


@login_required
@is_superuser
def is_favorite_board(request, board_slug):
    user = request.user
    board = Board.objects.get(slug=board_slug)

    try:
        user.favorite_boards.get(id=board.id)
        return JsonResponse({"is_favorite_board": True})
    except Board.DoesNotExist:
        return JsonResponse({"is_favorite_board": False})
