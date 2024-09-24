from django.db.models.signals import post_save
from django.dispatch import receiver

from ej_clusters.models import Cluster


@receiver(post_save, sender=Cluster)
def create_periodic_clusterization(sender, instance: Cluster, **kwargs):
    instance.get_periodic_clusterization()
