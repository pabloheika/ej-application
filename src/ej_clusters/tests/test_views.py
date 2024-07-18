import pytest
from django.test import Client
from django.urls import reverse
from django.template.exceptions import TemplateDoesNotExist
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
from ej_conversations.tests.test_views import ConversationSetup


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


@pytest.fixture
def stereotype(base_user):
    stereotype, _ = Stereotype.objects.get_or_create(name="name", owner=base_user)
    return stereotype


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
            "boards:stereotype-votes-list",
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
            "boards:stereotype-votes-list",
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
            "boards:stereotype-votes-list",
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
            "boards:stereotype-votes-list",
            kwargs={
                "board_slug": conversation_with_board.board.slug,
                "conversation_id": conversation_with_board.id,
                "slug": conversation_with_board.slug,
            },
        )
        response = client.get(path, {"stereotype-select": second_stereotype.id})

        assert response.status_code == 200

    def test_auxiliar_parse_choice_from_action(self):
        response_id, response_choice = StereotypeVote.parse_choice_from_action(
            "delete-id"
        )
        assert response_id == "id"
        assert response_choice == "delete"

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


class TestStereotypeDelete(ConversationSetup):
    def test_get_access_delete_stereotype_view(self, base_user, stereotype):
        url = reverse("stereotypes:delete", kwargs={"pk": stereotype.id})

        client = Client()
        client.force_login(base_user)

        with pytest.raises(TemplateDoesNotExist):
            client.get(url)
        assert Stereotype.objects.filter(id=stereotype.id).exists()

    def test_delete_stereotype_with_no_permission(self, stereotype):
        url = reverse("stereotypes:delete", kwargs={"pk": stereotype.id})

        client = Client()
        response = client.post(url)

        assert response.status_code == 302
        assert "/login/" in response.url
        assert Stereotype.objects.filter(id=stereotype.id).exists()

    def test_delete_stereotype(self, base_user, stereotype, conversation_with_comments):
        url = reverse("stereotypes:delete", kwargs={"pk": stereotype.id})

        client = Client()
        client.force_login(base_user)
        clusters = stereotype.clusters
        response = client.post(url, {"conversation_id": conversation_with_comments.id})

        assert response.status_code == 302
        assert response.url == reverse(
            "boards:stereotype-votes-list",
            kwargs=conversation_with_comments.get_url_kwargs(),
        )
        assert not Stereotype.objects.filter(id=stereotype.id).exists()
        assert not Cluster.objects.filter(id__in=clusters).exists()

    def test_admin_delete_stereotype(
        self, admin_user, stereotype, conversation_with_comments
    ):
        url = reverse("stereotypes:delete", kwargs={"pk": stereotype.id})

        client = Client()
        client.force_login(admin_user)
        clusters = stereotype.clusters
        response = client.post(url, {"conversation_id": conversation_with_comments.id})

        assert response.status_code == 302
        assert response.url == reverse(
            "boards:stereotype-votes-list",
            kwargs=conversation_with_comments.get_url_kwargs(),
        )
        assert not Stereotype.objects.filter(id=stereotype.id).exists()
        assert not Cluster.objects.filter(id__in=clusters).exists()


class TestStereotypeEdit(ConversationSetup):
    def test_post_edit_stereotype(self, base_user, stereotype):
        url = reverse("stereotypes:edit", kwargs={"pk": stereotype.id})

        client = Client()
        client.force_login(base_user)

        new_name = "new name"
        response = client.post(
            url,
            {
                "name": new_name,
                "description": stereotype.description,
            },
        )
        stereotype.refresh_from_db()

        assert response.status_code == 200
        assert stereotype.name == new_name

    def test_post_edit_stereotype_without_required_field(self, base_user, stereotype):
        url = reverse("stereotypes:edit", kwargs={"pk": stereotype.id})

        client = Client()
        client.force_login(base_user)

        response = client.post(url)
        stereotype.refresh_from_db()

        assert response.status_code == 200
        assert b"This field is required." in response.content


class TestStereotypeVoteDelete(ConversationSetup):
    @pytest.fixture
    def stereotype_vote(self, conversation_with_comments, stereotype):
        clusterization = Clusterization.objects.create(
            conversation=conversation_with_comments, cluster_status=ClusterStatus.ACTIVE
        )
        comment = conversation_with_comments.comments.first()
        cluster = Cluster.objects.create(name="name", clusterization=clusterization)
        cluster.stereotypes.add(stereotype)
        stereotype_vote = StereotypeVote.objects.create(
            choice=Choice.AGREE, comment=comment, author_id=stereotype.id
        )
        return stereotype_vote

    def test_get_access_delete_stereotype_vote_view(
        self, base_user, stereotype_vote, conversation_with_comments
    ):
        url = reverse(
            "boards:stereotype-votes-delete",
            kwargs={
                "pk": stereotype_vote.id,
                **conversation_with_comments.get_url_kwargs(),
            },
        )

        client = Client()
        client.force_login(base_user)

        with pytest.raises(TemplateDoesNotExist):
            client.get(url)
        assert StereotypeVote.objects.filter(id=stereotype_vote.id).exists()

    def test_delete_stereotype_vote_with_no_permission(
        self, stereotype_vote, conversation_with_comments
    ):
        url = reverse(
            "boards:stereotype-votes-delete",
            kwargs={
                "pk": stereotype_vote.id,
                **conversation_with_comments.get_url_kwargs(),
            },
        )

        client = Client()
        response = client.post(url)

        assert response.status_code == 302
        assert "/login/" in response.url
        assert StereotypeVote.objects.filter(id=stereotype_vote.id).exists()

    def test_delete_stereotype_vote(
        self, base_user, stereotype_vote, conversation_with_comments
    ):
        url = reverse(
            "boards:stereotype-votes-delete",
            kwargs={
                "pk": stereotype_vote.id,
                **conversation_with_comments.get_url_kwargs(),
            },
        )

        client = Client()
        client.force_login(base_user)
        response = client.post(url)

        assert response.status_code == 302
        assert response.url == "/"
        assert not StereotypeVote.objects.filter(id=stereotype_vote.id).exists()

    def test_admin_delete_stereotype_vote(
        self, admin_user, stereotype_vote, conversation_with_comments
    ):
        url = reverse(
            "boards:stereotype-votes-delete",
            kwargs={
                "pk": stereotype_vote.id,
                **conversation_with_comments.get_url_kwargs(),
            },
        )

        client = Client()
        client.force_login(admin_user)
        response = client.post(url)

        assert response.status_code == 302
        assert response.url == "/"
        assert not StereotypeVote.objects.filter(id=stereotype_vote.id).exists()
