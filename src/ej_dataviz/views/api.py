# src/ej_dataviz/views/api.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from ej_conversations.models import Conversation
from ej_dataviz.serializers import ClusterSerializer
from ej_clusters.models.cluster import Cluster
from ej.decorators import can_access_dataviz

@api_view(["GET"])
@can_access_dataviz
def api_list_clusters(request, conversation_id, slug=None):
    """
    GET /api/v1/dataviz/conversations/{conversation_id}/{slug}/clusters/
    Retorna todos os Clusters associados à Conversation de ID=conversation_id.
    """
    # 1) Verificar que a Conversation existe
    try:
        conversation = Conversation.objects.get(id=conversation_id)
    except Conversation.DoesNotExist:
        return Response(
            {"detail": "Conversation não encontrada."},
            status=status.HTTP_404_NOT_FOUND
        )

    # 2) Filtrar todos os Cluster dessa conversa
    # No modelo Cluster, existe 'conversation = delegate_to("clusterization")',
    # então podemos fazer:
    clusters_qs = Cluster.objects.filter(conversation=conversation)

    # 3) Serializar a lista e devolver
    serializer = ClusterSerializer(clusters_qs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
