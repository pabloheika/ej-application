import pytest
from ej_users.models import User
from ej_dataviz.models import ToolsLinksHelper
from ej_clusters.enums import ClusterStatus
from ej_conversations.enums import Choice
from ej_clusters.models.cluster import Cluster
from ej_clusters.models.clusterization import Clusterization
from ej_clusters.mommy_recipes import ClusterRecipes
from ej_clusters.models.stereotype import Stereotype
from ej_clusters.models.stereotype_vote import StereotypeVote
from ej_dataviz.models import (
    CommentsReportClustersFilter,
    ReportOrderByFilter,
    CommentsReportSearchFilter,
    UsersReportClustersFilter,
    UsersReportSearchFilter,
)
from ej_dataviz.utils import (
    conversation_has_stereotypes,
    get_comments_dataframe,
    get_user_dataframe,
)


class TestToolsLinksHelper:
    def setup_method(self, method):
        self.environments = {
            "local": "http://localhost:8000",
            "dev": "https://ejplatform.pencillabs.com.br",
            "prod": "https://www.ejplatform.org",
        }

    def test_bot_link_local(self):
        bot_link = ToolsLinksHelper.get_bot_link(self.environments["local"])
        assert bot_link == "https://t.me/DudaLocalBot?start="

    def test_bot_link_dev(self):
        bot_link = ToolsLinksHelper.get_bot_link(self.environments["dev"])
        assert bot_link == "https://t.me/DudaEjDevBot?start="

    def test_bot_link_prod(self):
        bot_link = ToolsLinksHelper.get_bot_link(self.environments["prod"])
        assert bot_link == "https://t.me/DudaEjBot?start="


class TestReport(ClusterRecipes):
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


class TestCommentsReport(TestReport):
    def test_get_comments_dataframe(self, conversation_with_comments):
        comments_df = get_comments_dataframe(conversation_with_comments, "")
        assert comments_df.iloc[[0]].get("group").item() == ""
        assert comments_df.iloc[[1]].get("group").item() == ""
        assert comments_df.iloc[[2]].get("group").item() == ""
        assert comments_df.iloc[[3]].get("group").item() == ""
        assert len(comments_df.index) == 4

    def test_get_comments_dataframe_for_comments_without_votes(
        self, conversation_with_comments, author_db
    ):
        conversation_with_comments.create_comment(
            author_db, "comment without vote", status="approved", check_limits=False
        )
        conversation_with_comments.save()

        comments_df = get_comments_dataframe(conversation_with_comments, "")
        assert comments_df.iloc[[0]].get("group").item() == ""
        assert comments_df.iloc[[1]].get("group").item() == ""
        assert comments_df.iloc[[2]].get("group").item() == ""
        assert comments_df.iloc[[3]].get("group").item() == ""
        assert comments_df.iloc[[4]].get("group").item() == ""

        assert comments_df.iloc[[4]].get("content").item() == "comment without vote"
        assert comments_df.iloc[[4]].get("agree").item() == 0
        assert comments_df.iloc[[4]].get("disagree").item() == 0
        assert comments_df.iloc[[4]].get("skipped").item() == 0
        assert comments_df.iloc[[4]].get("convergence").item() == 0
        assert comments_df.iloc[[4]].get("participation").item() == 0

        assert len(comments_df.index) == 5

    def test_get_statistics_summary_dataframe(
        self, conversation_with_comments, author_db
    ):
        conversation_with_comments.create_comment(
            author_db, "comment without vote", status="approved", check_limits=False
        )
        conversation_with_comments.save()

        comments_df = conversation_with_comments.comments.statistics_summary_dataframe(
            normalization=100
        )

        assert comments_df.iloc[[0]].get("content").item() == "aa"
        assert comments_df.iloc[[0]].get("agree").item() == 100
        assert comments_df.iloc[[0]].get("disagree").item() == 0
        assert comments_df.iloc[[0]].get("skipped").item() == 0
        assert comments_df.iloc[[0]].get("participation").item() == 100

        assert comments_df.iloc[[1]].get("content").item() == "aaa"
        assert round(comments_df.iloc[[1]].get("agree").item(), 1) == 33.3
        assert round(comments_df.iloc[[1]].get("disagree").item(), 1) == 66.7
        assert comments_df.iloc[[1]].get("skipped").item() == 0
        assert comments_df.iloc[[1]].get("participation").item() == 100

        assert comments_df.iloc[[2]].get("content").item() == "aaaa"
        assert round(comments_df.iloc[[2]].get("agree").item(), 1) == 0
        assert round(comments_df.iloc[[2]].get("disagree").item(), 1) == 100
        assert comments_df.iloc[[2]].get("skipped").item() == 0
        assert comments_df.iloc[[2]].get("participation").item() == 100

        assert comments_df.iloc[[3]].get("content").item() == "test"
        assert round(comments_df.iloc[[3]].get("agree").item(), 1) == 0
        assert round(comments_df.iloc[[3]].get("disagree").item(), 1) == 100
        assert comments_df.iloc[[3]].get("skipped").item() == 0
        assert round(comments_df.iloc[[3]].get("participation").item(), 1) == 33.3

        assert comments_df.iloc[[4]].get("content").item() == "comment without vote"
        assert comments_df.iloc[[4]].get("agree").item() == 0
        assert comments_df.iloc[[4]].get("disagree").item() == 0
        assert comments_df.iloc[[4]].get("skipped").item() == 0
        assert comments_df.iloc[[4]].get("convergence").item() == 0
        assert comments_df.iloc[[4]].get("participation").item() == 0

        assert len(comments_df.index) == 5

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

        orderby_filter = ReportOrderByFilter("agree", comments_df)
        sorted_comments_df = orderby_filter.filter()
        assert sorted_comments_df.iloc[[0]].get("content").item() == "aa"
        assert round(sorted_comments_df.iloc[[0]].get("agree").item(), 1) == 100.0
        assert sorted_comments_df.iloc[[1]].get("content").item() == "aaa"
        assert round(sorted_comments_df.iloc[[1]].get("agree").item(), 1) == 33.3
        assert sorted_comments_df.iloc[[2]].get("content").item() == "aaaa"
        assert round(sorted_comments_df.iloc[[2]].get("agree").item(), 1) == 0.0
        assert sorted_comments_df.iloc[[3]].get("content").item() == "test"
        assert round(sorted_comments_df.iloc[[3]].get("agree").item(), 1) == 0.0

        orderby_filter = ReportOrderByFilter("disagree", comments_df)
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

        orderby_filter = ReportOrderByFilter("agree", comments_df, True)
        sorted_comments_df = orderby_filter.filter()
        assert sorted_comments_df.iloc[[0]].get("content").item() == "aaaa"
        assert round(sorted_comments_df.iloc[[0]].get("agree").item(), 1) == 0.0
        assert sorted_comments_df.iloc[[1]].get("content").item() == "test"
        assert round(sorted_comments_df.iloc[[1]].get("agree").item(), 1) == 0.0
        assert sorted_comments_df.iloc[[2]].get("content").item() == "aaa"
        assert round(sorted_comments_df.iloc[[2]].get("agree").item(), 1) == 33.3
        assert sorted_comments_df.iloc[[3]].get("content").item() == "aa"
        assert round(sorted_comments_df.iloc[[3]].get("agree").item(), 1) == 100.0

        orderby_filter = ReportOrderByFilter("disagree", comments_df, True)
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

        search_filter = CommentsReportSearchFilter("aa", comments_df)
        filtered_comments_df = search_filter.filter()
        assert len(filtered_comments_df.index) == 3
        search_filter = CommentsReportSearchFilter("aaa", comments_df)
        filtered_comments_df = search_filter.filter()
        assert len(filtered_comments_df.index) == 2
        search_filter = CommentsReportSearchFilter("t", comments_df)
        filtered_comments_df = search_filter.filter()
        assert len(filtered_comments_df.index) == 1

    def test_conversation_has_stereotypes(self, cluster_db, stereotype_vote):
        cluster_db.stereotypes.add(stereotype_vote.author)
        cluster_db.users.add(cluster_db.clusterization.conversation.author)
        cluster_db.save()
        clusterization = Clusterization.objects.filter(
            conversation=cluster_db.conversation
        )
        assert conversation_has_stereotypes(clusterization)


class TestUsersReport(TestReport):
    no_group_text = "No group"

    @pytest.fixture
    def user_cluster(self, conversation_with_comments):
        clusterization = Clusterization.objects.create(
            conversation=conversation_with_comments, cluster_status=ClusterStatus.ACTIVE
        )
        cluster = Cluster.objects.create(name="name", clusterization=clusterization)
        comments = conversation_with_comments.comments
        stereotype, _ = Stereotype.objects.get_or_create(
            name="name", owner=conversation_with_comments.author
        )
        cluster.stereotypes.add(stereotype)

        StereotypeVote.objects.create(
            choice=Choice.AGREE, comment=comments[0], author_id=stereotype.id
        )
        StereotypeVote.objects.create(
            choice=Choice.SKIP, comment=comments[1], author_id=stereotype.id
        )
        StereotypeVote.objects.create(
            choice=Choice.DISAGREE, comment=comments[2], author_id=stereotype.id
        )
        StereotypeVote.objects.create(
            choice=Choice.DISAGREE, comment=comments[3], author_id=stereotype.id
        )
        clusterization.update_clusterization(force=True)
        yield cluster

    def test_get_user_dataframe(self, conversation_with_comments):
        users_df = get_user_dataframe(conversation_with_comments, "")
        assert users_df.iloc[[0]].get("group").item() == TestUsersReport.no_group_text
        assert users_df.iloc[[1]].get("group").item() == TestUsersReport.no_group_text
        assert users_df.iloc[[2]].get("group").item() == TestUsersReport.no_group_text
        assert len(users_df.index) == 3

    def test_get_cluster_users_dataframe(self, conversation_with_comments, user_cluster):

        clusters_filter = UsersReportClustersFilter(
            [user_cluster.id], conversation_with_comments
        )
        users_df = clusters_filter.filter()

        assert users_df.iloc[[0]].get("group").item() == user_cluster.name
        assert users_df.iloc[[1]].get("group").item() == user_cluster.name
        assert users_df.iloc[[2]].get("group").item() == user_cluster.name
        assert len(users_df.index) == 3

    def test_filter_users_by_group_with_no_group(self, conversation_with_comments):
        clusters_filter = UsersReportClustersFilter([], conversation_with_comments)
        filtered_users_df = clusters_filter.filter()
        assert (
            filtered_users_df.iloc[[0]].get("group").item()
            == TestUsersReport.no_group_text
        )
        assert (
            filtered_users_df.iloc[[1]].get("group").item()
            == TestUsersReport.no_group_text
        )
        assert (
            filtered_users_df.iloc[[2]].get("group").item()
            == TestUsersReport.no_group_text
        )
        assert len(filtered_users_df.index) == 3

    def test_filter_users_by_group(self, conversation_with_comments, user_cluster):
        clusters_filter = UsersReportClustersFilter(
            [user_cluster.id], conversation_with_comments
        )
        filtered_users_df = clusters_filter.filter()
        assert filtered_users_df.iloc[[0]].get("group").item() == user_cluster.name
        assert filtered_users_df.iloc[[1]].get("group").item() == user_cluster.name
        assert filtered_users_df.iloc[[2]].get("group").item() == user_cluster.name
        assert len(filtered_users_df.index) == 3

    def test_sort_user_dataframe_in_descending_order(self, conversation_with_comments):
        clusters_filter = UsersReportClustersFilter([], conversation_with_comments)
        users_df = clusters_filter.filter()

        orderby_filter = ReportOrderByFilter("email", users_df)
        sorted_users_df = orderby_filter.filter()
        assert sorted_users_df.iloc[[0]].get("participant").item() == "user3@email.br"
        assert sorted_users_df.iloc[[1]].get("participant").item() == "user2@email.br"
        assert sorted_users_df.iloc[[2]].get("participant").item() == "user1@email.br"

        orderby_filter = ReportOrderByFilter("name", users_df)
        sorted_users_df = orderby_filter.filter()
        assert sorted_users_df.iloc[[0]].get("participant").item() == "user3@email.br"
        assert sorted_users_df.iloc[[1]].get("participant").item() == "user2@email.br"
        assert sorted_users_df.iloc[[2]].get("participant").item() == "user1@email.br"

        orderby_filter = ReportOrderByFilter("date_joined", users_df)
        sorted_users_df = orderby_filter.filter()
        assert sorted_users_df.iloc[[0]].get("participant").item() == "user3@email.br"
        assert sorted_users_df.iloc[[1]].get("participant").item() == "user2@email.br"
        assert sorted_users_df.iloc[[2]].get("participant").item() == "user1@email.br"

    def test_sort_users_dataframe_in_ascending_order(self, conversation_with_comments):
        clusters_filter = UsersReportClustersFilter([], conversation_with_comments)
        users_df = clusters_filter.filter()

        orderby_filter = ReportOrderByFilter("email", users_df, True)
        sorted_users_df = orderby_filter.filter()
        assert sorted_users_df.iloc[[0]].get("participant").item() == "user1@email.br"
        assert sorted_users_df.iloc[[1]].get("participant").item() == "user2@email.br"
        assert sorted_users_df.iloc[[2]].get("participant").item() == "user3@email.br"

        orderby_filter = ReportOrderByFilter("date_joined", users_df, True)
        sorted_users_df = orderby_filter.filter()
        assert sorted_users_df.iloc[[0]].get("participant").item() == "user1@email.br"
        assert sorted_users_df.iloc[[1]].get("participant").item() == "user2@email.br"
        assert sorted_users_df.iloc[[2]].get("participant").item() == "user3@email.br"

    def test_search_string_users_dataframe(self, conversation_with_comments):
        clusters_filter = UsersReportClustersFilter([], conversation_with_comments)
        users_df = clusters_filter.filter()

        search_filter = UsersReportSearchFilter("user", users_df)
        filtered_users_df = search_filter.filter()
        assert len(filtered_users_df.index) == 3
        search_filter = UsersReportSearchFilter("user1", users_df)
        filtered_users_df = search_filter.filter()
        assert len(filtered_users_df.index) == 1
        search_filter = UsersReportSearchFilter("user2", users_df)
        filtered_users_df = search_filter.filter()
        assert len(filtered_users_df.index) == 1

        search_filter = UsersReportSearchFilter("@email.br", users_df)
        filtered_users_df = search_filter.filter()
        assert len(filtered_users_df.index) == 3
