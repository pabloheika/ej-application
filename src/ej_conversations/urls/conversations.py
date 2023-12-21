from django.urls import path
from .. import views

app_name = "ej_conversations"
conversation_url = "<int:conversation_id>/<slug:slug>"

urlpatterns = [
    path(
        "",
        views.PrivateConversationView.as_view(),
        name="list",
    ),
    path(
        f"{conversation_url}/welcome/",
        views.ConversationWelcomeView.as_view(),
        name="welcome",
    ),
    path(
        f"{conversation_url}/comments/new/",
        views.NewCommentView.as_view(),
        name="new_comment",
    ),
    path(
        f"{conversation_url}/comments/delete/",
        views.delete_comment,
        name="delete_comment",
    ),
    path(
        f"{conversation_url}/comments/check/",
        views.check_comment,
        name="check_comment",
    ),
    path(
        f"{conversation_url}/moderate/",
        views.ConversationModerateView.as_view(),
        name="moderate",
    ),
    path(
        f"{conversation_url}/edit/",
        views.ConversationEditView.as_view(),
        name="edit",
    ),
    path(
        f"{conversation_url}/",
        views.ConversationDetailView.as_view(),
        name="detail",
    ),
    path(
        f"{conversation_url}/comment/",
        views.ConversationCommentView.as_view(),
        name="comment",
    ),
    path(
        f"{conversation_url}/cancel/",
        views.ConversationCommentCancelView.as_view(),
        name="comment_cancel",
    ),
    path(
        "add/",
        views.ConversationCreateView.as_view(),
        name="create",
    ),
    path(
        f"update-favorite-boards/",
        views.update_favorite_boards,
        name="update-favorite-boards",
    ),
    path(
        f"is-favorite-board/",
        views.is_favorite_board,
        name="is-favorite-board",
    ),
]
