"""
Accounts — Unit tests for auth and profile endpoints.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class AuthTests(TestCase):
    """Test registration and login endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.register_url = "/api/v1/auth/register/"
        self.login_url = "/api/v1/auth/login/"

    def test_register_success(self):
        """A new user can register with email + password."""
        data = {
            "email": "test@dilcare.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "name": "Test User",
        }
        resp = self.client.post(self.register_url, data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("tokens", resp.data)
        self.assertIn("access", resp.data["tokens"])
        self.assertIn("refresh", resp.data["tokens"])
        self.assertEqual(resp.data["user"]["email"], "test@dilcare.com")

    def test_register_duplicate_email(self):
        """Cannot register with an already-used email."""
        User.objects.create_user(email="taken@dilcare.com", password="Pass123!")
        data = {
            "email": "taken@dilcare.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }
        resp = self.client.post(self.register_url, data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_mismatch(self):
        """Password and confirm must match."""
        data = {
            "email": "new@dilcare.com",
            "password": "StrongPass123!",
            "password_confirm": "WrongPass123!",
        }
        resp = self.client.post(self.register_url, data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        """A registered user can obtain JWT tokens."""
        User.objects.create_user(email="user@dilcare.com", password="Pass123!")
        data = {"email": "user@dilcare.com", "password": "Pass123!"}
        resp = self.client.post(self.login_url, data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_login_wrong_password(self):
        """Login with wrong password is rejected."""
        User.objects.create_user(email="user@dilcare.com", password="Pass123!")
        data = {"email": "user@dilcare.com", "password": "WrongPass!"}
        resp = self.client.post(self.login_url, data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class ProfileTests(TestCase):
    """Test profile CRUD endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="profile@dilcare.com",
            password="Pass123!",
            first_name="Test",
            last_name="User",
        )
        self.client.force_authenticate(user=self.user)
        self.profile_url = "/api/v1/user/profile/"

    def test_get_profile(self):
        """Authenticated user can read their profile."""
        resp = self.client.get(self.profile_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["email"], "profile@dilcare.com")
        self.assertEqual(resp.data["name"], "Test User")

    def test_update_profile(self):
        """Authenticated user can update their profile."""
        data = {"phone": "+91 9876543210", "blood_group": "O+", "age": "55"}
        resp = self.client.patch(self.profile_url, data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, "+91 9876543210")
        self.assertEqual(self.user.blood_group, "O+")
        self.assertEqual(self.user.age, "55")

    def test_update_name(self):
        """Profile update can include a name field that splits into first/last."""
        data = {"name": "Ravi Kumar"}
        resp = self.client.put(self.profile_url, data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Ravi")
        self.assertEqual(self.user.last_name, "Kumar")

    def test_profile_unauthenticated(self):
        """Unauthenticated requests are rejected."""
        self.client.force_authenticate(user=None)
        resp = self.client.get(self.profile_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class LinkCodeTests(TestCase):
    """Test family link code endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="link@dilcare.com", password="Pass123!")
        self.client.force_authenticate(user=self.user)

    def test_get_link_code(self):
        """User can retrieve their link code."""
        resp = self.client.get("/api/v1/user/link-code/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["parent_link_code"]), 6)

    def test_regenerate_link_code(self):
        """User can regenerate their link code."""
        old_code = self.user.parent_link_code
        resp = self.client.post("/api/v1/user/link-code/regenerate/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertNotEqual(resp.data["parent_link_code"], old_code)
        self.assertEqual(len(resp.data["parent_link_code"]), 6)

    def test_link_code_unique_per_user(self):
        """Each user gets a unique link code."""
        user2 = User.objects.create_user(email="link2@dilcare.com", password="Pass123!")
        self.assertNotEqual(self.user.parent_link_code, user2.parent_link_code)
