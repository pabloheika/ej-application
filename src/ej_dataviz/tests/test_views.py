import datetime
import json

from django.test import Client
from django.urls import reverse
import pytest

from ej.testing import UrlTester
from ej_clusters.enums import ClusterStatus
from ej_clusters.models.cluster import Cluster
from ej_clusters.models.clusterization import Clusterization
from ej_clusters.models.stereotype import Stereotype
from ej_clusters.mommy_recipes import ClusterRecipes
from ej_conversations.mommy_recipes import ConversationRecipes
from ej_users.models import User

BASE_URL = "/api/v1"


class TestRoutes(ConversationRecipes, UrlTester):
    admin_urls = [
        "/conversations/1/conversation/report/users/",
        "/conversations/1/conversation/report/comments/",
        "/conversations/1/conversation/dashboard/",
    ]

    @pytest.fixture
    def data(self, conversation, board, author_db):
        conversation.author = author_db
        board.owner = author_db
        board.save()
        conversation.board = board
        conversation.save()


class TestReportRoutes(ClusterRecipes):
    @pytest.fixture
    def logged_client(self):
        user = User.objects.get(email="author@domain.com")
        client = Client()
        client.force_login(user)
        return client

    @pytest.fixture
    def conversation_with_votes(self, conversation, board, author_db):
        user1 = User.objects.create_user("user1@email.br", "password")
        user2 = User.objects.create_user("user2@email.br", "password")
        user3 = User.objects.create_user("user3@email.br", "password")

        conversation.author = author_db
        board.owner = author_db
        board.save()
        conversation.board = board
        conversation.save()

        comment = conversation.create_comment(
            author_db, "aa", status="approved", check_limits=False
        )
        comment.vote(user1, "agree")
        comment.vote(user2, "agree")
        comment.vote(user3, "disagree")
        return conversation

    @pytest.fixture
    def conversation_with_comments(self, conversation, board, author_db):
        user1 = User.objects.create_user("user1@email.br", "password")
        user2 = User.objects.create_user("user2@email.br", "password")
        user3 = User.objects.create_user("user3@email.br", "password")

        conversation.author = author_db
        board.owner = author_db
        board.save()
        conversation.board = board
        conversation.save()

        comment = conversation.create_comment(
            author_db, "aa", status="approved", check_limits=False
        )
        comment2 = conversation.create_comment(
            author_db, "aaa", status="approved", check_limits=False
        )
        comment3 = conversation.create_comment(
            author_db, "aaaa", status="approved", check_limits=False
        )
        comment4 = conversation.create_comment(
            author_db, "test", status="approved", check_limits=False
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

    def test_should_get_count_of_votes_in_a_period_of_time(
        self, conversation_with_votes, logged_client
    ):
        conversation = conversation_with_votes
        today = datetime.datetime.now().date()  # 2022-04-04
        one_week_ago = today - datetime.timedelta(days=7)
        url = reverse(
            "boards:dataviz-votes_over_time", kwargs=conversation.get_url_kwargs()
        )
        url = url + f"?startDate={one_week_ago}&endDate={today}"
        response = logged_client.get(url)
        data = json.loads(response.content)["data"]

        assert response.status_code == 200
        assert len(data) == 8
        assert data[0]["date"] == one_week_ago.strftime("%Y-%m-%dT%H:%M:%SZ")
        assert data[-1]["date"] == today.strftime("%Y-%m-%dT%H:%M:%SZ")

        assert data[0]["value"] == 0
        assert data[1]["value"] == 0
        assert data[2]["value"] == 0
        assert data[3]["value"] == 0
        assert data[4]["value"] == 0
        assert data[5]["value"] == 0
        assert data[6]["value"] == 0
        assert data[7]["value"] == 3

    def test_should_return_error_if_start_date_is_bigger_than_end_date(
        self, conversation, board, author_db, logged_client
    ):
        conversation.author = author_db
        board.owner = author_db
        board.save()
        conversation.board = board
        conversation.save()

        url = reverse(
            "boards:dataviz-votes_over_time", kwargs=conversation.get_url_kwargs()
        )
        url = url + "?startDate=2021-10-13&endDate=2021-10-06"
        response = logged_client.get(url)
        assert json.loads(response.content) == {
            "error": "end date must be gratter then start date."
        }

    def test_missing_params_should_return_error(
        self, conversation, board, author_db, logged_client
    ):
        conversation.author = author_db
        board.owner = author_db
        board.save()
        conversation.board = board
        conversation.save()

        base_url = reverse(
            "boards:dataviz-votes_over_time", kwargs=conversation.get_url_kwargs()
        )
        response = logged_client.get(base_url)
        assert json.loads(response.content) == {
            "error": "end date and start date should be passed as a parameter."
        }

        url = base_url + "?startDate=2021-10-06"
        response = logged_client.get(url)
        assert json.loads(response.content) == {
            "error": "end date and start date should be passed as a parameter."
        }

        url = base_url + "?endDate=2021-10-13"
        response = logged_client.get(url)
        assert json.loads(response.content) == {
            "error": "end date and start date should be passed as a parameter."
        }

    def test_board_owner_can_view_dataviz_dashboard(
        self, conversation, board, author_db, logged_client
    ):
        conversation.author = author_db
        board.owner = author_db
        board.save()
        conversation.board = board
        conversation.save()

        clusterization = Clusterization.objects.create(
            conversation=conversation, cluster_status=ClusterStatus.ACTIVE
        )
        cluster = Cluster.objects.create(name="name", clusterization=clusterization)
        stereotype, _ = Stereotype.objects.get_or_create(name="name", owner=author_db)
        cluster.stereotypes.add(stereotype)

        url = reverse("boards:dataviz-dashboard", kwargs=conversation.get_url_kwargs())
        response = logged_client.get(url)
        assert (
            "Your conversation still does not have defined personas. Without personas, it is not possible to generate opinion groups."
            not in response.content.decode()
        )

    def test_get_page(self, conversation_with_comments, logged_client):
        conv = conversation_with_comments
        base_url = reverse("boards:dataviz-comments", kwargs=conv.get_url_kwargs())
        url = f"{base_url}?page=1"

        response = logged_client.get(url)
        comments = list(response.context["page"])
        assert conversation_with_comments.comments.all()[0].content == comments[0][0]
        assert conversation_with_comments.comments.all()[1].content == comments[1][0]
        assert conversation_with_comments.comments.all()[2].content == comments[2][0]
        assert conversation_with_comments.comments.all()[3].content == comments[3][0]

    def test_get_dashboard_with_clusters(
        self, cluster_db, stereotype_vote, comment, vote, logged_client
    ):
        """
        EJ has several recipes for create objects for testing.
        cluster_db creates objects based on ej_clusters/mommy_recipes.py and testing/fixture_class.py.
        calling cluster_db on method signature creates and cluster belonging to a conversation and clusterization.
        """
        cluster_db.stereotypes.add(stereotype_vote.author)
        cluster_db.users.add(cluster_db.clusterization.conversation.author)
        cluster_db.save()
        conversation = cluster_db.conversation
        comment = conversation.create_comment(
            conversation.author, "aa", status="approved", check_limits=False
        )
        comment.vote(conversation.author, "agree")
        comment.save()
        dashboard_url = reverse(
            "boards:dataviz-dashboard", kwargs=conversation.get_url_kwargs()
        )
        response = logged_client.get(dashboard_url)
        assert response.status_code == 200
        assert response.context["biggest_cluster_data"].get("name") == "cluster"
        assert response.context["biggest_cluster_data"].get("content") == comment.content
        assert response.context["biggest_cluster_data"].get("percentage")

    def test_get_dashboard_without_clusters(
        self, cluster_db, stereotype_vote, logged_client
    ):
        """
        EJ has several recipes for creating objects for testing.
        cluster_db creates objects based on ej_clusters/mommy_recipes.py and testing/fixture_class.py.
        calling cluster_db on method signature creates an cluster belonging to a conversation and clusterization.
        """
        cluster_db.stereotypes.add(stereotype_vote.author)
        cluster_db.users.add(cluster_db.clusterization.conversation.author)
        cluster_db.save()
        conversation = cluster_db.conversation
        dashboard_url = reverse(
            "boards:dataviz-dashboard", kwargs=conversation.get_url_kwargs()
        )
        response = logged_client.get(dashboard_url)
        assert response.status_code == 200
        assert response.context["biggest_cluster_data"] == {}
