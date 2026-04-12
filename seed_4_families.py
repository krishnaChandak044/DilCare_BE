import os
import sys
import django
import random
from datetime import date, timedelta
from decimal import Decimal

# ── Django setup ─────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DJANGO_DIR = os.path.join(BASE_DIR, 'DilCare_BE') # script is in DilCare_BE
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# ── Imports (after django.setup) ─────────────────────────────────────────────
from django.contrib.auth import get_user_model
from django.utils import timezone
from family.models import Family, FamilyMembership
from medicine.models import Medicine, MedicineIntake
from accounts.models import Notification
from location.models import UserLocationPing

User = get_user_model()

SEED_PASSWORD = 'Seed@1234'
TODAY = timezone.localdate()
NOW = timezone.now()

FAMILIES = [
    {
        "name": "Rathi Family",
        "members": [
            {"name": "Shrutika Rathi", "email": "shrutika@rathi.com", "role": "admin", "nickname": "Daughter", "lat": 18.5204, "lon": 73.8567},
            {"name": "Rutuja Rathi", "email": "rutuja@rathi.com", "role": "member", "nickname": "Daughter", "lat": 18.5204, "lon": 73.8567},
            {"name": "Jaykumar Rathi", "email": "jaykumar@rathi.com", "role": "member", "nickname": "Father", "lat": 19.3586, "lon": 75.2199},
            {"name": "Sangita Rathi", "email": "sangita@rathi.com", "role": "member", "nickname": "Mother", "lat": 19.3411, "lon": 75.2133},
        ]
    },
    {
        "name": "Maheshwari Family",
        "members": [
            {"name": "Ritu Maheshwari", "email": "ritu@maheshwari.com", "role": "admin", "nickname": "Daughter"},
            {"name": "Ajay Maheshwari", "email": "ajay@maheshwari.com", "role": "member", "nickname": "Father"},
            {"name": "Asha Maheshwari", "email": "asha@maheshwari.com", "role": "member", "nickname": "Mother"},
            {"name": "Rohan Maheshwari", "email": "rohan@maheshwari.com", "role": "member", "nickname": "Son"},
        ]
    },
    {
        "name": "Sharma Family",
        "members": [
            {"name": "Priya Sharma", "email": "priya@sharma.com", "role": "admin", "nickname": "Daughter"},
            {"name": "Rajesh Sharma", "email": "rajesh@sharma.com", "role": "member", "nickname": "Father"},
            {"name": "Kavita Sharma", "email": "kavita@sharma.com", "role": "member", "nickname": "Mother"},
            {"name": "Kunal Sharma", "email": "kunal@sharma.com", "role": "member", "nickname": "Son"},
        ]
    },
    {
        "name": "Verma Family",
        "members": [
            {"name": "Anjali Verma", "email": "anjali@verma.com", "role": "admin", "nickname": "Daughter"},
            {"name": "Rakesh Verma", "email": "rakesh@verma.com", "role": "member", "nickname": "Father"},
            {"name": "Sunita Verma", "email": "sunita@verma.com", "role": "member", "nickname": "Mother"},
            {"name": "Siddharth Verma", "email": "siddharth@verma.com", "role": "member", "nickname": "Son"},
        ]
    }
]

def seed_families():
    print('🌱 Seeding 4 Families...')
    print('─' * 40)
    
    credentials = []

    for fam_data in FAMILIES:
        # 1. Create family
        family, created = Family.objects.get_or_create(
            name=fam_data["name"],
            defaults={"plan": "free", "max_members": 4}
        )
        print(f"\n〔 {family.name} 〕")
        
        admin_user = None
        mother_user = None
        father_user = None

        # 2. Add users
        for mem in fam_data["members"]:
            first, *last_parts = mem["name"].split()
            last = " ".join(last_parts)
            
            user, created_user = User.objects.get_or_create(
                email=mem["email"],
                defaults={'first_name': first, 'last_name': last, 'is_active': True}
            )
            if created_user:
                user.set_password(SEED_PASSWORD)
                user.save()
            
            # Record users for specific data injections later
            if mem["role"] == "admin":
                admin_user = user
                family.created_by = user
                family.save()
            if mem["nickname"] == "Mother":
                mother_user = user
            if mem["nickname"] == "Father":
                father_user = user
                
            # Family Membership
            FamilyMembership.objects.get_or_create(
                family=family,
                user=user,
                defaults={
                    "role": mem["role"],
                    "nickname": mem["nickname"]
                }
            )
            
            # Seed Location Ping if present
            if "lat" in mem and "lon" in mem:
                UserLocationPing.objects.get_or_create(
                    user=user,
                    defaults={
                        'latitude': Decimal(str(mem["lat"])),
                        'longitude': Decimal(str(mem["lon"])),
                        'battery_level': random.randint(30, 100),
                        'source': 'gps',
                        'recorded_at': NOW
                    }
                )
            
            print(f"  ✓ Added {mem['name']} ({mem['nickname']})")
            credentials.append(f"Email: {mem['email']} | Password: {SEED_PASSWORD} | Role: {mem['role']}")

        # 3. Add Medicines for Father and Mother
        print("  ✓ Adding BP Medicines for Father and Mother")
        if father_user:
            med_f, _ = Medicine.objects.get_or_create(
                user=father_user,
                name="Amlodipine (BP)",
                defaults={
                    "dosage": "5mg",
                    "frequency": "once_daily",
                    "schedule_times": "17:00",
                    "start_date": TODAY - timedelta(days=30),
                    "current_quantity": 60
                }
            )
        
        if mother_user:
            med_m, _ = Medicine.objects.get_or_create(
                user=mother_user,
                name="Losartan (BP)",
                defaults={
                    "dosage": "50mg",
                    "frequency": "once_daily",
                    "schedule_times": "17:00",
                    "start_date": TODAY - timedelta(days=60),
                    "current_quantity": 5 # low quantity to trigger "getting over"
                }
            )
            
        # 4. Add Notifications to Admin (Daughter)
        if admin_user:
            print("  ✓ Adding Notifications for Admin")
            # Notification 1: Mom took medicine in the morning
            Notification.objects.get_or_create(
                user=admin_user,
                title="Medicine Updates - Mom",
                body="Mom has took medicine in the morning.",
                notification_type="medication_reminder",
                defaults={}
            )
            
            # Notification 2: Drink water and stay hydrated
            Notification.objects.get_or_create(
                user=admin_user,
                title="Hydration Alert",
                body="Drink Water and stay hydrated.",
                notification_type="health_update",
                defaults={}
            )
            
            # Notification 3: Mom's medicine are getting over
            Notification.objects.get_or_create(
                user=admin_user,
                title="Refill Needed",
                body="Mom's medicine are getting over buy it asap.",
                notification_type="health_update",
                defaults={}
            )

    print('\n🎉 Seeding Complete! Here are the credentials for the 4 families:\n')
    for cred in credentials:
        print(cred)

if __name__ == '__main__':
    seed_families()
