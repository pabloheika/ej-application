from django.http import HttpResponse
from django.shortcuts import redirect, reverse
from django.utils.translation import gettext_lazy as _
from ej_users.models import User


TOOLS_CHANNEL = {
    "socketio": (_("Opinion Bots"), "webchat"),
    "telegram": (_("Opinion Bots"), "telegram"),
    "whatsapp": (_("Opinion Bots"), "whatsapp"),
    "opinion_component": (_("Opinion component"),),
    "unknown": (),
}


def bot_tool_is_active(bots_tool, tool_name):
    """
    checks if a certain type of bot (webchat, telegram, whatsapp) is active.
    """
    tool = getattr(bots_tool, tool_name)
    return tool.is_active


def redirect_to_conversation_detail(view):
    """
    Verify if request.user should see the welcome page.
    If not, redirect  him to conversation detail route.
    """

    def wrapper(self, request, *args, **kwargs):
        user = request.user
        conversation = self.get_object()
        user_has_votes = conversation.votes.filter(author__id=user.id).exists()
        user_has_comments = conversation.comments.filter(author__id=user.id).exists()
        if user_has_votes or user_has_comments or not conversation.welcome_message:
            return redirect("boards:conversation-detail", **conversation.get_url_kwargs())
        print("USER", user)
        return view(self, request, *args, **kwargs)

    return wrapper


def user_can_post_anonymously(func):
    """
    user_can_post_anonymously checks if conversation was configured to accept
    anonymous votes.
    """

    def wrapper(self, request, conversation_id, slug, board_slug, *args, **kwargs):
        conversation = self.get_object()
        request.user = User.get_or_create_from_session(conversation, request)
        redirect_url = ""
        conversation_url = reverse(
            "boards:conversation-detail", kwargs=conversation.get_url_kwargs()
        )
        if conversation.reaches_anonymous_particiption_limit(request.user):
            redirect_url = f"/register/?sessionKey={request.session.session_key}&next={conversation_url}"
        elif request.user.is_anonymous:
            redirect_url = f"/register/?next={conversation_url}"

        if redirect_url:
            """
            Participation page uses HTMX library to make backend AJAX requests.
            In order to make a redirect with HTMX,
            we need to include HX-Redirect header to the response.
            For more information, access https://htmx.org/reference/.
            """
            response = HttpResponse()
            response["HX-Redirect"] = redirect_url
            response.status_code = 302
            return response

        return func(self, request, conversation_id, slug, board_slug, *args, **kwargs)

    return wrapper


def create_session_key(func):
    """
    create_session_key check if request.session.session_key is empty.
    If so, creates it.
    """

    def wrapper(self, **kwargs):
        User.creates_request_session_key(self.request)
        return func(self)

    return wrapper
