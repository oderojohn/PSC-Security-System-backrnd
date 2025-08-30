from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import LostItem, FoundItem, SystemSettings
from .serializers import LostItemSerializer, FoundItemSerializer, SystemSettingsSerializer
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()

class LostFoundTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_lost_item_creation(self):
        lost_item = LostItem.objects.create(
            type='item',
            item_name='Test Item',
            owner_name='Test Owner',
            place_lost='Test Place',
            reporter_email='test@example.com',
            reported_by=self.user
        )
        self.assertEqual(lost_item.item_name, 'Test Item')
        self.assertTrue(lost_item.tracking_id.startswith('LI-'))

    def test_found_item_creation(self):
        found_item = FoundItem.objects.create(
            type='item',
            item_name='Test Found Item',
            owner_name='Test Owner',
            place_found='Test Place',
            finder_name='Test Finder',
            reported_by=self.user
        )
        self.assertEqual(found_item.item_name, 'Test Found Item')

    def test_system_settings(self):
        setting = SystemSettings.set_setting('test_key', 'test_value', 'Test description')
        self.assertEqual(SystemSettings.get_setting('test_key'), 'test_value')
        self.assertEqual(setting.description, 'Test description')

class APITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)

    def test_lost_item_api(self):
        data = {
            'type': 'item',
            'item_name': 'API Test Item',
            'owner_name': 'API Test Owner',
            'place_lost': 'API Test Place',
            'reporter_email': 'api@example.com'
        }
        response = self.client.post('/lost/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tracking_id', response.data)

    def test_system_settings_api(self):
        # Test setting a value
        data = {'key': 'api_test', 'value': 'api_value', 'description': 'API Test'}
        response = self.client.post('/settings/set_setting/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test getting the value
        response = self.client.get('/settings/get_setting/?key=api_test')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['value'], 'api_value')
