from ej_clusters.models.clusterization import Clusterization
from ej_conversations.models import Conversation
from sidekick import import_later
from rest_framework.decorators import action
from rest_framework.response import Response
from ej.viewsets import RestAPIBaseViewSet
from .utils import cluster_shapes
from ej_clusters.serializers import (
    ClusterizationSerializer,
    ClusterSerializer,
    StereotypeSerializer,
)
from ej.permissions import IsOwner, IsSuperUser
from rest_framework.permissions import IsAdminUser
from ej_clusters.models import Stereotype

math = import_later(".math", package=__package__)


class ClusterizationViewSet(RestAPIBaseViewSet):
    queryset = Clusterization.objects.all()
    serializer_class = ClusterizationSerializer
    permission_classes = [IsOwner, IsSuperUser, IsAdminUser]

    def list(self, request):
        if request.user.is_superuser:
            queryset = Clusterization.objects.all()
        else:
            conversation = Conversation.objects.filter(author=request.user)
            queryset = Clusterization.objects.filter(conversation__in=conversation)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True)
    def clusters(self, request, pk):
        clusterization = self.get_object()
        clusters = clusterization.clusters.all()
        serializer = ClusterSerializer(clusters, context={"request": request}, many=True)
        return Response(serializer.data)

    @action(detail=True)
    def affinities(self, request, pk):
        clusterization = self.get_object()
        shapes = cluster_shapes(clusterization, user=request.user)
        return Response(shapes)

    @action(detail=True)
    def stereotypes(self, request, pk):
        clusterization = self.get_object()
        serializer = StereotypeSerializer(
            clusterization.stereotypes.all(), context={"request": request}, many=True
        )
        return Response(serializer.data)


class StereotypeViewSet(RestAPIBaseViewSet):
    queryset = Stereotype.objects.all()
    serializer_class = StereotypeSerializer
    permission_classes = [IsOwner, IsSuperUser]

    def _get_conversation(self, stereotype):
        cluster = stereotype.clusters.first()
        if cluster is None:
            return None
        return cluster.clusterization.conversation

    def _serialize_comment(self, comment, vote=None):
        choice_val = None
        if vote is not None:
            choice_val = vote.choice
        else:
            choice_val = getattr(comment, "choice", None)

        return {
            "id": comment.id,
            "content": comment.content,
            "choice": choice_val,
        }

    @action(detail=True, methods=["get"], url_path="vote-form-data")
    def vote_form_data(self, request, pk=None):
        stereotype = self.get_object()
        conversation = self._get_conversation(stereotype)
        if conversation is None:
            return Response(
                {
                    "detail": "Stereotype is not associated with any conversation.",
                    "comments": [],
                }
            )

        approved_comments = conversation.comments.approved()
        votes = stereotype.votes.filter(comment__in=approved_comments)
        votes_by_comment = {v.comment_id: v for v in votes}

        data = [
            self._serialize_comment(comment, votes_by_comment.get(comment.id))
            for comment in approved_comments
        ]
        return Response(
            {
                "conversation_id": conversation.id,
                "stereotype_id": stereotype.id,
                "comments": data,
            }
        )

    @action(detail=True, methods=["post"], url_path="votes")
    def create_votes(self, request, pk=None):
        from ej_conversations.models import Comment
        from ej_conversations.enums import Choice

        stereotype = self.get_object()
        votes_payload = request.data.get("votes", [])
        created, errors = [], []

        for item in votes_payload:
            try:
                comment_id = item.get("comment")
                choice = item.get("choice")
                if comment_id is None or choice is None:
                    raise ValueError("'comment' and 'choice' are required fields.")

                comment = Comment.objects.get(id=comment_id)
                vote = stereotype.vote(comment, choice)
                created.append(vote.id)
            except Exception as exc:
                errors.append({"input": item, "error": str(exc)})

        status_code = 201 if created and not errors else 207
        return Response({"created": created, "errors": errors}, status=status_code)

    @action(detail=True, methods=["get"], url_path="manage-votes")
    def manage_votes(self, request, pk=None):
        stereotype = self.get_object()
        conversation = self._get_conversation(stereotype)
        if conversation is None:
            return Response(
                {
                    "detail": "Stereotype is not associated with any conversation.",
                    "voted": [],
                    "non_voted": [],
                }
            )

        voted_comments = stereotype.voted_comments(conversation)
        non_voted_comments = stereotype.non_voted_comments(conversation)

        voted = [self._serialize_comment(c) for c in voted_comments]
        non_voted = [self._serialize_comment(c) for c in non_voted_comments]

        return Response({"voted": voted, "non_voted": non_voted})

    @action(detail=True, methods=["put"], url_path="votes/bulk-update")
    def bulk_update_votes(self, request, pk=None):
        from ej_conversations.models import Comment
        from ej_conversations.enums import Choice
        from ej_clusters.models.stereotype_vote import StereotypeVote

        stereotype = self.get_object()
        votes_payload = request.data.get("votes", [])

        updated, deleted, errors = [], [], []

        for item in votes_payload:
            try:
                comment_id = item.get("comment")
                if comment_id is None:
                    raise ValueError("'comment' is required.")
                choice = item.get("choice")
                comment = Comment.objects.get(id=comment_id)

                existing = stereotype.votes.filter(comment=comment).first()

                if choice in (None, "", "null"):
                    # delete vote if exists
                    if existing:
                        existing.delete()
                        deleted.append(comment_id)
                    continue

                choice_value = Choice.normalize(choice)

                if existing:
                    existing.choice = choice_value
                    existing.save()
                    updated.append(comment_id)
                else:
                    stereotype.vote(comment, choice_value)
                    updated.append(comment_id)
            except Exception as exc:
                errors.append({"input": item, "error": str(exc)})

        return Response({
            "updated": updated,
            "deleted": deleted,
            "errors": errors,
        })
