from django.urls import path
from .. import views

app_name = "ej_conversations"
conversation_url = "<int:conversation_id>/<slug:slug>/"

urlpatterns = [
    path(
        "",
        views.PublicConversationView.as_view(),
        name="list",
    ),
    path(
        "tags/",
        views.ConversationsFilterByTag.as_view(),
        name="filter-tags",
    ),
    path(
        "tags/user/",
        views.UserConversationsFilterByTag.as_view(),
        name="filter-tags-user",
    ),
    path(
        "tags/promoted/",
        views.PromotedConversationsFilterByTag.as_view(),
        name="filter-promoted",
    ),
]
