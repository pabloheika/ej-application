import json
from logging import getLogger
from boogie import rules
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from model_utils.models import TimeStampedModel
from sidekick import delegate_to, lazy, placeholder as this

from ej_clusters.tasks import update_clusterization
from ..enums import ClusterStatus
from ..utils import cluster_shapes, use_transaction
from .querysets import ClusterizationManager
from .stereotype import Stereotype
from .stereotype_vote import StereotypeVote

NOT_GIVEN = object()
log = getLogger("ej")


class Clusterization(TimeStampedModel):
    """
    Manages clusterization tasks for a given conversation.
    """

    conversation = models.OneToOneField(
        "ej_conversations.Conversation",
        on_delete=models.CASCADE,
        related_name="clusterization",
    )
    cluster_status = models.IntegerField(
        ClusterStatus, default=ClusterStatus.PENDING_DATA
    )
    comments = delegate_to("conversation")
    users = delegate_to("conversation")
    votes = delegate_to("conversation")
    owner = delegate_to("conversation", name="author")

    @property
    def stereotypes(self):
        return Stereotype.objects.filter(clusters__in=self.clusters.all())

    @property
    def stereotype_votes(self):
        return StereotypeVote.objects.filter(comment__in=self.comments.all())

    @property
    def n_unprocessed_votes(self):
        return self.conversation.votes.filter(created__gte=self.modified).count()

    #
    # Statistics and annotated values
    #
    n_clusters = lazy(this.clusters.count())
    n_stereotypes = lazy(this.stereotypes.count())
    n_stereotype_votes = lazy(this.stereotype_votes.count())

    objects = ClusterizationManager()

    class Meta:
        ordering = ["conversation_id"]

    def __str__(self):
        clusters = self.clusters.count()
        return f"{self.conversation} ({clusters} clusters)"

    def get_absolute_url(self):
        return reverse(
            "boards:stereotype-votes-list",
            kwargs=self.conversation.get_url_kwargs(),
        )

    def update_clusterization(self, force=False, atomic=False):
        """
        Update clusters according to environment setup
        if variable USE_CELERY_BACKEND is set, this is executed asynchronously
        """
        if settings.USE_CELERY_BACKEND:
            return self.get_periodic_clusterization()
        return self.update_clusters(force, atomic)

    def update_clusters(self, force=False, atomic=False):
        """
        Update clusters if necessary, unless force=True, in which it
        unconditionally updates the clusterization.
        """
        if force or rules.test_rule("ej.must_update_clusterization", self):
            log.info(f"[clusters] updating cluster: {self.conversation}")

            if self.clusters.count() == 0:
                if self.cluster_status == ClusterStatus.ACTIVE:
                    self.cluster_status = ClusterStatus.PENDING_DATA
                self.save()
                return

            with use_transaction(atomic=atomic):
                try:
                    self.clusters.find_clusters()
                except ValueError as exc:
                    log.error(f"[clusters] Error during clusterization: [{exc}]")
                    raise
                if self.cluster_status == ClusterStatus.PENDING_DATA:
                    self.cluster_status = ClusterStatus.ACTIVE
                self.save()

    def get_stereotypes(self):
        return {
            stereotype.name: str(stereotype.id) for stereotype in self.stereotypes.all()
        } or None

    @staticmethod
    def get_default_shape_data():
        return {"json_data": None, "user_group": None, "clusters": ()}

    def get_shape_data(self, user) -> dict:
        """
        Returns a dict containing all the clusters shapes of a specific conversation,
        the user group and the clusters of the conversation.
        """
        user_group = None

        try:
            clusters = (
                self.clusters.annotate(size=models.Count(models.F("users")))
                .annotate_attr(separated_comments=lambda c: c.separate_comments())
                .prefetch_related("stereotypes")
            )
            shapes = cluster_shapes(self, clusters, user)
            shapes_json = json.dumps({"shapes": list(shapes.values())})
        except Exception as exc:
            exc_name = exc.__class__.__name__
            log.error(f"Error found during clusterization: {exc} ({exc_name})")
            clusters = ()
            shapes_json = {
                "shapes": [{"name": _("Error"), "size": 0, "intersections": [[0.0]]}]
            }
        else:
            user_group = (
                self.clusters.filter(users=user).values_list("name", flat=True).first()
            )

        return {"json_data": shapes_json, "user_group": user_group, "clusters": clusters}

    @staticmethod
    def get_shape_data_by_groups(instance, user):
        num_groups = instance.get_clusters_count()
        if not instance or not num_groups:
            return Clusterization.get_default_shape_data()
        return instance.get_shape_data(user)

    def get_clusters_count(self):
        return self.clusters.count()

    def get_biggest_cluster(self):
        if self.get_clusters_count() > 0:
            clusters = self.clusters.annotate(size=models.Count(models.F("users")))
            return clusters.order_by("-size").first()
        return None

    def get_similar_opinion(self, user):
        user_cluster = user.clusters.filter(clusterization__id=self.id)
        clusters_user_count = user_cluster.users().all().count()
        return clusters_user_count / self.conversation.n_participants * 100

    def get_periodic_clusterization(self):
        from django_celery_beat.models import PeriodicTask, IntervalSchedule
        id = self.id

        if self.clusters.all().count() >= 2:
            schedule, _ = IntervalSchedule.objects.get_or_create(
                every=5,
                period=IntervalSchedule.MINUTES,
            )

            periodic_task, created = PeriodicTask.objects.get_or_create(
                name=f"update-clusterization-{id}",
                task="ej_clusters.tasks.update_clusterization",
                interval=schedule,
                kwargs=json.dumps({"id": id, "force": True}),
            )
            if created:
                update_clusterization.delay(id, True).get(timeout=5)
            return periodic_task
