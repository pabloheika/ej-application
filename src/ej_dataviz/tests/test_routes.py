import datetime
import json

from django.test import RequestFactory
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
from ej_dataviz.models import (
    CommentsReportClustersFilter,
    CommentsReportOrderByFilter,
    CommentsReportSearchFilter,
)
from ej_dataviz.utils import conversation_has_stereotypes, get_comments_dataframe
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
    def request_factory(self):
        return RequestFactory()

    @pytest.fixture
    def admin_user(self, db):
        admin_user = User.objects.create_superuser("admin@test.com", "pass")
        admin_user.save()
        return admin_user

    @pytest.fixture
    def request_as_admin(self, request_factory, admin_user):
        request = request_factory
        request.user = admin_user
        return request

    @pytest.fixture
    def logged_client(self):
        user = User.objects.get(email="author@domain.com")
        client = Client()
        client.force_login(user)
        return client

    @pytest.fixture()
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
        url = url + f"?startDate=2021-10-13&endDate=2021-10-06"
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

        url = base_url + f"?startDate=2021-10-06"
        response = logged_client.get(url)
        assert json.loads(response.content) == {
            "error": "end date and start date should be passed as a parameter."
        }

        url = base_url + f"?endDate=2021-10-13"
        response = logged_client.get(url)
        assert json.loads(response.content) == {
            "error": "end date and start date should be passed as a parameter."
        }

    def test_conversation_has_stereotypes(
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
            not "Your conversation still does not have defined personas. Without personas, it is not possible to generate opinion groups."
            in response.content.decode()
        )

    def test_get_comments_dataframe(self, conversation_with_comments):
        comments_df = get_comments_dataframe(conversation_with_comments.comments, "")
        assert comments_df.iloc[[0]].get("group").item() == ""
        assert comments_df.iloc[[1]].get("group").item() == ""
        assert comments_df.iloc[[2]].get("group").item() == ""
        assert comments_df.iloc[[3]].get("group").item() == ""
        assert len(comments_df.index) == 4

    def test_get_cluster_comments_dataframe(self, conversation_with_comments):
        clusterization = Clusterization.objects.create(
            conversation=conversation_with_comments, cluster_status=ClusterStatus.ACTIVE
        )
        cluster = Cluster.objects.create(name="name", clusterization=clusterization)

        clusters_filter = CommentsReportClustersFilter(
            [cluster.id], conversation_with_comments
        )
        comments_df = clusters_filter.filter()

        assert comments_df.iloc[[0]].get("group").item() == cluster.name
        assert comments_df.iloc[[1]].get("group").item() == cluster.name
        assert comments_df.iloc[[2]].get("group").item() == cluster.name
        assert comments_df.iloc[[3]].get("group").item() == cluster.name
        assert len(comments_df.index) == 4

    def test_filter_comments_by_group(self, conversation_with_comments):
        clusterization = Clusterization.objects.create(
            conversation=conversation_with_comments, cluster_status=ClusterStatus.ACTIVE
        )
        clusters_filter = CommentsReportClustersFilter([], conversation_with_comments)
        filtered_comments_df = clusters_filter.filter()
        assert filtered_comments_df.iloc[[0]].get("group").item() == ""
        assert filtered_comments_df.iloc[[1]].get("group").item() == ""
        assert filtered_comments_df.iloc[[2]].get("group").item() == ""
        assert filtered_comments_df.iloc[[3]].get("group").item() == ""
        assert len(filtered_comments_df.index) == 4

        cluster = Cluster.objects.create(name="name", clusterization=clusterization)
        clusters_filter = CommentsReportClustersFilter(
            [cluster.id], conversation_with_comments
        )
        filtered_comments_df = clusters_filter.filter()
        assert filtered_comments_df.iloc[[0]].get("group").item() == cluster.name
        assert filtered_comments_df.iloc[[1]].get("group").item() == cluster.name
        assert filtered_comments_df.iloc[[2]].get("group").item() == cluster.name
        assert filtered_comments_df.iloc[[3]].get("group").item() == cluster.name
        assert len(filtered_comments_df.index) == 4

    def test_sort_comments_dataframe_in_descending_order(
        self, conversation_with_comments
    ):
        clusters_filter = CommentsReportClustersFilter([], conversation_with_comments)
        comments_df = clusters_filter.filter()

        orderby_filter = CommentsReportOrderByFilter(
            "agree", conversation_with_comments.comments, comments_df
        )
        sorted_comments_df = orderby_filter.filter()
        assert sorted_comments_df.iloc[[0]].get("content").item() == "aa"
        assert round(sorted_comments_df.iloc[[0]].get("agree").item(), 1) == 100.0
        assert sorted_comments_df.iloc[[1]].get("content").item() == "aaa"
        assert round(sorted_comments_df.iloc[[1]].get("agree").item(), 1) == 33.3
        assert sorted_comments_df.iloc[[2]].get("content").item() == "aaaa"
        assert round(sorted_comments_df.iloc[[2]].get("agree").item(), 1) == 0.0
        assert sorted_comments_df.iloc[[3]].get("content").item() == "test"
        assert round(sorted_comments_df.iloc[[3]].get("agree").item(), 1) == 0.0

        orderby_filter = CommentsReportOrderByFilter(
            "disagree", conversation_with_comments.comments, comments_df
        )
        sorted_comments_df = orderby_filter.filter()
        assert sorted_comments_df.iloc[[0]].get("content").item() == "aaaa"
        assert round(sorted_comments_df.iloc[[0]].get("disagree").item(), 1) == 100.0
        assert sorted_comments_df.iloc[[1]].get("content").item() == "test"
        assert round(sorted_comments_df.iloc[[1]].get("disagree").item(), 1) == 100.0
        assert sorted_comments_df.iloc[[2]].get("content").item() == "aaa"
        assert round(sorted_comments_df.iloc[[2]].get("disagree").item(), 1) == 66.7
        assert sorted_comments_df.iloc[[3]].get("content").item() == "aa"
        assert round(sorted_comments_df.iloc[[3]].get("disagree").item(), 1) == 0.0

    def test_sort_comments_dataframe_in_ascending_order(self, conversation_with_comments):
        clusters_filter = CommentsReportClustersFilter([], conversation_with_comments)
        comments_df = clusters_filter.filter()

        orderby_filter = CommentsReportOrderByFilter(
            "agree", conversation_with_comments.comments, comments_df, True
        )
        sorted_comments_df = orderby_filter.filter()
        assert sorted_comments_df.iloc[[0]].get("content").item() == "aaaa"
        assert round(sorted_comments_df.iloc[[0]].get("agree").item(), 1) == 0.0
        assert sorted_comments_df.iloc[[1]].get("content").item() == "test"
        assert round(sorted_comments_df.iloc[[1]].get("agree").item(), 1) == 0.0
        assert sorted_comments_df.iloc[[2]].get("content").item() == "aaa"
        assert round(sorted_comments_df.iloc[[2]].get("agree").item(), 1) == 33.3
        assert sorted_comments_df.iloc[[3]].get("content").item() == "aa"
        assert round(sorted_comments_df.iloc[[3]].get("agree").item(), 1) == 100.0

        orderby_filter = CommentsReportOrderByFilter(
            "disagree", conversation_with_comments.comments, comments_df, True
        )
        sorted_comments_df = orderby_filter.filter()
        assert sorted_comments_df.iloc[[0]].get("content").item() == "aa"
        assert round(sorted_comments_df.iloc[[0]].get("disagree").item(), 1) == 0.0
        assert sorted_comments_df.iloc[[1]].get("content").item() == "aaa"
        assert round(sorted_comments_df.iloc[[1]].get("disagree").item(), 1) == 66.7
        assert sorted_comments_df.iloc[[2]].get("content").item() == "aaaa"
        assert round(sorted_comments_df.iloc[[2]].get("disagree").item(), 1) == 100.0
        assert sorted_comments_df.iloc[[3]].get("content").item() == "test"
        assert round(sorted_comments_df.iloc[[3]].get("disagree").item(), 1) == 100.0

    def test_search_string_comments_dataframe(self, conversation_with_comments):
        clusters_filter = CommentsReportClustersFilter([], conversation_with_comments)
        comments_df = clusters_filter.filter()

        search_filter = CommentsReportSearchFilter(
            "aa", conversation_with_comments.comments, comments_df
        )
        filtered_comments_df = search_filter.filter()
        assert len(filtered_comments_df.index) == 3
        search_filter = CommentsReportSearchFilter(
            "aaa", conversation_with_comments.comments, comments_df
        )
        filtered_comments_df = search_filter.filter()
        assert len(filtered_comments_df.index) == 2
        search_filter = CommentsReportSearchFilter(
            "t", conversation_with_comments.comments, comments_df
        )
        filtered_comments_df = search_filter.filter()
        assert len(filtered_comments_df.index) == 1

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

    def test_conversation_has_stereotypes(self, cluster_db, stereotype_vote):
        cluster_db.stereotypes.add(stereotype_vote.author)
        cluster_db.users.add(cluster_db.clusterization.conversation.author)
        cluster_db.save()
        clusterization = Clusterization.objects.filter(
            conversation=cluster_db.conversation
        )
        assert conversation_has_stereotypes(clusterization)

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
