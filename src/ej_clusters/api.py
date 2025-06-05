from ej_clusters.models.clusterization import Clusterization
from ej_conversations.models import Conversation
from ej_conversations.utils import check_promoted
from sidekick import import_later
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from ej.viewsets import RestAPIBaseViewSet
from .utils import cluster_shapes
from ej_clusters.serializers import (
    ClusterizationSerializer,
    ClusterSerializer,
    StereotypeSerializer,
)
from ej.permissions import IsOwner, IsSuperUser
from rest_framework.permissions import IsAdminUser

math = import_later(".math", package=__package__)


class ClusterizationViewSet(RestAPIBaseViewSet):
    queryset = Clusterization.objects.all()
    serializer_class = ClusterizationSerializer
    permission_classes = [IsOwner, IsSuperUser, IsAdminUser]

    def get_permissions(self):
        """
        Instancia e retorna a lista de permissões que esta view precisa.
        Para os métodos list e retrieve, permite usuários autenticados.
        Para outros métodos, usa as permissões padrão.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = self.permission_classes
        return [permission() for permission in permission_classes]

    def list(self, request):
        if request.user.is_superuser:
            queryset = Clusterization.objects.all()
        else:
            conversation = Conversation.objects.filter(author=request.user)
            queryset = Clusterization.objects.filter(conversation__in=conversation)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """
        Recupera uma clusterização específica.
        Permite acesso se o usuário for superusuário ou autor da conversa.
        """
        clusterization = self.get_object()
        user = request.user
        
        if not (user.is_superuser or user.id == clusterization.conversation.author_id):
            return Response(
                {"error": "Permission denied. You must be the conversation author or a superuser."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(clusterization)
        return Response(serializer.data)

    @action(detail=True)
    def clusters(self, request, pk):
        clusterization = self.get_object()
        clusters = clusterization.clusters.all()
        serializer = ClusterSerializer(clusters, context={"request": request}, many=True)
        return Response(serializer.data)

    @action(detail=True)
    def affinities(self, request, pk):
        clusterization = self.get_object()
        shapes = cluster_shapes(clusterization, user=request.user)
        return Response(shapes)

    @action(detail=True)
    def stereotypes(self, request, pk):
        clusterization = self.get_object()
        serializer = StereotypeSerializer(
            clusterization.stereotypes.all(), context={"request": request}, many=True
        )
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def control(self, request, pk):
        """
        Endpoint de controle de clusterização para executar ações administrativas.
        
        Aceita as seguintes ações:
        - force-clusterization: Força reprocessamento da clusterização
        - check-promotion: Verifica promoção da conversa
        """
        clusterization = self.get_object()
        conversation = clusterization.conversation
        user = request.user
        
        if not (user.is_superuser or user.id == conversation.author_id):
            return Response(
                {"error": "Permission denied. You must be the conversation author or a superuser."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        action_name = request.data.get('action')
        if not action_name:
            return Response(
                {"error": "Action is required. Supported actions: 'force-clusterization', 'check-promotion'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            if action_name == 'force-clusterization':
                clusterization.update_clusterization(force=True)
                return Response({
                    "message": "Clusterization reprocessing completed successfully",
                    "action": action_name,
                    "status": "success"
                })
            
            elif action_name == 'check-promotion':
                check_promoted(conversation, request)
                return Response({
                    "message": "Promotion check completed successfully",
                    "action": action_name,
                    "status": "success",
                    "is_promoted": conversation.is_promoted
                })
            
            else:
                return Response(
                    {"error": f"Invalid action '{action_name}'. Supported actions: 'force-clusterization', 'check-promotion'"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            return Response(
                {"error": f"Failed to execute action '{action_name}': {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
