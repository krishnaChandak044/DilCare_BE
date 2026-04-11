"""
Medicine Inventory — End-to-end tests covering:
  1. Creating a medicine with current_quantity (inventory fields appear in response)
  2. Inventory end_date and days_until_empty computed correctly
  3. Quantity decrements when intake is toggled 'taken'
  4. Running-out endpoint returns correct medicines
  5. Family members get in-app notification when medicine runs low
"""
from datetime import date, timedelta
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from accounts.models import User, Notification
from family.models import Family, FamilyMembership
from medicine.models import Medicine, MedicineIntake


class MedicineInventoryTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="patient@test.com", password="pass1234", first_name="Riya"
        )
        self.client.force_authenticate(user=self.user)

    # ------------------------------------------------------------------
    # 1. Create medicine with inventory
    # ------------------------------------------------------------------
    def test_create_medicine_with_quantity(self):
        url = reverse("medicine:medicine-list-create")
        payload = {
            "name": "Paracetamol",
            "dosage": "500mg",
            "schedule_times": "08:00",
            "current_quantity": 4,
        }
        resp = self.client.post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        data = resp.json()
        self.assertEqual(data["current_quantity"], 4)
        self.assertIn("inventory_end_date", data)
        self.assertIn("days_until_empty", data)
        self.assertIn("is_running_low", data)

    # ------------------------------------------------------------------
    # 2. Inventory deadline computed correctly
    #    4 tablets, 1/day → runs out in 4 days
    # ------------------------------------------------------------------
    def test_inventory_end_date_computation(self):
        med = Medicine.objects.create(
            user=self.user,
            name="Aspirin",
            dosage="100mg",
            schedule_times="08:00",
            current_quantity=4,
            doses_per_day=1,
        )
        expected_end = date.today() + timedelta(days=4)
        self.assertEqual(med.inventory_end_date, expected_end)
        self.assertEqual(med.days_until_empty, 4)
        self.assertFalse(med.is_running_low)

    # ------------------------------------------------------------------
    # 3. is_running_low triggers when ≤2 days left
    # ------------------------------------------------------------------
    def test_is_running_low_when_two_days_left(self):
        med = Medicine.objects.create(
            user=self.user,
            name="Metformin",
            dosage="500mg",
            schedule_times="08:00",
            current_quantity=2,
            doses_per_day=1,
        )
        self.assertEqual(med.days_until_empty, 2)
        self.assertTrue(med.is_running_low)

    # ------------------------------------------------------------------
    # 4. PATCH inventory endpoint updates quantity
    # ------------------------------------------------------------------
    def test_patch_inventory_endpoint(self):
        med = Medicine.objects.create(
            user=self.user,
            name="Vitamin C",
            dosage="1000mg",
            schedule_times="09:00",
            current_quantity=10,
        )
        url = reverse("medicine:medicine-inventory-update", kwargs={"pk": med.pk})
        resp = self.client.patch(url, {"current_quantity": 2}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        med.refresh_from_db()
        self.assertEqual(med.current_quantity, 2)

    # ------------------------------------------------------------------
    # 5. Running-out endpoint returns only running-low medicines
    # ------------------------------------------------------------------
    def test_running_out_endpoint(self):
        # Low medicine (2 days)
        Medicine.objects.create(
            user=self.user, name="PillA", dosage="10mg",
            schedule_times="08:00", current_quantity=2, doses_per_day=1,
        )
        # Safe medicine (20 days)
        Medicine.objects.create(
            user=self.user, name="PillB", dosage="20mg",
            schedule_times="08:00", current_quantity=20, doses_per_day=1,
        )
        url = reverse("medicine:running-out")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["running_low"][0]["name"], "PillA")

    # ------------------------------------------------------------------
    # 6. Toggling intake 'taken' decrements quantity
    # ------------------------------------------------------------------
    def test_toggle_taken_decrements_quantity(self):
        from django.utils import timezone as tz
        med = Medicine.objects.create(
            user=self.user, name="Panadol", dosage="500mg",
            schedule_times="08:00", current_quantity=5, doses_per_day=1,
        )
        intake = MedicineIntake.objects.create(
            medicine=med,
            scheduled_date=date.today(),
            scheduled_time=__import__("datetime").time(8, 0),
            status="pending",
        )
        url = reverse("medicine:intake-toggle", kwargs={"intake_id": intake.pk})
        resp = self.client.post(url, {"status": "taken"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        med.refresh_from_db()
        self.assertEqual(med.current_quantity, 4)

    # ------------------------------------------------------------------
    # 7. Family members get notified when medicine runs low
    # ------------------------------------------------------------------
    def test_family_notification_sent_when_running_low(self):
        # Create a family with two members
        family = Family.objects.create(name="Test Family", created_by=self.user)
        FamilyMembership.objects.create(family=family, user=self.user, role="admin")
        spouse = User.objects.create_user(email="spouse@test.com", password="pass1234", first_name="Raj")
        FamilyMembership.objects.create(family=family, user=spouse, role="member")

        # PATCH inventory to 1 (running low) via the view helper directly
        med = Medicine.objects.create(
            user=self.user, name="Insulin", dosage="10U",
            schedule_times="08:00", current_quantity=5, doses_per_day=1,
        )
        url = reverse("medicine:medicine-inventory-update", kwargs={"pk": med.pk})
        resp = self.client.patch(url, {"current_quantity": 1}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Spouse should have received a notification
        notif = Notification.objects.filter(user=spouse, notification_type="medication_reminder").first()
        self.assertIsNotNone(notif)
        self.assertIn("Insulin", notif.title)
        self.assertIn("Riya", notif.body)

    # ------------------------------------------------------------------
    # 8. Today's schedule includes inventory fields
    # ------------------------------------------------------------------
    def test_today_schedule_includes_inventory(self):
        Medicine.objects.create(
            user=self.user, name="D3", dosage="2000IU",
            schedule_times="07:00", current_quantity=7, doses_per_day=1,
        )
        url = reverse("medicine:today-medicines")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        items = resp.json()
        self.assertGreater(len(items), 0)
        item = items[0]
        self.assertIn("current_quantity", item)
        self.assertIn("is_running_low", item)
        self.assertIn("inventory_end_date", item)
