from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from ej_clusters.models import Cluster


@receiver(post_save, sender=Cluster)
def create_periodic_clusterization(sender, instance: Cluster, **kwargs):
    if settings.CELERY_ACTIVE:
        instance.get_periodic_clusterization()
