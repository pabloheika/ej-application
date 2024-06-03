from django.test import RequestFactory
from django.test import Client
import pytest

from ej_clusters.models.cluster import Cluster
from ej_clusters.models.clusterization import Clusterization
from ej_clusters.models.stereotype import Stereotype
from ej_clusters.models.stereotype_vote import StereotypeVote
from ej_conversations.enums import Choice
from ej_conversations.tests.conftest import *
from ej_users.models import User


@pytest.fixture
def stereotype(db, user):
    return Stereotype.objects.create(name="stereotype", owner=user)


@pytest.fixture
def stereotype_vote(db, comment, stereotype):
    return StereotypeVote.objects.create(
        author=stereotype, comment=comment, choice=Choice.AGREE
    )


@pytest.fixture
def clusterization(db, conversation):
    return Clusterization.objects.create(conversation=conversation)


@pytest.fixture
def cluster(db, clusterization, stereotype):
    cluster = Cluster.objects.create(clusterization=clusterization, name="My Cluster")
    cluster.stereotypes.add(stereotype)
    cluster.save()
    return cluster


@pytest.fixture
def request_factory(self):
    return RequestFactory()


@pytest.fixture
def admin_user(db):
    admin_user = User.objects.create_superuser("admin@test.com", "pass")
    admin_user.save()
    return admin_user


@pytest.fixture
def request_as_admin(request_factory, admin_user):
    request = request_factory
    request.user = admin_user
    return request


@pytest.fixture
def logged_client(user):
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def conversation_with_comments(conversation, board):
    user1 = User.objects.create_user("user1@email.br", "password")
    user2 = User.objects.create_user("user2@email.br", "password")
    user3 = User.objects.create_user("user3@email.br", "password")

    board.save()
    conversation.board = board
    conversation.save()

    comment = conversation.create_comment(
        conversation.author, "aa", status="approved", check_limits=False
    )
    comment2 = conversation.create_comment(
        conversation.author, "aaa", status="approved", check_limits=False
    )
    comment3 = conversation.create_comment(
        conversation.author, "aaaa", status="approved", check_limits=False
    )
    comment4 = conversation.create_comment(
        conversation.author, "test", status="approved", check_limits=False
    )

    comment.vote(user1, "agree")
    comment.vote(user2, "agree")
    comment.vote(user3, "agree")

    comment2.vote(user1, "agree")
    comment2.vote(user2, "disagree")
    comment2.vote(user3, "disagree")

    comment3.vote(user1, "disagree")
    comment3.vote(user2, "disagree")
    comment3.vote(user3, "disagree")

    comment4.vote(user1, "disagree")
    conversation.save()
    return conversation


@pytest.fixture()
def conversation_with_votes(conversation, board):
    user1 = User.objects.create_user("user1@email.br", "password")
    user2 = User.objects.create_user("user2@email.br", "password")
    user3 = User.objects.create_user("user3@email.br", "password")

    conversation.board = board
    conversation.save()

    comment = conversation.create_comment(
        conversation.author, "aa", status="approved", check_limits=False
    )
    comment.vote(user1, "agree")
    comment.vote(user2, "agree")
    comment.vote(user3, "disagree")
    return conversation
