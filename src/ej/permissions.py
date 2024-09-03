from rest_framework import permissions
from ej_conversations.models import Conversation

class BaseAuthenticatedPermission(permissions.BasePermission):
    """
    Base permission class that checks if the user is authenticated.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated


class BaseObjectPermission(BaseAuthenticatedPermission):
    """
    Base class for object-level permissions that compares object attributes with the request user.
    """
    user_attribute = None

    def has_object_permission(self, request, view, obj):
        if self.user_attribute:
            return getattr(obj, self.user_attribute) == request.user
        return False


class IsAuthor(BaseObjectPermission):
    user_attribute = 'author'


class IsOwner(BaseObjectPermission):
    user_attribute = 'owner'


class IsUser(BaseObjectPermission):
    user_attribute = 'user'


class IsSuperUser(BaseAuthenticatedPermission):
    """
    Permission class that checks if the user is a superuser.
    """
    def has_object_permission(self, request, view, obj):
        return request.user.is_superuser


class IsAuthenticatedCreationView(BaseAuthenticatedPermission):
    """
    Permission class that allows access if the user is authenticated and the action is 'create'.
    """
    def has_permission(self, request, view):
        if super().has_permission(request, view):
            return view.action == "create"
        return False


class IsAuthenticatedOnlyGetView(BaseAuthenticatedPermission):
    """
    Permission class that allows access only to safe methods for authenticated users.
    """
    forbidden_endpoints = ["create", "update", "partial_update", "destroy"]

    def has_permission(self, request, view):
        if super().has_permission(request, view):
            return view.action not in self.forbidden_endpoints
        return False


class IsViewRetrieve(permissions.BasePermission):
    """
    Permission class that allows access only to the 'retrieve' action.
    """
    def has_permission(self, request, view):
        return view.action == "retrieve"


class ParticipantCanAddComment(permissions.BasePermission):
    message = "participants are not allowed to add comments"

    def has_permission(self, request, view):
        if request.method == "POST":
            conversation_id = request.data.get("conversation")
            try:
                conversation = Conversation.objects.get(id=conversation_id)
                if not conversation.participants_can_add_comments:
                    return False
                return True
            except Conversation.DoesNotExist:
                self.message = f"could not find conversation with ID {conversation_id}"
                return False
        return True

class IsRandomCommentAndNotAuthenticated(BaseObjectPermission):
    def has_permission(self, request, view):
        if view.action == "random_comment":
            return True
        return False