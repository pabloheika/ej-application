from celery import shared_task


@shared_task
def update_clusterization(id, force=False):
    """
    Task that fetches a clusterization with the given id and executes it's
    .update_clusterization() method.
    """
    from ej_clusters.models import Clusterization

    try:
        clusterization = Clusterization.objects.get(id=id)
        clusterization.update_clusters(force=force)
    except Clusterization.DoesNotExist:
        return "clusterization not found"

    return f"{clusterization.conversation.title} clusterization updated"
