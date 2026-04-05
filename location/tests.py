from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from family.models import FamilyLink

from .models import FamilyLocationPermission, LocationShareSetting, UserLocationPing

User = get_user_model()


class LocationSharingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.parent = User.objects.create_user(email="parent@dilcare.com", password="Pass123!")
        self.child = User.objects.create_user(email="child@dilcare.com", password="Pass123!")
        self.other = User.objects.create_user(email="other@dilcare.com", password="Pass123!")

        self.link = FamilyLink.objects.create(
            child=self.child,
            parent=self.parent,
            relationship="father",
            is_active=True,
        )

    def test_upload_ping_success(self):
        self.client.force_authenticate(user=self.parent)
        response = self.client.post(
            "/api/v1/location/pings/",
            {
                "latitude": "19.076090",
                "longitude": "72.877426",
                "source": "gps",
                "recorded_at": timezone.now().isoformat(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserLocationPing.objects.filter(user=self.parent).count(), 1)

    def test_child_can_see_live_location_when_allowed(self):
        UserLocationPing.objects.create(
            user=self.parent,
            latitude="19.076090",
            longitude="72.877426",
            source="gps",
            recorded_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.child)
        response = self.client.get("/api/v1/location/family/live/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["parent_id"], self.parent.id)

    def test_child_cannot_see_live_if_permission_disabled(self):
        permission = FamilyLocationPermission.objects.create(
            family_link=self.link,
            can_view_live=False,
        )
        self.assertFalse(permission.can_view_live)

        UserLocationPing.objects.create(
            user=self.parent,
            latitude="19.076090",
            longitude="72.877426",
            source="gps",
            recorded_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.child)
        response = self.client.get("/api/v1/location/family/live/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_history_denied_when_parent_sharing_disabled(self):
        LocationShareSetting.objects.create(user=self.parent, sharing_enabled=False)
        UserLocationPing.objects.create(
            user=self.parent,
            latitude="19.076090",
            longitude="72.877426",
            source="gps",
            recorded_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.child)
        response = self.client.get(f"/api/v1/location/family/{self.parent.id}/history/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_parent_can_update_own_permission(self):
        permission = FamilyLocationPermission.objects.create(family_link=self.link)

        self.client.force_authenticate(user=self.parent)
        response = self.client.patch(
            f"/api/v1/location/permissions/{permission.id}/",
            {"history_window_hours": 12, "precision_mode": "approximate"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        permission.refresh_from_db()
        self.assertEqual(permission.history_window_hours, 12)
        self.assertEqual(permission.precision_mode, "approximate")

    def test_non_parent_cannot_update_permission(self):
        permission = FamilyLocationPermission.objects.create(family_link=self.link)

        self.client.force_authenticate(user=self.other)
        response = self.client.patch(
            f"/api/v1/location/permissions/{permission.id}/",
            {"history_window_hours": 12},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
