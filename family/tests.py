"""
Family — Tests for family group endpoints.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from .models import Family, FamilyMembership

User = get_user_model()


class CreateFamilyTests(TestCase):
    """Test POST /api/v1/family/create/"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="admin@family.com", password="Pass123!")
        self.client.force_authenticate(user=self.user)

    def test_create_family(self):
        resp = self.client.post("/api/v1/family/create/", {"name": "Sharma Family"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["name"], "Sharma Family")
        self.assertEqual(resp.data["member_count"], 1)
        self.assertEqual(len(resp.data["invite_code"]), 6)
        # Creator should be admin
        membership = FamilyMembership.objects.get(user=self.user)
        self.assertEqual(membership.role, "admin")

    def test_cannot_create_if_already_in_family(self):
        self.client.post("/api/v1/family/create/", {"name": "First"}, format="json")
        resp = self.client.post("/api/v1/family/create/", {"name": "Second"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class JoinFamilyTests(TestCase):
    """Test POST /api/v1/family/join/"""

    def setUp(self):
        self.admin_user = User.objects.create_user(email="admin@family.com", password="Pass123!")
        self.member_user = User.objects.create_user(email="member@family.com", password="Pass123!")

        # Create family via admin
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin_user)
        resp = self.admin_client.post("/api/v1/family/create/", {"name": "Test Family"}, format="json")
        self.invite_code = resp.data["invite_code"]

        self.member_client = APIClient()
        self.member_client.force_authenticate(user=self.member_user)

    def test_join_with_valid_code(self):
        resp = self.member_client.post("/api/v1/family/join/", {
            "invite_code": self.invite_code,
            "nickname": "Beta",
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["member_count"], 2)

    def test_join_with_invalid_code(self):
        resp = self.member_client.post("/api/v1/family/join/", {
            "invite_code": "ZZZZZZ",
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_join_twice(self):
        self.member_client.post("/api/v1/family/join/", {"invite_code": self.invite_code}, format="json")
        resp = self.member_client.post("/api/v1/family/join/", {"invite_code": self.invite_code}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_max_members_limit(self):
        """Family can have at most 5 members."""
        for i in range(4):
            u = User.objects.create_user(email=f"user{i}@family.com", password="Pass123!")
            c = APIClient()
            c.force_authenticate(user=u)
            c.post("/api/v1/family/join/", {"invite_code": self.invite_code}, format="json")

        # 6th member should be rejected (admin + 4 joined = 5, one more = 6)
        extra = User.objects.create_user(email="extra@family.com", password="Pass123!")
        extra_client = APIClient()
        extra_client.force_authenticate(user=extra)
        resp = extra_client.post("/api/v1/family/join/", {"invite_code": self.invite_code}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("maximum", resp.data["error"])


class MyFamilyTests(TestCase):
    """Test GET /api/v1/family/"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="test@family.com", password="Pass123!")
        self.client.force_authenticate(user=self.user)

    def test_no_family(self):
        resp = self.client.get("/api/v1/family/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(resp.data["has_family"])

    def test_with_family(self):
        self.client.post("/api/v1/family/create/", {"name": "My Family"}, format="json")
        resp = self.client.get("/api/v1/family/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["has_family"])
        self.assertEqual(resp.data["my_role"], "admin")
        self.assertEqual(len(resp.data["members"]), 1)


class LeaveFamilyTests(TestCase):
    """Test POST /api/v1/family/leave/"""

    def setUp(self):
        self.admin = User.objects.create_user(email="admin@family.com", password="Pass123!")
        self.member = User.objects.create_user(email="member@family.com", password="Pass123!")

        admin_client = APIClient()
        admin_client.force_authenticate(user=self.admin)
        resp = admin_client.post("/api/v1/family/create/", {"name": "Test"}, format="json")
        code = resp.data["invite_code"]

        member_client = APIClient()
        member_client.force_authenticate(user=self.member)
        member_client.post("/api/v1/family/join/", {"invite_code": code}, format="json")

        self.admin_client = admin_client
        self.member_client = member_client

    def test_member_can_leave(self):
        resp = self.member_client.post("/api/v1/family/leave/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(FamilyMembership.objects.filter(user=self.member).exists())

    def test_admin_leave_transfers_admin(self):
        """When admin leaves, oldest remaining member becomes admin."""
        self.admin_client.post("/api/v1/family/leave/")
        membership = FamilyMembership.objects.get(user=self.member)
        self.assertEqual(membership.role, "admin")


class RemoveMemberTests(TestCase):
    """Test POST /api/v1/family/remove/<member_id>/"""

    def setUp(self):
        self.admin = User.objects.create_user(email="admin@family.com", password="Pass123!")
        self.member = User.objects.create_user(email="member@family.com", password="Pass123!")

        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin)
        resp = self.admin_client.post("/api/v1/family/create/", {"name": "Test"}, format="json")
        code = resp.data["invite_code"]

        self.member_client = APIClient()
        self.member_client.force_authenticate(user=self.member)
        self.member_client.post("/api/v1/family/join/", {"invite_code": code}, format="json")

    def test_admin_can_remove_member(self):
        resp = self.admin_client.post(f"/api/v1/family/remove/{self.member.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(FamilyMembership.objects.filter(user=self.member).exists())

    def test_member_cannot_remove(self):
        resp = self.member_client.post(f"/api/v1/family/remove/{self.admin.id}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cannot_remove_self(self):
        resp = self.admin_client.post(f"/api/v1/family/remove/{self.admin.id}/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class FamilyMemberHealthTests(TestCase):
    """Test GET /api/v1/family/members/<member_id>/health/"""

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@family.com", password="Pass123!",
            first_name="Papa", last_name="Sharma",
        )
        self.member = User.objects.create_user(
            email="member@family.com", password="Pass123!",
            first_name="Beta", last_name="Sharma",
        )

        admin_client = APIClient()
        admin_client.force_authenticate(user=self.admin)
        resp = admin_client.post("/api/v1/family/create/", {"name": "Sharma"}, format="json")
        code = resp.data["invite_code"]

        self.member_client = APIClient()
        self.member_client.force_authenticate(user=self.member)
        self.member_client.post("/api/v1/family/join/", {"invite_code": code}, format="json")

    def test_can_view_family_member_health(self):
        resp = self.member_client.get(f"/api/v1/family/members/{self.admin.id}/health/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["member_name"], "Papa Sharma")
        self.assertEqual(resp.data["overall_status"], "good")

    def test_cannot_view_non_family_member(self):
        outsider = User.objects.create_user(email="outsider@test.com", password="Pass123!")
        resp = self.member_client.get(f"/api/v1/family/members/{outsider.id}/health/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
