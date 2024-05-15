import pytest
from django.test import Client
from django.urls import reverse
from boogie.testing.pytest import UrlTester
from ej_clusters.enums import ClusterStatus
from ej_clusters.models.cluster import Cluster
from ej_clusters.models.stereotype import Stereotype
from ej_clusters.mommy_recipes import ClusterRecipes
from ej_clusters.models.stereotype_vote import StereotypeVote
from ej_clusters.models.clusterization import Clusterization
from ej_conversations.enums import Choice
from ej_conversations.models.comment import Comment
from ej_conversations.mommy_recipes import ConversationRecipes

from ej_clusters.stereotypes_utils import order_stereotype_votes_by


class TestRoutes(ConversationRecipes, UrlTester):
    user_urls = ["/stereotypes/"]
    owner_urls = ["/conversations/1/conversation/stereotypes/"]

    @pytest.fixture
    def data(self, conversation, board, author_db):
        conversation.author = author_db
        board.owner = author_db
        board.save()
        conversation.board = board
        conversation.save()


class TestStereotypeVoteRoute(ClusterRecipes):
    @pytest.fixture
    def conversation_with_board(self, conversation, board, user_db):
        conversation.author = user_db
        board.owner = user_db
        board.save()
        conversation.board = board
        conversation.save()
        return conversation

    def test_get_stereotype_vote_page_without_stereotypes(
        self, conversation_with_board, user_db, rf
    ):
        Clusterization.objects.create(
            conversation=conversation_with_board, cluster_status=ClusterStatus.ACTIVE
        )

        client = Client()
        client.force_login(user_db)

        path = reverse(
            "boards:cluster-stereotype_votes",
            kwargs={
                "board_slug": conversation_with_board.board.slug,
                "conversation_id": conversation_with_board.id,
                "slug": conversation_with_board.slug,
            },
        )
        response = client.get(path)

        assert response.status_code == 200

    def test_get_stereotypes_of_conversation_without_clusters(
        self, conversation_with_board, user_db, rf
    ):
        client = Client()
        client.force_login(user_db)

        path = reverse(
            "boards:cluster-stereotype_votes",
            kwargs={
                "board_slug": conversation_with_board.board.slug,
                "conversation_id": conversation_with_board.id,
                "slug": conversation_with_board.slug,
            },
        )
        response = client.get(path)

        assert response.status_code == 200

    def test_get_stereotype_vote_page_with_one_stereotype(
        self, conversation_with_board, user_db, rf
    ):
        clusterization = Clusterization.objects.create(
            conversation=conversation_with_board, cluster_status=ClusterStatus.ACTIVE
        )
        cluster = Cluster.objects.create(name="name", clusterization=clusterization)
        stereotype, _ = Stereotype.objects.get_or_create(name="name", owner=user_db)
        cluster.stereotypes.add(stereotype)

        client = Client()
        client.force_login(user_db)

        path = reverse(
            "boards:cluster-stereotype_votes",
            kwargs={
                "board_slug": conversation_with_board.board.slug,
                "conversation_id": conversation_with_board.id,
                "slug": conversation_with_board.slug,
            },
        )
        response = client.get(path)

        assert response.status_code == 200

    def test_get_stereotype_vote_page_with_stereotypes_selected(
        self, conversation_with_board, user_db, rf
    ):
        clusterization = Clusterization.objects.create(
            conversation=conversation_with_board, cluster_status=ClusterStatus.ACTIVE
        )

        cluster = Cluster.objects.create(name="name", clusterization=clusterization)
        stereotype, _ = Stereotype.objects.get_or_create(name="name", owner=user_db)
        second_stereotype, _ = Stereotype.objects.get_or_create(
            name="second stereotype", owner=user_db
        )
        cluster.stereotypes.add(stereotype)
        cluster.stereotypes.add(second_stereotype)

        client = Client()
        client.force_login(user_db)

        path = reverse(
            "boards:cluster-stereotype_votes",
            kwargs={
                "board_slug": conversation_with_board.board.slug,
                "conversation_id": conversation_with_board.id,
                "slug": conversation_with_board.slug,
            },
        )
        response = client.get(path, {"stereotype-select": second_stereotype.id})

        assert response.status_code == 200

    def test_post_update_stereotype_vote_page_with_stereotypes(
        self, conversation_with_board, user_db, board, rf
    ):
        clusterization = Clusterization.objects.create(
            conversation=conversation_with_board, cluster_status=ClusterStatus.ACTIVE
        )
        comment = Comment.objects.create(
            content="comment", conversation=conversation_with_board, author=user_db
        )
        stereotype, _ = Stereotype.objects.get_or_create(name="name", owner=user_db)
        cluster = Cluster.objects.create(name="name", clusterization=clusterization)
        cluster.stereotypes.add(stereotype)
        stereotype_vote = StereotypeVote.objects.create(
            choice=Choice.AGREE, comment=comment, author_id=stereotype.id
        )
        assert stereotype_vote.choice == Choice.AGREE

        client = Client()
        client.force_login(user_db)

        path = reverse(
            "boards:cluster-stereotype_votes",
            kwargs={
                "board_slug": conversation_with_board.board.slug,
                "conversation_id": conversation_with_board.id,
                "slug": conversation_with_board.slug,
            },
        )
        response = client.post(
            path,
            {"update": f"skip-{stereotype_vote.id}", "stereotype": stereotype.id},
        )

        assert response.status_code == 200

    def test_post_delete_stereotype_vote_page_with_stereotypes(
        self, conversation_with_board, user_db, rf
    ):
        clusterization = Clusterization.objects.create(
            conversation=conversation_with_board, cluster_status=ClusterStatus.ACTIVE
        )
        comment = Comment.objects.create(
            content="comment", conversation=conversation_with_board, author=user_db
        )
        stereotype, _ = Stereotype.objects.get_or_create(name="name", owner=user_db)
        cluster = Cluster.objects.create(name="name", clusterization=clusterization)
        cluster.stereotypes.add(stereotype)
        stereotype_vote = StereotypeVote.objects.create(
            choice=Choice.AGREE, comment=comment, author_id=stereotype.id
        )

        client = Client()
        client.force_login(user_db)

        path = reverse(
            "boards:cluster-stereotype_votes",
            kwargs={
                "board_slug": conversation_with_board.board.slug,
                "conversation_id": conversation_with_board.id,
                "slug": conversation_with_board.slug,
            },
        )
        response = client.post(
            path,
            {"update": f"delete-{stereotype_vote.id}", "stereotype": stereotype.id},
        )

        assert not StereotypeVote.objects.filter(id=stereotype_vote.id).exists()
        assert response.status_code == 200

    def test_auxiliar_parse_choice_from_action(self):
        response_id, response_choice = StereotypeVote.parse_choice_from_action(
            "delete-id"
        )
        assert response_id == "id"
        assert response_choice == "delete"

    def test_auxiliar_order_by_stereotype_vote_choice(
        self, conversation_with_board, user_db
    ):
        clusterization = Clusterization.objects.create(
            conversation=conversation_with_board, cluster_status=ClusterStatus.ACTIVE
        )
        comment = Comment.objects.create(
            content="comment", conversation=conversation_with_board, author=user_db
        )
        comment2 = Comment.objects.create(
            content="comment 2", conversation=conversation_with_board, author=user_db
        )
        comment3 = Comment.objects.create(
            content="comment 3", conversation=conversation_with_board, author=user_db
        )
        stereotype, _ = Stereotype.objects.get_or_create(name="name", owner=user_db)
        cluster = Cluster.objects.create(name="name", clusterization=clusterization)
        cluster.stereotypes.add(stereotype)
        stereotype_vote_agree = StereotypeVote.objects.create(
            choice=Choice.AGREE, comment=comment, author_id=stereotype.id
        )
        stereotype_vote_skip = StereotypeVote.objects.create(
            choice=Choice.SKIP, comment=comment2, author_id=stereotype.id
        )
        stereotype_vote_disagree = StereotypeVote.objects.create(
            choice=Choice.DISAGREE, comment=comment3, author_id=stereotype.id
        )

        steoreotype_votes_list = clusterization.stereotype_votes.filter(author=stereotype)
        return_with_agree_first = order_stereotype_votes_by(
            steoreotype_votes_list, 1, "-"
        )
        assert return_with_agree_first.first() == stereotype_vote_agree
        assert return_with_agree_first.last() == stereotype_vote_disagree

        return_with_disagree_first = order_stereotype_votes_by(
            steoreotype_votes_list, -1, "-"
        )
        assert return_with_disagree_first.first() == stereotype_vote_disagree
        assert return_with_disagree_first.last() == stereotype_vote_agree

        return_with_skip_first = order_stereotype_votes_by(steoreotype_votes_list, 0, "-")
        assert return_with_skip_first.first() == stereotype_vote_skip
        assert return_with_skip_first.last() == stereotype_vote_disagree

    def test_auxiliar_post_create_stereotype_vote(
        self, conversation_with_board, user_db, rf
    ):
        clusterization = Clusterization.objects.create(
            conversation=conversation_with_board, cluster_status=ClusterStatus.ACTIVE
        )
        comment = Comment.objects.create(
            content="comment", conversation=conversation_with_board, author=user_db
        )
        cluster = Cluster.objects.create(name="name", clusterization=clusterization)
        stereotype, _ = Stereotype.objects.get_or_create(name="name", owner=user_db)
        cluster.stereotypes.add(stereotype)

        path = f"{conversation_with_board.get_absolute_url()}stereotypes/stereotype-votes/create"

        client = Client()
        client.force_login(user_db)

        response = client.post(
            path,
            {"comment": comment.id, "author": stereotype.id, "choice": "1"},
        )

        assert response.content.decode() == str(
            clusterization.stereotype_votes.filter(author=stereotype).first().id
        )
