from celery import shared_task


@shared_task
def update_clusterization(id, force=False):
    """
    Task that fetches a clusterization with the given id and executes it's
    .update_clusterization() method.
    """
    from .models import Clusterization

    clusterization = Clusterization.objects.filter(id=id).first()
    if clusterization is not None:
        clusterization.update_clusters(force=force)

    return "Clusterization updated"


@shared_task
def test_celery():
    return "Celery is working!"
