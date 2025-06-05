import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from ej_clusters.models.clusterization import Clusterization
from ej_conversations.models import Conversation

User = get_user_model()


@pytest.mark.django_db
class TestClusterizationAPI:
    
    @pytest.fixture(autouse=True)
    def setup_method(self, user, conversation, clusterization):
        self.client = APIClient()
        self.user = user
        self.other_user = User.objects.create_user(
            'other@example.com',
            'testpass123'
        )
        self.superuser = User.objects.create_superuser(
            'admin@example.com',
            'adminpass123'
        )
        self.conversation = conversation
        self.clusterization = clusterization
    
    def test_control_endpoint_force_clusterization_as_author(self):
        """Teste: autor da conversa pode forçar reprocessamento de clusterização"""
        self.client.force_authenticate(user=self.user)
        url = reverse('v1-clusterizations-control', kwargs={'pk': self.clusterization.pk})
        
        data = {'action': 'force-clusterization'}
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['action'] == 'force-clusterization'
        assert response.data['status'] == 'success'
        assert 'message' in response.data
    
    def test_control_endpoint_force_clusterization_as_superuser(self):
        """Teste: superusuário pode forçar reprocessamento de clusterização"""
        self.client.force_authenticate(user=self.superuser)
        url = reverse('v1-clusterizations-control', kwargs={'pk': self.clusterization.pk})
        
        data = {'action': 'force-clusterization'}
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['action'] == 'force-clusterization'
        assert response.data['status'] == 'success'
    
    def test_control_endpoint_check_promotion_as_author(self):
        """Teste: autor da conversa pode verificar promoção"""
        self.client.force_authenticate(user=self.user)
        url = reverse('v1-clusterizations-control', kwargs={'pk': self.clusterization.pk})
        
        data = {'action': 'check-promotion'}
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['action'] == 'check-promotion'
        assert response.data['status'] == 'success'
        assert 'is_promoted' in response.data
    
    def test_control_endpoint_permission_denied_other_user(self):
        """Teste: usuário que não é autor nem superusuário não pode acessar controle"""
        self.client.force_authenticate(user=self.other_user)
        url = reverse('v1-clusterizations-control', kwargs={'pk': self.clusterization.pk})
        
        data = {'action': 'force-clusterization'}
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'error' in response.data
        assert 'Permission denied' in response.data['error']
    
    def test_control_endpoint_unauthenticated_user(self):
        """Teste: usuário não autenticado não pode acessar controle"""
        url = reverse('v1-clusterizations-control', kwargs={'pk': self.clusterization.pk})
        
        data = {'action': 'force-clusterization'}
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_control_endpoint_missing_action(self):
        """Teste: erro quando action não é fornecida"""
        self.client.force_authenticate(user=self.user)
        url = reverse('v1-clusterizations-control', kwargs={'pk': self.clusterization.pk})
        
        response = self.client.post(url, {}, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
        assert 'Action is required' in response.data['error']
    
    def test_control_endpoint_invalid_action(self):
        """Teste: erro quando action inválida é fornecida"""
        self.client.force_authenticate(user=self.user)
        url = reverse('v1-clusterizations-control', kwargs={'pk': self.clusterization.pk})
        
        data = {'action': 'invalid-action'}
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
        assert 'Invalid action' in response.data['error']
        assert 'invalid-action' in response.data['error']
    
    def test_control_endpoint_get_method_not_allowed(self):
        """Teste: método GET não é permitido no endpoint de controle"""
        self.client.force_authenticate(user=self.user)
        url = reverse('v1-clusterizations-control', kwargs={'pk': self.clusterization.pk})
        
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    def test_control_endpoint_nonexistent_clusterization(self):
        """Teste: erro 404 para clusterização inexistente"""
        self.client.force_authenticate(user=self.user)
        url = reverse('v1-clusterizations-control', kwargs={'pk': 99999})
        
        data = {'action': 'force-clusterization'}
        response = self.client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestClusterizationViewSet:
    
    @pytest.fixture(autouse=True)
    def setup_method(self, user):
        self.client = APIClient()
        self.user = user
        self.superuser = User.objects.create_superuser(
            'admin@example.com',
            'adminpass123'
        )
        
    def test_list_clusterizations_as_superuser(self):
        """Teste: superusuário pode listar todas as clusterizações"""
        self.client.force_authenticate(user=self.superuser)
        url = reverse('v1-clusterizations-list')
        
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
    
    def test_list_clusterizations_as_regular_user(self, board):
        """Teste: usuário regular só pode listar suas próprias clusterizações"""
        # Criar uma conversa do usuário
        conversation = Conversation.objects.create(
            title='User Conversation',
            text='Description',
            author=self.user,
            board=board
        )
        clusterization = Clusterization.objects.create(conversation=conversation)
        
        self.client.force_authenticate(user=self.user)
        url = reverse('v1-clusterizations-list')
        
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        # Verificar se retorna apenas clusterizações do usuário
        if response.data:
            assert all(c['conversation'] == conversation.slug for c in response.data)
    
    def test_retrieve_clusterization_detail(self, board):
        """Teste: obter detalhes de uma clusterização específica"""
        conversation = Conversation.objects.create(
            title='Test Conversation',
            text='Description',
            author=self.user,
            board=board
        )
        clusterization = Clusterization.objects.create(conversation=conversation)
        
        self.client.force_authenticate(user=self.user)
        url = reverse('v1-clusterizations-detail', kwargs={'pk': clusterization.pk})
        
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['conversation'] == conversation.slug
        assert 'links' in response.data 