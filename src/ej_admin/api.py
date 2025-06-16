from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated, BasePermission
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required
from ej_boards.serializers import BoardSerializer
from .utils import apply_board_filters, NUM_ENTRIES_DEFAULT, PAGINATOR_START_PAGE
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

class SearchedBoardsPagination(PageNumberPagination):
    page_size_query_param = 'numEntries'
    page_query_param = 'page'
    max_page_size = 100
    page_size = NUM_ENTRIES_DEFAULT

@extend_schema(
    summary="Busca boards com filtros, ordenação e paginação",
    description="Endpoint para buscar boards com suporte a filtros por string, ordenação, paginação e proteção por permissão.",
    parameters=[
        OpenApiParameter(name="searchString", description="Texto para busca", required=False, type=str),
        OpenApiParameter(name="orderBy", description="Campo de ordenação (date, conversations-count, comments-count)", required=False, type=str),
        OpenApiParameter(name="sort", description="Ordem (asc ou desc)", required=False, type=str),
        OpenApiParameter(name="page", description="Número da página", required=False, type=int),
        OpenApiParameter(name="numEntries", description="Itens por página", required=False, type=int),
    ],
    responses={200: OpenApiResponse(response=BoardSerializer(many=True), description="Resposta paginada de boards")}
)
@method_decorator(permission_required('ej.can_access_environment_management'), name='dispatch')
class SearchedBoardsAPIView(APIView):
    def get(self, request):
        search_string = request.GET.get('searchString', '')
        order_by = request.GET.get('orderBy', 'date')
        sort = request.GET.get('sort', 'desc')
        page = request.GET.get('page', PAGINATOR_START_PAGE)
        num_entries = request.GET.get('numEntries', NUM_ENTRIES_DEFAULT)

        boards_qs = apply_board_filters(order_by, sort, search_string)
        paginator = SearchedBoardsPagination()
        paginator.page_size = num_entries
        result_page = paginator.paginate_queryset(boards_qs, request)
        serializer = BoardSerializer(result_page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

class CanAccessEnvironmentManagementPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_perm('ej.can_access_environment_management')

class FavoriteBoardsAPIView(APIView):
    """
    GET /api/admin/environment/favorite-boards/
    Lista os boards favoritos do usuário autenticado.
    Protegido por permissão 'ej.can_access_environment_management'.
    """
    permission_classes = [CanAccessEnvironmentManagementPermission]

    def get(self, request):
        user = request.user
        favorite_boards = user.favorite_boards.order_by('-created')
        serializer = BoardSerializer(favorite_boards, many=True, context={"request": request})
        return Response(serializer.data)
