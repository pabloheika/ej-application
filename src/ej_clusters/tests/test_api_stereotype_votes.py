import pytest

from django.urls import reverse
from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK, HTTP_207_MULTI_STATUS, HTTP_403_FORBIDDEN

from ej_clusters.models import Clusterization, Cluster, Stereotype, StereotypeVote
from ej_conversations.enums import Choice
from ej_conversations.tests.conftest import get_authorized_api_client
from ej_users.models import User


@pytest.fixture()
def stereotype_context(db, user, conversation, comments):
    """Constrói um estereótipo ligado a uma conversa com comentários aprovados."""
    clusterization = Clusterization.objects.create(conversation=conversation)
    cluster = Cluster.objects.create(clusterization=clusterization, name="My Cluster")
    stereotype = Stereotype.objects.create(name="Persona", owner=user)
    cluster.stereotypes.add(stereotype)

    return {
        "stereotype": stereotype,
        "conversation": conversation,
        "comments": comments,
        "user": user,
    }


def _get_api_client(email, password="password"):
    return get_authorized_api_client({"email": email, "password": password})


@pytest.fixture()
def other_user(db):
    """Usuário adicional para testar restrições de permissão."""
    user = User.objects.create_user("other@server.com", "password")
    return user


class TestStereotypeVoteAPI:
    def test_vote_form_data(self, stereotype_context):
        """Teste: retorna dados para o formulário de votação do estereótipo."""
        stereotype = stereotype_context["stereotype"]
        user = stereotype_context["user"]

        api = _get_api_client(user.email)
        path = reverse("v1-stereotypes-vote-form-data", kwargs={"pk": stereotype.id})
        response = api.get(path, format="json")

        assert response.status_code == HTTP_200_OK
        data = response.data
        assert data["stereotype_id"] == stereotype.id
        assert len(data["comments"]) == len(stereotype_context["comments"])

    def test_create_votes(self, stereotype_context):
        """Teste: cria votos para o estereótipo (POST /votes/)."""
        stereotype = stereotype_context["stereotype"]
        user = stereotype_context["user"]
        comments = stereotype_context["comments"]

        api = _get_api_client(user.email)
        path = reverse("v1-stereotypes-votes", kwargs={"pk": stereotype.id})

        payload = {
            "votes": [
                {"comment": comments[0].id, "choice": "agree"},
                {"comment": comments[1].id, "choice": "disagree"},
            ]
        }
        response = api.post(path, payload, format="json")

        assert response.status_code in (HTTP_201_CREATED, HTTP_207_MULTI_STATUS)
        assert StereotypeVote.objects.filter(author=stereotype).count() == 2

    def test_manage_votes(self, stereotype_context):
        """Teste: lista votos já registrados e comentários ainda não votados."""
        stereotype = stereotype_context["stereotype"]
        user = stereotype_context["user"]
        comments = stereotype_context["comments"]

        StereotypeVote.objects.create(
            author=stereotype, comment=comments[0], choice=Choice.AGREE
        )

        api = _get_api_client(user.email)
        path = reverse("v1-stereotypes-manage-votes", kwargs={"pk": stereotype.id})
        response = api.get(path, format="json")

        data = response.data
        assert response.status_code == HTTP_200_OK
        assert len(data["voted"]) == 1
        assert len(data["non_voted"]) == len(comments) - 1

    def test_bulk_update_votes(self, stereotype_context):
        """Teste: atualiza ou remove votos em lote (PUT /votes/bulk-update/)."""
        stereotype = stereotype_context["stereotype"]
        user = stereotype_context["user"]
        comments = stereotype_context["comments"]

        vote1 = StereotypeVote.objects.create(
            author=stereotype, comment=comments[0], choice=Choice.AGREE
        )
        vote2 = StereotypeVote.objects.create(
            author=stereotype, comment=comments[1], choice=Choice.DISAGREE
        )

        api = _get_api_client(user.email)
        path = reverse("v1-stereotypes-votes-bulk-update", kwargs={"pk": stereotype.id})

        payload = {
            "votes": [
                {"comment": comments[0].id, "choice": "skip"},
                {"comment": comments[1].id, "choice": None},
            ]
        }
        response = api.put(path, payload, format="json")

        assert response.status_code == HTTP_200_OK
        vote1.refresh_from_db()
        assert vote1.choice == Choice.SKIP
        assert not StereotypeVote.objects.filter(id=vote2.id).exists()

    def test_permission_denied(self, stereotype_context, other_user):
        """Teste: outro usuário autenticado não pode manipular o estereótipo (403)."""
        stereotype = stereotype_context["stereotype"]

        api = _get_api_client(other_user.email)
        path = reverse("v1-stereotypes-vote-form-data", kwargs={"pk": stereotype.id})
        response = api.get(path, format="json")
        assert response.status_code == HTTP_403_FORBIDDEN 