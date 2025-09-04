from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import LostItem, FoundItem, SystemSettings
from .serializers import LostItemSerializer, FoundItemSerializer, SystemSettingsSerializer
from .views import calculate_match_score, get_match_reasons
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()

class MatchingAlgorithmTestCase(TestCase):
    """Test cases for the improved matching algorithm"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_perfect_match(self):
        """Test items that should be a perfect match"""
        lost_item = LostItem.objects.create(
            type='item',
            item_name='iPhone 12 Pro Max',
            description='Black iPhone with cracked screen',
            place_lost='Tennis Court',
            owner_name='John Doe',
            reporter_email='john@example.com',
            reported_by=self.user
        )

        found_item = FoundItem.objects.create(
            type='item',
            item_name='iPhone 12 Pro Max',
            description='Black iPhone found on tennis court',
            place_found='Tennis Court',
            finder_name='Jane Smith',
            reported_by=self.user
        )

        score = calculate_match_score(lost_item, found_item)
        reasons = get_match_reasons(lost_item, found_item)

        self.assertGreater(score, 0.8, f"Perfect match should have high score, got {score}")
        self.assertIn('Similar item names', str(reasons))
        self.assertIn('Matching type', str(reasons))

    def test_partial_match(self):
        """Test items with partial information match"""
        lost_item = LostItem.objects.create(
            type='item',
            item_name='iPhone 12',
            description='',
            place_lost='Gym',
            owner_name='John Doe',
            reporter_email='john@example.com',
            reported_by=self.user
        )

        found_item = FoundItem.objects.create(
            type='item',
            item_name='iPhone 12 Pro',
            description='',
            place_found='Gym Area',
            finder_name='Jane Smith',
            reported_by=self.user
        )

        score = calculate_match_score(lost_item, found_item)
        reasons = get_match_reasons(lost_item, found_item)

        self.assertGreater(score, 0.3, f"Partial match should have reasonable score, got {score}")
        self.assertGreater(len(reasons), 1, "Should have multiple match reasons")

    def test_keyword_match(self):
        """Test keyword-based matching"""
        lost_item = LostItem.objects.create(
            type='item',
            item_name='Samsung Galaxy S21',
            description='Blue color, case damaged',
            place_lost='Parking Lot',
            owner_name='John Doe',
            reporter_email='john@example.com',
            reported_by=self.user
        )

        found_item = FoundItem.objects.create(
            type='item',
            item_name='Samsung Phone',
            description='Blue Samsung found in parking',
            place_found='Parking Area',
            finder_name='Jane Smith',
            reported_by=self.user
        )

        score = calculate_match_score(lost_item, found_item)
        reasons = get_match_reasons(lost_item, found_item)

        self.assertGreater(score, 0.4, f"Keyword match should work well, got {score}")
        self.assertIn('Common keywords', str(reasons))

    def test_color_match(self):
        """Test color-based matching in descriptions"""
        lost_item = LostItem.objects.create(
            type='item',
            item_name='Wallet',
            description='Black leather wallet with cards',
            place_lost='Restaurant',
            owner_name='John Doe',
            reporter_email='john@example.com',
            reported_by=self.user
        )

        found_item = FoundItem.objects.create(
            type='item',
            item_name='Leather Wallet',
            description='Black wallet found at restaurant',
            place_found='Restaurant Area',
            finder_name='Jane Smith',
            reported_by=self.user
        )

        score = calculate_match_score(lost_item, found_item)
        reasons = get_match_reasons(lost_item, found_item)

        self.assertGreater(score, 0.3, f"Color match should work, got {score}")
        self.assertIn('Matching colors', str(reasons))

    def test_time_decay(self):
        """Test that time difference affects scoring"""
        base_time = timezone.now()

        lost_item = LostItem.objects.create(
            type='item',
            item_name='Watch',
            description='Silver watch',
            place_lost='Lobby',
            owner_name='John Doe',
            reporter_email='john@example.com',
            reported_by=self.user,
            date_reported=base_time
        )

        # Same day - high score
        found_item_same_day = FoundItem.objects.create(
            type='item',
            item_name='Watch',
            description='Silver watch',
            place_found='Lobby',
            finder_name='Jane Smith',
            reported_by=self.user,
            date_reported=base_time + timedelta(hours=2)
        )

        # Week later - lower score
        found_item_week_later = FoundItem.objects.create(
            type='item',
            item_name='Watch',
            description='Silver watch',
            place_found='Lobby',
            finder_name='Jane Smith',
            reported_by=self.user,
            date_reported=base_time + timedelta(days=7)
        )

        score_same_day = calculate_match_score(lost_item, found_item_same_day)
        score_week_later = calculate_match_score(lost_item, found_item_week_later)

        self.assertGreater(score_same_day, score_week_later,
                          "Same day match should score higher than week later match")

    def test_different_types_no_match(self):
        """Test that different item types don't match"""
        lost_item = LostItem.objects.create(
            type='card',
            card_last_four='A1234',
            owner_name='John Doe',
            reporter_email='john@example.com',
            reported_by=self.user
        )

        found_item = FoundItem.objects.create(
            type='item',
            item_name='Access Card',
            finder_name='Jane Smith',
            reported_by=self.user
        )

        score = calculate_match_score(lost_item, found_item)
        self.assertEqual(score, 0.0, "Different types should not match")

    def test_card_exact_match(self):
        """Test exact card number matching"""
        lost_item = LostItem.objects.create(
            type='card',
            card_last_four='K123D',
            owner_name='John Doe',
            reporter_email='john@example.com',
            reported_by=self.user
        )

        found_item = FoundItem.objects.create(
            type='card',
            card_last_four='K123D',
            finder_name='Jane Smith',
            reported_by=self.user
        )

        score = calculate_match_score(lost_item, found_item)
        reasons = get_match_reasons(lost_item, found_item)

        self.assertGreater(score, 0.8, f"Exact card match should have high score, got {score}")
        self.assertIn('Exact card number match', str(reasons))

    def test_card_different_numbers_no_match(self):
        """Test that different card numbers don't match"""
        lost_item = LostItem.objects.create(
            type='card',
            card_last_four='K123D',
            owner_name='John Doe',
            reporter_email='john@example.com',
            reported_by=self.user
        )

        found_item = FoundItem.objects.create(
            type='card',
            card_last_four='0000',
            finder_name='Jane Smith',
            reported_by=self.user
        )

        score = calculate_match_score(lost_item, found_item)
        reasons = get_match_reasons(lost_item, found_item)

        self.assertLess(score, 0.3, f"Different card numbers should have low score, got {score}")
        self.assertIn('Different card numbers', str(reasons))

    def test_card_partial_match(self):
        """Test partial card number similarity"""
        lost_item = LostItem.objects.create(
            type='card',
            card_last_four='K123D',
            owner_name='John Doe',
            reporter_email='john@example.com',
            reported_by=self.user
        )

        found_item = FoundItem.objects.create(
            type='card',
            card_last_four='K123E',  # Very similar
            finder_name='Jane Smith',
            reported_by=self.user
        )

        score = calculate_match_score(lost_item, found_item)
        reasons = get_match_reasons(lost_item, found_item)

        self.assertGreater(score, 0.4, f"Similar card numbers should match reasonably, got {score}")
        self.assertIn('Similar card numbers', str(reasons))

    def test_missing_data_handling(self):
        """Test handling of missing or empty data"""
        lost_item = LostItem.objects.create(
            type='item',
            item_name='',  # Empty name
            description=None,  # None description
            place_lost='Pool',
            owner_name='John Doe',
            reporter_email='john@example.com',
            reported_by=self.user
        )

        found_item = FoundItem.objects.create(
            type='item',
            item_name='Swim Goggles',  # Has name
            description='',  # Empty description
            place_found='Pool Area',
            finder_name='Jane Smith',
            reported_by=self.user
        )

        score = calculate_match_score(lost_item, found_item)
        reasons = get_match_reasons(lost_item, found_item)

        # Should still get some score from location and type
        self.assertGreater(score, 0.1, f"Should handle missing data gracefully, got {score}")
        self.assertGreater(len(reasons), 0, "Should still provide reasons even with missing data")


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
