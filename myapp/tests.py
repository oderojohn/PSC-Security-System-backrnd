from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Package


class PackagePickTestCase(APITestCase):
    def setUp(self):
        # Create a test package
        self.package = Package.objects.create(
            type=Package.PACKAGE,
            description="Test package",
            recipient_name="John Doe",
            recipient_phone="1234567890",
            dropped_by="Jane Smith",
            status=Package.PENDING
        )

    def test_pick_package_with_picker_name_and_id(self):
        """Test picking a package with picked_by and picker_id (user's example)"""
        url = reverse('package-pick', kwargs={'pk': self.package.pk})
        data = {
            "picked_by": "Bob Johnson",
            "picker_id": "678901"
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.package.refresh_from_db()
        self.assertEqual(self.package.status, Package.PICKED)
        self.assertEqual(self.package.picked_by, "Bob Johnson")
        self.assertEqual(self.package.picker_id, "678901")
        self.assertIsNotNone(self.package.picked_at)

    def test_pick_package_with_picker_phone(self):
        """Test picking a package with picker_phone"""
        url = reverse('package-pick', kwargs={'pk': self.package.pk})
        data = {
            "picker_phone": "0987654321"
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.package.refresh_from_db()
        self.assertEqual(self.package.status, Package.PICKED)
        self.assertEqual(self.package.picker_phone, "0987654321")

    def test_pick_package_validation_no_fields(self):
        """Test that picking fails when no fields are provided"""
        url = reverse('package-pick', kwargs={'pk': self.package.pk})
        data = {}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('At least one field', str(response.data))

    def test_pick_package_already_picked(self):
        """Test that picking an already picked package fails"""
        # First pick the package
        self.package.status = Package.PICKED
        self.package.save()

        url = reverse('package-pick', kwargs={'pk': self.package.pk})
        data = {
            "picked_by": "Bob Johnson",
            "picker_id": "678901"
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already picked', str(response.data))
