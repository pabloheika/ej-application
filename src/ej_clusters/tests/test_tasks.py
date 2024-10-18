import pytest

from ej_clusters.enums import ClusterStatus
from ej_clusters.models.cluster import Cluster
from ej_clusters.models.clusterization import Clusterization
from ej_clusters.models.stereotype import Stereotype
from ..tasks import test_celery
from ej_clusters.tasks import update_clusterization

pytest_plugins = ("celery.contrib.pytest",)


@pytest.fixture(scope="session")
def celery_config():
    return {
        "broker_url": "redis://localhost:8001",
        "result_backend": "redis://localhost:8001",
    }


@pytest.fixture
def conversation_with_comments(conversation, base_board, base_user):
    conversation.author = base_user
    base_board.owner = base_user
    base_board.save()
    conversation.board = base_board
    conversation.save()

    conversation.create_comment(base_user, "aa", status="approved", check_limits=False)

    conversation.create_comment(base_user, "aaa", status="approved", check_limits=False)
    conversation.create_comment(base_user, "aaaa", status="approved", check_limits=False)

    conversation.save()
    return conversation


def test_celery_worker_initializes(celery_app, celery_worker):
    # this confirms that the default fixtures from celery exists
    assert True


def test_celery_simple_task(celery_app, celery_worker):

    assert test_celery.delay().get(timeout=5) == "Celery is working!"


def test_update_clusterization_task(
    celery_app, celery_worker, conversation_with_comments
):
    clusterization = Clusterization.objects.create(
        conversation=conversation_with_comments, cluster_status=ClusterStatus.ACTIVE
    )
    cluster = Cluster.objects.create(name="name", clusterization=clusterization)
    stereotype, _ = Stereotype.objects.get_or_create(
        name="name", owner=conversation_with_comments.author
    )
    cluster.stereotypes.add(stereotype)
    assert (
        update_clusterization.delay(clusterization.id, True).get(timeout=5)
        == "Celery is working!"
    )
