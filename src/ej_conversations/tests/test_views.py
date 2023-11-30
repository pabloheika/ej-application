from django.test import Client
from django.http import HttpResponseServerError
from django.contrib.auth.models import AnonymousUser
from pytest import raises
import pytest
import json
from ej_boards.models import Board

from ej_conversations import create_conversation, views
from ej_conversations.models import Comment, FavoriteConversation, Conversation
from ej_conversations.mommy_recipes import ConversationRecipes
from ej_conversations.utils import votes_counter
from ej_conversations.roles.comments import comment_summary
from ej_users.models import User
from ..enums import Choice


class ConversationSetup:
    @pytest.fixture
    def admin_user(self, db):
        admin_user = User.objects.create_superuser("admin@test.com", "pass")
        admin_user.save()
        return admin_user

    @pytest.fixture
    def logged_admin(self, admin_user):
        client = Client()
        client.force_login(admin_user)
        return client

    @pytest.fixture
    def base_user(self, db):
        user = User.objects.create_user("tester@email.br", "password")
        profile = user.get_profile()
        profile.save()
        return user

    @pytest.fixture
    def base_board(self, base_user):
        board = Board.objects.create(slug="userboard", owner=base_user, description="board")
        return board


class TestConversationDetail(ConversationSetup):
    @pytest.fixture
    def first_conversation(self, admin_user):
        board = Board.objects.create(slug="board", owner=admin_user, description="board")
        conversation = create_conversation("foo", "conv1", admin_user, board=board)
        conversation.create_comment(admin_user, "ad", status="approved", check_limits=False)
        conversation.create_comment(admin_user, "ad2", status="approved", check_limits=False)
        conversation.is_promoted = True
        conversation.is_hidden = False
        conversation.save()
        return conversation

    def test_vote_agree_in_comment(self, first_conversation):
        user = User.objects.create_user("user@server.com", "password")

        client = Client()
        client.force_login(user)

        comment = first_conversation.comments.first()
        response = client.post(
            f"/board/conversations/{first_conversation.id}/{first_conversation.slug}/",
            {"action": "vote", "vote": "agree", "comment_id": comment.id},
        )

        assert response.context["conversation"] == first_conversation
        assert votes_counter(comment) == 1

        vote = comment.votes.first()
        assert vote.choice == Choice.AGREE

    def test_vote_disagree_in_comment(self, first_conversation):
        user = User.objects.create_user("user@server.com", "password")

        client = Client()
        client.force_login(user)

        comment = first_conversation.comments.first()
        response = client.post(
            f"/board/conversations/{first_conversation.id}/{first_conversation.slug}/",
            {"action": "vote", "vote": "disagree", "comment_id": comment.id},
        )
        assert response.context["conversation"] == first_conversation
        assert votes_counter(comment) == 1

        vote = comment.votes.first()
        assert vote.choice == Choice.DISAGREE

    def test_vote_skip_in_comment(self, first_conversation):
        user = User.objects.create_user("user@server.com", "password")

        client = Client()
        client.force_login(user)

        comment = first_conversation.comments.first()
        response = client.post(
            f"/board/conversations/{first_conversation.id}/{first_conversation.slug}/",
            {"action": "vote", "vote": "skip", "comment_id": comment.id},
        )
        assert response.context["conversation"] == first_conversation
        assert votes_counter(comment) == 1

        vote = comment.votes.first()
        assert vote.choice == Choice.SKIP

    def test_invalid_vote_in_comment(self, first_conversation):
        user = User.objects.create_user("user@server.com", "password")

        client = Client()
        client.force_login(user)

        comment = first_conversation.comments.first()
        with raises(Exception):
            client.post(
                f"/board/conversations/{first_conversation.id}/{first_conversation.slug}/",
                {"action": "vote", "vote": "INVALID", "comment_id": comment.id},
            )

    def test_invalid_action_conversation_detail(self, first_conversation):
        user = User.objects.create_user("user@server.com", "password")

        client = Client()
        client.force_login(user)

        comment = first_conversation.comments.first()

        response = client.post(
            f"/board/conversations/{first_conversation.id}/{first_conversation.slug}/",
            {"action": "invalid", "vote": "INVALID", "comment_id": comment.id},
        )
        assert isinstance(response, HttpResponseServerError)

    def test_user_can_comment(self, first_conversation):
        user = User.objects.create_user("user@server.com", "password")

        client = Client()
        client.force_login(user)

        client.post(
            f"/board/conversations/{first_conversation.id}/{first_conversation.slug}/",
            {"action": "comment", "content": "test comment"},
        )

        assert Comment.objects.filter(author=user)[0].content == "test comment"

    def test_user_post_invalid_comment(self, first_conversation):
        user = User.objects.create_user("user@server.com", "password")

        client = Client()
        client.force_login(user)

        client.post(
            f"/board/conversations/{first_conversation.id}/{first_conversation.slug}/",
            {"action": "comment", "content": ""},
        )

        assert not Comment.objects.filter(author=user).exists()

    def test_anonymous_user_cannot_participate(self, first_conversation):
        client = Client()
        comment = first_conversation.comments.first()

        conversation_url = f"/board/conversations/{first_conversation.id}/{first_conversation.slug}/"
        response = client.get(conversation_url)
        assert response.status_code == 200

        response = client.post(
            conversation_url,
            {"action": "vote", "vote": "agree", "comment_id": comment.id},
        )
        assert response.status_code == 302
        assert response["HX-Redirect"] == f"/register/?next={conversation_url}"

        response = client.post(
            conversation_url,
            {"action": "comment", "content": "test comment"},
        )
        assert response.status_code == 302
        assert response["HX-Redirect"] == f"/register/?next={conversation_url}"

        response = client.post(
            conversation_url,
            {"action": "favorite"},
        )
        assert response.status_code == 302
        assert response["HX-Redirect"] == f"/register/?next={conversation_url}"

    def test_anonymous_user_can_participate(self, first_conversation):
        client = Client()
        comment = first_conversation.comments.first()
        conversation_url = f"/board/conversations/{first_conversation.id}/{first_conversation.slug}/"
        response = client.get(conversation_url)
        assert response.status_code == 200
        response = client.post(
            conversation_url,
            {"action": "vote", "vote": "agree", "comment_id": comment.id},
        )
        assert response.status_code == 302
        assert response["HX-Redirect"] == f"/register/?next={conversation_url}"

        first_conversation.anonymous_votes_limit = 1
        first_conversation.save()

        response = client.post(
            conversation_url,
            {"action": "vote", "vote": "agree", "comment_id": comment.id},
        )
        assert response.status_code == 200

    def test_register_user_from_session_after_conversation_anonymous_limit(self, first_conversation):
        first_conversation.anonymous_votes_limit = 1
        first_conversation.save()

        client = Client()

        conversation_url = f"/board/conversations/{first_conversation.id}/{first_conversation.slug}/"
        first_comment = first_conversation.comments.first()
        last_comment = first_conversation.comments.last()

        client.post(
            conversation_url,
            {"action": "vote", "vote": "agree", "comment_id": first_comment.id},
        )

        session_user_email = User.objects.last().email

        response = client.post(
            conversation_url,
            {"action": "vote", "vote": "agree", "comment_id": last_comment.id},
        )

        register_url = response["HX-Redirect"]
        response = client.post(
            register_url,
            data={
                "name": "Tester",
                "email": "tester@example.com",
                "password": "pass123",
                "password_confirm": "pass123",
                "agree_with_terms": True,
                "agree_with_privacy_policy": True,
            },
        )
        user = User.objects.get(email="tester@example.com")

        assert user.votes.count() == 1
        assert user.votes.first().comment == first_comment
        assert user.votes.first().choice == Choice.AGREE
        assert not User.objects.filter(email=session_user_email).exists()

    def test_user_can_add_conversation_as_favorite(self, first_conversation):
        user = User.objects.create_user("user@server.com", "password")

        client = Client()
        client.force_login(user)

        client.post(
            f"/board/conversations/{first_conversation.id}/{first_conversation.slug}/",
            {"action": "favorite"},
        )

        assert FavoriteConversation.objects.filter(user=user, conversation=first_conversation).exists()

    def test_user_progress_zero(self, first_conversation):
        user = User.objects.create_user("user@server.com", "password")

        percentage = first_conversation.user_progress_percentage(user)
        assert percentage == 0

    def test_user_progress_after_voting(self, first_conversation, admin_user):
        comment = first_conversation.create_comment(
            admin_user, "other comment here", status="approved", check_limits=False
        )

        comment.vote(admin_user, Choice.AGREE)
        percentage = first_conversation.user_progress_percentage(admin_user)
        assert percentage > 0

    def test_user_progress_anonymous(self, first_conversation):
        user = AnonymousUser()

        percentage = first_conversation.user_progress_percentage(user)
        assert percentage == 0

    def test_user_progress_conversation_with_no_comments(self, admin_user):
        user = AnonymousUser()
        board = Board.objects.create(slug="board12", owner=admin_user, description="board12")
        conversation = create_conversation("foo", "conv1", admin_user, board=board)
        conversation.is_promoted = True
        conversation.is_hidden = False
        conversation.save()

        percentage = conversation.user_progress_percentage(user)
        assert percentage == 1


class TestConversationCreate(ConversationSetup):
    def test_board_owner_can_create_conversation(self, base_board, base_user):
        url = "/userboard/conversations/add/"
        client = Client()
        client.force_login(base_user)

        response = client.post(
            url,
            {
                "title": "whatever",
                "tags": "tag",
                "text": "description",
                "comments_count": 0,
                "anonymous_votes_limit": 0,
            },
        )
        assert response.status_code == 302
        assert response.url == "/userboard/conversations/1/whatever/"

        conversation = Conversation.objects.first()
        assert conversation.is_promoted == False
        assert conversation.board == base_board

    def test_user_should_not_create_conversation_on_another_users_board(self, base_board, base_user):
        url = "/userboard/conversations/add/"

        user = User.objects.create_user("user2@email.br", "password")
        client = Client()
        client.force_login(user)

        response = client.post(
            url,
            {
                "title": "whatever",
                "tags": "tag",
                "text": "description",
                "comments_count": 0,
                "anonymous_votes_limit": 0,
            },
        )
        assert response.status_code == 302
        assert response.url == "/login/"

    def test_anonymous_user_should_not_create_conversation(self):
        url = "/userboard/conversations/add/"
        client = Client()

        response = client.post(
            url, {"title": "whatever", "tags": "tag", "text": "description", "comments_count": 0}
        )

        assert response.status_code == 302
        assert response.url == "/login/?next=/userboard/conversations/add/"

    def test_should_not_create_invalid_conversation(self, base_board, base_user):
        url = "/userboard/conversations/add/"
        client = Client()
        client.force_login(base_user)

        response = client.post(
            url, {"title": "", "tags": "tag", "text": "description", "comments_count": 0}
        )

        assert not response.context["form"].is_valid()
        assert not Conversation.objects.filter(author=base_user).exists()

    def test_admin_can_create_conversations_on_another_users_board(
        self, admin_user, logged_admin, base_board
    ):
        url = "/userboard/conversations/add/"
        response = logged_admin.post(
            url,
            {
                "title": "whatever",
                "tags": "tag",
                "text": "description",
                "comments_count": 0,
                "anonymous_votes_limit": 0,
            },
        )
        conversation = Conversation.objects.first()

        assert response.status_code == 302
        assert response.url == "/userboard/conversations/1/whatever/"
        assert conversation.board == base_board
        assert conversation.author == admin_user


class TestConversationComments(ConversationSetup):
    def test_user_can_create_comments(self, logged_admin):
        user = User.objects.create_user("user1@email.br", "password")
        board = Board.objects.create(slug="board1", owner=user, description="board")
        client = Client()
        client.login(email="user1@email.br", password="password")
        conversation = create_conversation("foo", "conv1", user, board=board)
        comments = ["Some comment to test", "Some other comment to test"]
        url = f"/{board.slug}/conversations/{conversation.id}/{conversation.slug}/comments/new/"
        client.post(url, {"comment": comments})

        assert Comment.objects.get(content=comments[0], author=user).status == "approved"
        assert Comment.objects.get(content=comments[1], author=user).status == "approved"

    def test_comments_with_less_than_2_chars_arent_created(self, logged_admin):
        user = User.objects.create_user("user1@email.br", "password")
        board = Board.objects.create(slug="board1", owner=user, description="board")
        client = Client()
        client.login(email="user1@email.br", password="password")
        conversation = create_conversation("foo", "conv1", user, board=board)
        comments = ["A", "Some other comment to test"]
        url = f"/{board.slug}/conversations/{conversation.id}/{conversation.slug}/comments/new/"
        client.post(url, {"comment": comments})

        assert Comment.objects.get(content=comments[1], author=user).status == "approved"
        assert Comment.objects.all().count() == 1

    def test_admin_can_delete_comment(self, logged_admin):
        user = User.objects.create_user("user1@email.br", "password")
        board = Board.objects.create(slug="board1", owner=user, description="board")
        client = Client()
        client.login(email="user1@email.br", password="password")
        conversation = create_conversation("foo", "conv1", user, board=board)
        comment = conversation.create_comment(author=user, content="comment to delete", status="approved")
        url = f"/{board.slug}/conversations/{conversation.id}/{conversation.slug}/comments/delete/"
        client.post(url, {"comment_id": comment.id})

        assert Comment.objects.all().count() == 0

    def test_admin_cant_delete_others_users_comments(self, logged_admin):
        user_1 = User.objects.create_user("user1@email.br", "password")
        user_2 = User.objects.create_user("user2@email.br", "password2")
        board = Board.objects.create(slug="board1", owner=user_1, description="board")
        client = Client()
        client.login(email="user1@email.br", password="password")
        conversation = create_conversation("foo", "conv1", user_2, board=board)
        comment = conversation.create_comment(
            author=user_2, content="comment to not delete", status="approved"
        )
        url = f"/{board.slug}/conversations/{conversation.id}/{conversation.slug}/comments/delete/"
        client.post(url, {"comment_id": comment.id})

        assert Comment.objects.all().count() == 1

    def test_admin_can_check_for_repeated_comment(self, logged_admin):
        user = User.objects.create_user("user1@email.br", "password")
        board = Board.objects.create(slug="board1", owner=user, description="board")
        client = Client()
        client.login(email="user1@email.br", password="password")
        conversation = create_conversation("foo", "conv1", user, board=board)
        comment = conversation.create_comment(author=user, content="comment to check", status="approved")
        url = f"/{board.slug}/conversations/{conversation.id}/{conversation.slug}/comments/check/"
        response = client.post(url, {"comment_content": "comment to check"})

        assert response.status_code == 200

    def test_admin_can_check_for_not_repeated_comment(self, logged_admin):
        user = User.objects.create_user("user1@email.br", "password")
        board = Board.objects.create(slug="board1", owner=user, description="board")
        client = Client()
        client.login(email="user1@email.br", password="password")
        conversation = create_conversation("foo", "conv1", user, board=board)
        conversation.create_comment(author=user, content="comment to check", status="approved")
        url = f"/{board.slug}/conversations/{conversation.id}/{conversation.slug}/comments/check/"
        response = client.post(url, {"comment_content": "new and different comment to check"})

        assert response.status_code == 204


class TestConversationEdit(ConversationSetup):
    @pytest.fixture
    def another_logged_user(self, db):
        user = User.objects.create_user("user1@email.br", "password")
        profile = user.get_profile()
        profile.save()
        client = Client()
        client.force_login(user)
        return client

    @pytest.fixture
    def new_conversation(self, base_user, base_board):
        conversation = create_conversation(title="bar", text="conv", author=base_user, board=base_board)
        conversation.is_promoted = True
        conversation.save()
        return conversation

    def test_edit_conversation(self, base_user, new_conversation):
        url = f"/userboard/conversations/{new_conversation.id}/{new_conversation.slug}/edit/"

        client = Client()
        client.force_login(base_user)

        response = client.post(
            url,
            {
                "title": "bar updated",
                "tags": "tag",
                "text": "description",
                "comments_count": 0,
                "anonymous_votes_limit": 0,
            },
        )

        new_conversation.refresh_from_db()

        assert response.status_code == 302
        assert response.url == "/userboard/conversations/1/bar/"
        assert new_conversation.title == "bar updated"
        assert new_conversation.text == "description"

    def test_edit_invalid_conversation(self, base_user, new_conversation):
        url = f"/userboard/conversations/{new_conversation.id}/{new_conversation.slug}/edit/"

        client = Client()
        client.force_login(base_user)

        response = client.post(
            url, {"title": "", "tags": "tag", "text": "description", "comments_count": 0}
        )

        assert not response.context["form"].is_valid()

    def test_author_can_edit_not_promoted_conversation(self, base_user, new_conversation):
        url = f"/{new_conversation.board.slug}/conversations/{new_conversation.id}/{new_conversation.slug}/edit/"
        new_conversation.is_promoted = False
        new_conversation.save()

        client = Client()
        client.force_login(base_user)

        client.post(url, {"title": "bar updated", "text": "description", "anonymous_votes_limit": 1})

        conversation = Conversation.objects.get(id=new_conversation.id)
        assert conversation.title == "bar updated"
        assert conversation.text == "description"
        assert conversation.anonymous_votes_limit == 1

    def test_get_edit_conversation(self, base_user, new_conversation):
        url = f"/userboard/conversations/{new_conversation.id}/{new_conversation.slug}/edit/"
        comment = new_conversation.create_comment(base_user, "comment", "pending")
        new_conversation.create_comment(base_user, "comment1")
        comment.status = comment.STATUS.pending
        comment.save()

        client = Client()
        client.force_login(base_user)

        response = client.get(url)
        new_conversation.refresh_from_db()

        assert response.context["conversation"] == new_conversation

    def test_admin_can_edit_conversation(self, new_conversation, logged_admin):
        url = f"/userboard/conversations/{new_conversation.id}/{new_conversation.slug}/edit/"

        response = logged_admin.post(
            url,
            {
                "title": "bar updated",
                "tags": "tag",
                "text": "description",
                "comments_count": 0,
                "anonymous_votes_limit": 0,
            },
        )

        new_conversation.refresh_from_db()

        assert response.status_code == 302
        assert response.url == "/userboard/conversations/1/bar/"
        assert new_conversation.title == "bar updated"
        assert new_conversation.text == "description"

    def test_user_cannot_edit_anothers_one_conversation(self, new_conversation, another_logged_user):
        url = f"/userboard/conversations/{new_conversation.id}/{new_conversation.slug}/edit/"
        client = Client()

        response = client.post(
            url, {"title": "bar updated", "tags": "tag", "text": "description", "comments_count": 0}
        )
        assert response.status_code == 302
        assert response.url == f"/login/?next={url}"

        new_conversation.refresh_from_db()
        assert new_conversation.title == "bar"
        assert new_conversation.text == "conv"

        response = another_logged_user.post(
            url, {"title": "bar updated", "tags": "tag", "text": "description", "comments_count": 0}
        )
        assert response.status_code == 302
        assert response.url == "/login/"

        new_conversation.refresh_from_db()
        assert new_conversation.title == "bar"
        assert new_conversation.text == "conv"


class TestConversationModerate(ConversationSetup):
    def test_user_can_moderate_comments(self, logged_admin):
        user = User.objects.create_user("user1@email.br", "password")
        board = Board.objects.create(slug="board1", owner=user, description="board")
        client = Client()
        client.login(email="user1@email.br", password="password")
        conversation = create_conversation("foo", "conv1", user, board=board)
        comment_to_approve = conversation.create_comment(
            author=user, content="comment to approve", status="pending"
        )
        comment_to_reject = conversation.create_comment(
            author=user, content="comment to reject", status="pending"
        )
        url = f"/{board.slug}/conversations/{conversation.id}/{conversation.slug}/moderate/"
        client.post(url, {"approved": comment_to_approve.id, "rejected": comment_to_reject.id})

        assert (
            conversation.comments.get(id=comment_to_approve.id).status == comment_to_approve.STATUS.approved
        )
        assert (
            conversation.comments.get(id=comment_to_reject.id).status == comment_to_reject.STATUS.rejected
        )

    def test_comment_status_is_correct(self, base_user, base_board):
        conversation = create_conversation("foo", "conv1", base_user, board=base_board)
        comment_to_approve_1 = conversation.create_comment(
            author=base_user, content="comment to approve 1", status="pending"
        )
        comment_to_approve_2 = conversation.create_comment(
            author=base_user, content="comment to approve 2", status="pending"
        )
        comment_to_reject = conversation.create_comment(
            author=base_user, content="comment to reject", status="pending"
        )
        pending_comment = conversation.create_comment(
            author=base_user, content="pending comment", status="pending"
        )

        client = Client()
        client.force_login(base_user)

        url = f"/{base_board.slug}/conversations/{conversation.id}/{conversation.slug}/moderate/"
        client.post(
            url,
            {
                "approved": [comment_to_approve_1.id, comment_to_approve_2.id],
                "rejected": comment_to_reject.id,
                "pending": pending_comment.id,
            },
        )

        assert (
            conversation.comments.get(id=comment_to_approve_1.id).status
            == comment_to_approve_1.STATUS.approved
        )
        assert (
            conversation.comments.get(id=comment_to_approve_2.id).status
            == comment_to_approve_2.STATUS.approved
        )
        assert (
            conversation.comments.get(id=comment_to_reject.id).status == comment_to_reject.STATUS.rejected
        )
        assert conversation.comments.get(id=pending_comment.id).status == pending_comment.STATUS.pending

    def test_get_moderate_comments(self, base_user, base_board):
        conversation = create_conversation("foo", "conv1", base_user, board=base_board)
        comment_to_approve_1 = conversation.create_comment(
            author=base_user, content="comment approved 1", status="pending"
        )
        comment_to_approve_2 = conversation.create_comment(
            author=base_user, content="comment approved 2", status="pending"
        )
        comment_to_reject = conversation.create_comment(
            author=base_user, content="comment to reject", status="pending"
        )
        pending_comment = conversation.create_comment(
            author=base_user, content="pending comment", status="pending"
        )

        client = Client()
        client.force_login(base_user)

        url = f"/{base_board.slug}/conversations/{conversation.id}/{conversation.slug}/moderate/"
        client.post(
            url,
            {
                "approved": [comment_to_approve_1.id, comment_to_approve_2.id],
                "rejected": comment_to_reject.id,
                "pending": pending_comment.id,
            },
        )
        response = client.get(url)

        assert len(response.context["approved"]) == 2
        assert comment_to_approve_1 in response.context["approved"]
        assert comment_to_approve_2 in response.context["approved"]
        assert len(response.context["rejected"]) == 1
        assert comment_to_reject in response.context["rejected"]
        assert len(response.context["pending"]) == 1
        assert pending_comment in response.context["pending"]


class TestPrivateConversations(ConversationRecipes):
    @pytest.fixture
    def admin_user(self, db):
        admin_user = User.objects.create_superuser("admin@test.com", "pass")
        profile = admin_user.get_profile()
        profile.save()
        admin_user.save()
        return admin_user

    @pytest.fixture
    def logged_admin(self, admin_user):
        client = Client()
        client.force_login(admin_user)
        return client

    @pytest.fixture
    def base_user(self, db):
        user = User.objects.create_user("tester@email.br", "password")
        profile = user.get_profile()
        profile.save()
        return user

    @pytest.fixture
    def base_board(self, base_user):
        board = Board.objects.create(slug="userboard", owner=base_user, description="board")
        return board

    @pytest.fixture
    def hiden_conversation(self, admin_user):
        board = Board.objects.create(slug="adminboard", owner=admin_user, description="board")
        conversation = create_conversation("foo", "conv", admin_user, board=board)
        conversation.is_hidden = True
        conversation.save()
        return conversation

    @pytest.fixture
    def first_conversation(self, base_board, base_user):
        conversation = create_conversation("bar", "conv1", base_user, board=base_board)
        conversation.is_hidden = False
        conversation.save()
        return conversation

    @pytest.fixture
    def second_conversation(self, base_board, base_user):
        conversation = create_conversation("forbar", "conv2", base_user, board=base_board)
        conversation.is_hidden = False
        conversation.save()
        return conversation

    @pytest.fixture
    def third_conversation(self, base_board, base_user):
        conversation = create_conversation("forbarbar", "conv3", base_user, board=base_board)
        conversation.is_hidden = True
        conversation.save()
        return conversation

    def test_user_can_access_their_board_conversations(
        self,
        logged_admin,
        base_board,
        hiden_conversation,
        first_conversation,
        second_conversation,
        third_conversation,
    ):
        user_url = f"/userboard/conversations/"

        client = Client()
        client.login(email="tester@email.br", password="password")
        response = client.get(user_url)

        assert len(response.context["conversations"]) == 3
        assert first_conversation in response.context["conversations"]
        assert second_conversation in response.context["conversations"]
        assert len(response.context["user_boards"]) == 2
        assert base_board in response.context["user_boards"]

        admin_url = "/adminboard/conversations/"
        response = logged_admin.get(admin_url)

        assert len(response.context["conversations"]) == 1
        assert hiden_conversation in response.context["conversations"]

    def test_anonymous_user_should_not_access_board_conversations(
        self, admin_user, base_user, hiden_conversation, first_conversation, second_conversation
    ):
        admin_url = f"/adminboard/conversations/"
        anonymous_user = Client()
        response = anonymous_user.get(admin_url)
        assert response.status_code == 302
        assert response.url == "/login/?next=/adminboard/conversations/"

    def test_only_admin_user_can_access_others_conversations(
        self, logged_admin, base_user, hiden_conversation, first_conversation, second_conversation
    ):
        user_url = f"/userboard/conversations/"
        response = logged_admin.get(user_url)

        assert len(response.context["conversations"]) == 2
        assert first_conversation in response.context["conversations"]
        assert second_conversation in response.context["conversations"]

        admin_url = f"/adminboard/conversations/"
        client = Client()
        client.login(email="tester@email.br", password="password")
        response = client.get(admin_url)
        assert response.status_code == 302
        assert response.url == "/login/"


class TestPublicConversations(ConversationRecipes):
    @pytest.fixture
    def admin_user(self, db):
        admin_user = User.objects.create_superuser("admin@test.com", "pass")
        admin_user.save()
        return admin_user

    @pytest.fixture
    def logged_admin(self, admin_user):
        client = Client()
        client.force_login(admin_user)
        return client

    @pytest.fixture
    def promoted_conversation(self, admin_user):
        board = Board.objects.create(slug="board1", owner=admin_user, description="board")
        conversation = create_conversation("foo", "conv1", admin_user, board=board)
        conversation.is_promoted = True
        conversation.is_hidden = False
        conversation.save()
        return conversation

    @pytest.fixture
    def not_promoted_conversation(self, admin_user):
        board = Board.objects.create(slug="board2", owner=admin_user, description="board2")
        conversation = create_conversation("bar", "conv2", admin_user, board=board)
        conversation.is_promoted = False
        conversation.is_hidden = False
        conversation.save()
        return conversation

    @pytest.fixture
    def hiden_conversation(self, admin_user):
        board = Board.objects.create(slug="board3", owner=admin_user, description="board3")
        conversation = create_conversation("foobar", "conv3", admin_user, board=board)
        conversation.is_promoted = True
        conversation.is_hidden = True
        conversation.save()
        return conversation

    def test_authenticated_user_can_access_public_conversations(
        self, logged_admin, promoted_conversation, not_promoted_conversation, hiden_conversation
    ):
        url = f"/conversations/"
        response = logged_admin.get(url)

        board1 = Board.objects.get(slug="admintestcom")
        board2 = Board.objects.get(slug="board1")
        board3 = Board.objects.get(slug="board2")
        board4 = Board.objects.get(slug="board3")

        assert response.status_code == 200

        assert board1 in response.context["user_boards"]
        assert board2 in response.context["user_boards"]
        assert board3 in response.context["user_boards"]
        assert board4 in response.context["user_boards"]
        assert len(response.context["user_boards"]) == 4

        assert response.context["conversations_limit"] == 20

        assert promoted_conversation in response.context["conversations"]
        assert not_promoted_conversation not in response.context["conversations"]
        assert hiden_conversation in response.context["conversations"]

    def test_anonymous_user_can_access_public_conversations(
        self, logged_admin, promoted_conversation, not_promoted_conversation, hiden_conversation
    ):
        url = f"/conversations/"
        client = Client()
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["user_boards"] == []
        assert response.context["conversations_limit"] == 0
        assert promoted_conversation in response.context["conversations"]
        assert response.context["conversations"][0].is_hidden == True
