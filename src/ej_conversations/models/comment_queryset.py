import logging

from boogie import db
from boogie.models.wordcloud import WordCloudQuerySet
from django.contrib.auth import get_user_model
from django.db.models import Q, Count

from .vote import Vote
from ..math import comment_statistics
from ..mixins import ConversationMixin, EXTEND_FIELDS as _EXTEND_FIELDS
from ej_conversations.enums import Choice


log = logging.getLogger("ej")


class CommentQuerySet(ConversationMixin, WordCloudQuerySet):
    """
    A table of comments.
    """

    comments = lambda self, conversation=None: self

    def dataframe(self, *fields, index=None, verbose=False):
        """
        Returns a pandas dataframe for the comment queryset.
        """
        if not fields:
            fields = (
                "id",
                "author",
                "content",
                "agree",
                "disagree",
                "skipped",
                "participants",
                "created",
            )
        return super().dataframe(*fields, index=index, verbose=verbose)

    def get_annotated_comments(self):
        """
        Return comments annotated with the total of agree votes (agree field), the total
        of disagree votes (disagree field), the total of skipped votes (skipped field),
        and the total of participation for each comment.
        """
        return self.annotate(
            disagree=Count("votes", filter=Q(votes__choice=Choice.DISAGREE)),
            agree=Count("votes", filter=Q(votes__choice=Choice.AGREE)),
            skipped=Count("votes", filter=Q(votes__choice=Choice.SKIP)),
            participants=Count("votes__author"),
        )

    def _votes_from_comments(self, comments):
        return Vote.objects.filter(comment__in=self)

    def authors(self):
        """
        Return authors from the current comments.
        """
        return get_user_model().objects.filter(Q(comments__in=self))

    def conversations(self):
        conversations = self.values_list("conversation", flat=True)
        return db.ej_conversations.conversations.filter(id__in=conversations)

    def approved(self):
        """
        Keeps only approved comments.
        """
        return self.filter(status=self.model.STATUS.approved)

    def pending(self):
        """
        Keeps only pending comments.
        """
        return self.filter(status=self.model.STATUS.pending)

    def rejected(self):
        """
        Keeps only rejected comments.
        """
        return self.filter(status=self.model.STATUS.rejected)

    def statistics(self):
        return [x.statistics() for x in self]

    def statistics_summary_dataframe(
        self, normalization=1.0, votes=None, extend_fields=()
    ):
        """
        Return a dataframe with basic voting statistics.

        The resulting dataframe has the 'content', 'author', 'agree', 'disagree'
        'skipped', 'convergence' and 'participation' columns.
        """
        annotated_comments = self.get_annotated_comments()
        comments_df = annotated_comments.dataframe()
        stats = comment_statistics(
            annotated_comments,
            comments_df,
            participation=True,
            convergence=True,
            ratios=True,
        )
        stats *= normalization
        stats = self.extend_dataframe(stats, "author__name", *extend_fields, "content")
        stats["author"] = stats.pop("author__name")
        stats["group"] = "geral"
        stats["created"] = comments_df["created"]
        cols = [
            "content",
            "author",
            "agree",
            "disagree",
            "skipped",
            "convergence",
            "participation",
            "group",
            "created",
            *extend_fields,
        ]
        return stats[cols]


#
# Constants
#
EXTEND_FIELDS = {**{"author__" + k: v for k, v in _EXTEND_FIELDS.items()}}
