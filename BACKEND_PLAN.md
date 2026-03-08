# DilCare Backend — Master Development Plan

> A comprehensive blueprint for building a production-grade Django REST API backend for the DilCare Health Companion mobile app.

---

## 📌 Executive Summary

**What's Done:**
- ✅ Auth Service (register, login, token refresh)
- ✅ User Service (profile CRUD, family link codes)
- ✅ Core abstractions (TimeStampedModel, SoftDeleteModel)
- ✅ JWT authentication setup
- ✅ API documentation (drf-spectacular)

**What's Needed:**
- 11 additional Django apps with models, views, serializers, and URL routes
- Celery for background tasks (reminders, notifications)
- Redis for caching + Celery broker
- PostgreSQL for production
- Firebase/Expo for push notifications
- External AI integration (OpenAI/Gemini)
- File uploads (prescriptions, documents)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      React Native App                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS (JWT Auth)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Django REST Framework                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ accounts │ │  health  │ │ medicine │ │  family  │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  steps   │ │  water   │ │  doctor  │ │    ai    │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │community │ │   bmi    │ │  gyaan   │ │   sos    │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
    ┌──────────────────────┼──────────────────────┐
    ▼                      ▼                      ▼
┌─────────┐          ┌──────────┐          ┌──────────────┐
│PostgreSQL│         │  Redis   │          │ Celery Beat  │
│(Database)│         │(Cache+   │          │ (Scheduled   │
│          │         │ Broker)  │          │  Tasks)      │
└─────────┘          └──────────┘          └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Firebase FCM │
                    │ (Push Notifs)│
                    └──────────────┘
```

---

## 📱 Django Apps Structure

Each app follows a consistent pattern:
```
appname/
├── __init__.py
├── admin.py           # Admin configuration
├── apps.py            # App config
├── models.py          # Database models
├── serializers.py     # DRF serializers
├── views.py           # API views
├── services.py        # Business logic layer
├── signals.py         # Django signals (optional)
├── tasks.py           # Celery tasks (optional)
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_views.py
│   └── test_services.py
├── migrations/
└── urls.py            # URL patterns
```

---

## 📊 Complete Database Schema

### Phase 1: Core Apps (Foundation)

#### 1. `accounts` (✅ Done - Enhance)
```python
# User model already exists, add:
class UserDevice(TimeStampedModel):
    """Store FCM tokens for push notifications"""
    user = ForeignKey(User, on_delete=CASCADE, related_name='devices')
    device_token = CharField(max_length=500)
    device_type = CharField(choices=[('ios', 'iOS'), ('android', 'Android')])
    is_active = BooleanField(default=True)
    
class UserSettings(TimeStampedModel):
    """User preferences"""
    user = OneToOneField(User, on_delete=CASCADE, related_name='settings')
    language = CharField(max_length=5, default='en')
    notifications_enabled = BooleanField(default=True)
    dark_mode = BooleanField(default=False)
    units = CharField(choices=[('metric', 'Metric'), ('imperial', 'Imperial')], default='metric')
```

#### 2. `health` — Health Readings & Vitals
```python
class HealthReading(SoftDeleteModel):
    """Store BP, Sugar, Weight, Heart Rate readings"""
    READING_TYPES = [
        ('bp', 'Blood Pressure'),
        ('sugar', 'Blood Sugar'),
        ('weight', 'Weight'),
        ('heart_rate', 'Heart Rate'),
    ]
    STATUS_CHOICES = [
        ('normal', 'Normal'),
        ('warning', 'Warning'),
        ('danger', 'Danger'),
    ]
    
    user = ForeignKey(User, on_delete=CASCADE, related_name='health_readings')
    reading_type = CharField(max_length=20, choices=READING_TYPES)
    value = CharField(max_length=50)  # "120/80" for BP, "95" for sugar
    value_numeric = FloatField(null=True)  # For calculations
    secondary_value = FloatField(null=True)  # For BP diastolic
    unit = CharField(max_length=20)
    status = CharField(max_length=20, choices=STATUS_CHOICES, default='normal')
    notes = TextField(blank=True)
    recorded_at = DateTimeField()  # User-specified time
    
    class Meta:
        ordering = ['-recorded_at']
        indexes = [
            Index(fields=['user', 'reading_type', '-recorded_at']),
        ]

class HealthGoal(TimeStampedModel):
    """Target ranges for health metrics"""
    user = ForeignKey(User, on_delete=CASCADE, related_name='health_goals')
    reading_type = CharField(max_length=20)
    min_value = FloatField(null=True)
    max_value = FloatField(null=True)
    target_value = FloatField(null=True)
```

#### 3. `medicine` — Medicine Reminders & Prescriptions
```python
class Medicine(SoftDeleteModel):
    """User's medicines"""
    FREQUENCY_CHOICES = [
        ('once', 'Once a day'),
        ('twice', 'Twice a day'),
        ('thrice', 'Three times a day'),
        ('custom', 'Custom'),
    ]
    
    user = ForeignKey(User, on_delete=CASCADE, related_name='medicines')
    name = CharField(max_length=200)
    dosage = CharField(max_length=100)  # "500mg"
    frequency = CharField(max_length=20, choices=FREQUENCY_CHOICES)
    instructions = TextField(blank=True)  # "After meals"
    start_date = DateField()
    end_date = DateField(null=True, blank=True)  # null = ongoing
    is_active = BooleanField(default=True)
    
class MedicineSchedule(TimeStampedModel):
    """When to take each medicine"""
    medicine = ForeignKey(Medicine, on_delete=CASCADE, related_name='schedules')
    time = TimeField()  # 08:00, 14:00, 20:00
    label = CharField(max_length=50, blank=True)  # "Morning", "Evening"
    
class MedicineLog(TimeStampedModel):
    """Daily medicine intake tracking"""
    STATUS_CHOICES = [
        ('taken', 'Taken'),
        ('missed', 'Missed'),
        ('skipped', 'Skipped'),
    ]
    
    medicine = ForeignKey(Medicine, on_delete=CASCADE, related_name='logs')
    schedule = ForeignKey(MedicineSchedule, on_delete=SET_NULL, null=True)
    scheduled_for = DateTimeField()
    status = CharField(max_length=20, choices=STATUS_CHOICES)
    taken_at = DateTimeField(null=True)

class Prescription(SoftDeleteModel):
    """Uploaded prescription documents"""
    user = ForeignKey(User, on_delete=CASCADE, related_name='prescriptions')
    name = CharField(max_length=200)
    doctor_name = CharField(max_length=200, blank=True)
    file = FileField(upload_to='prescriptions/%Y/%m/')
    file_type = CharField(max_length=20)  # image, pdf
    notes = TextField(blank=True)
    prescription_date = DateField(null=True)
```

#### 4. `family` — Parent-Child Linking
```python
class FamilyLink(TimeStampedModel):
    """Links a child (caregiver) to a parent (elderly)"""
    RELATIONSHIP_CHOICES = [
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('grandfather', 'Grandfather'),
        ('grandmother', 'Grandmother'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    
    parent = ForeignKey(User, on_delete=CASCADE, related_name='children_links')
    child = ForeignKey(User, on_delete=CASCADE, related_name='parent_links')
    relationship = CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    status = CharField(max_length=20, choices=STATUS_CHOICES, default='accepted')
    
    # Permissions - what can the child see?
    can_view_health = BooleanField(default=True)
    can_view_medicines = BooleanField(default=True)
    can_view_location = BooleanField(default=False)
    
    class Meta:
        unique_together = ['parent', 'child']
```

### Phase 2: Activity Tracking Apps

#### 5. `steps` — Step Counter & Goals
```python
class DailySteps(TimeStampedModel):
    """Daily step count aggregate"""
    user = ForeignKey(User, on_delete=CASCADE, related_name='daily_steps')
    date = DateField()
    total_steps = IntegerField(default=0)
    goal = IntegerField(default=10000)
    distance_meters = FloatField(null=True)
    calories_burned = FloatField(null=True)
    source = CharField(max_length=50, default='manual')  # manual, google_fit, apple_health
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']

class StepEntry(TimeStampedModel):
    """Individual step entries (for manual additions)"""
    daily_steps = ForeignKey(DailySteps, on_delete=CASCADE, related_name='entries')
    steps = IntegerField()
    notes = CharField(max_length=200, blank=True)

class StepGoal(TimeStampedModel):
    """User's step goals"""
    user = OneToOneField(User, on_delete=CASCADE, related_name='step_goal')
    daily_goal = IntegerField(default=10000)
    weekly_goal = IntegerField(default=70000)
    
class FitnessIntegration(TimeStampedModel):
    """Google Fit / Apple Health integration"""
    user = OneToOneField(User, on_delete=CASCADE, related_name='fitness_integration')
    provider = CharField(max_length=50)  # google_fit, apple_health
    access_token = TextField()
    refresh_token = TextField(blank=True)
    token_expires_at = DateTimeField()
    is_connected = BooleanField(default=True)
```

#### 6. `water` — Water Intake Tracker
```python
class DailyWaterIntake(TimeStampedModel):
    """Daily water consumption"""
    user = ForeignKey(User, on_delete=CASCADE, related_name='water_intake')
    date = DateField()
    glasses = IntegerField(default=0)
    ml_total = IntegerField(default=0)
    goal_glasses = IntegerField(default=8)
    goal_ml = IntegerField(default=2000)
    
    class Meta:
        unique_together = ['user', 'date']
        
class WaterLog(TimeStampedModel):
    """Individual water intake logs"""
    daily_intake = ForeignKey(DailyWaterIntake, on_delete=CASCADE, related_name='logs')
    glasses = IntegerField(default=1)
    ml = IntegerField(default=250)
    logged_at = DateTimeField(auto_now_add=True)
```

#### 7. `bmi` — BMI Calculator & History
```python
class BMIRecord(SoftDeleteModel):
    """BMI calculation history"""
    CATEGORY_CHOICES = [
        ('underweight', 'Underweight'),
        ('normal', 'Normal'),
        ('overweight', 'Overweight'),
        ('obese', 'Obese'),
    ]
    
    user = ForeignKey(User, on_delete=CASCADE, related_name='bmi_records')
    weight = FloatField()  # kg
    height = FloatField()  # cm
    bmi = FloatField()
    category = CharField(max_length=20, choices=CATEGORY_CHOICES)
    recorded_at = DateTimeField()
    
    class Meta:
        ordering = ['-recorded_at']
```

### Phase 3: Healthcare Provider Apps

#### 8. `doctor` — Doctors & Appointments
```python
class Doctor(SoftDeleteModel):
    """User's doctors/healthcare providers"""
    user = ForeignKey(User, on_delete=CASCADE, related_name='doctors')
    name = CharField(max_length=200)
    specialty = CharField(max_length=100, blank=True)
    hospital = CharField(max_length=200, blank=True)
    phone = CharField(max_length=20, blank=True)
    email = EmailField(blank=True)
    address = TextField(blank=True)
    is_primary = BooleanField(default=False)
    notes = TextField(blank=True)
    
class Appointment(SoftDeleteModel):
    """Medical appointments"""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('missed', 'Missed'),
    ]
    
    user = ForeignKey(User, on_delete=CASCADE, related_name='appointments')
    doctor = ForeignKey(Doctor, on_delete=SET_NULL, null=True, related_name='appointments')
    title = CharField(max_length=200)
    date = DateField()
    time = TimeField(null=True)
    location = CharField(max_length=300, blank=True)
    reason = TextField(blank=True)
    status = CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = TextField(blank=True)
    reminder_sent = BooleanField(default=False)
    
class MedicalDocument(SoftDeleteModel):
    """Lab reports, health records, etc."""
    DOCUMENT_TYPES = [
        ('lab_report', 'Lab Report'),
        ('scan', 'Scan/X-Ray'),
        ('prescription', 'Prescription'),
        ('insurance', 'Insurance'),
        ('other', 'Other'),
    ]
    
    user = ForeignKey(User, on_delete=CASCADE, related_name='documents')
    title = CharField(max_length=200)
    document_type = CharField(max_length=50, choices=DOCUMENT_TYPES)
    file = FileField(upload_to='documents/%Y/%m/')
    doctor = ForeignKey(Doctor, on_delete=SET_NULL, null=True, blank=True)
    document_date = DateField(null=True)
    notes = TextField(blank=True)
```

### Phase 4: Engagement & Emergency

#### 9. `sos` — Emergency Services
```python
class EmergencyContact(SoftDeleteModel):
    """User's emergency contacts"""
    user = ForeignKey(User, on_delete=CASCADE, related_name='emergency_contacts')
    name = CharField(max_length=200)
    phone = CharField(max_length=20)
    relationship = CharField(max_length=100, blank=True)
    is_primary = BooleanField(default=False)
    notify_on_sos = BooleanField(default=True)
    
class SOSEvent(TimeStampedModel):
    """SOS trigger history"""
    user = ForeignKey(User, on_delete=CASCADE, related_name='sos_events')
    triggered_at = DateTimeField(auto_now_add=True)
    latitude = FloatField(null=True)
    longitude = FloatField(null=True)
    address = TextField(blank=True)
    resolved_at = DateTimeField(null=True)
    notes = TextField(blank=True)
    
class SOSNotification(TimeStampedModel):
    """Track who was notified during SOS"""
    event = ForeignKey(SOSEvent, on_delete=CASCADE, related_name='notifications')
    contact = ForeignKey(EmergencyContact, on_delete=SET_NULL, null=True)
    phone = CharField(max_length=20)  # Backup if contact deleted
    notification_type = CharField(max_length=20)  # sms, push, call
    sent_at = DateTimeField(auto_now_add=True)
    delivered = BooleanField(default=False)
```

#### 10. `community` — Social Features
```python
class Leaderboard(TimeStampedModel):
    """Weekly/monthly step leaderboards"""
    user = ForeignKey(User, on_delete=CASCADE, related_name='leaderboard_entries')
    period_type = CharField(max_length=20)  # weekly, monthly
    period_start = DateField()
    period_end = DateField()
    total_steps = IntegerField(default=0)
    rank = IntegerField(null=True)
    
    class Meta:
        unique_together = ['user', 'period_type', 'period_start']

class Challenge(TimeStampedModel):
    """Community health challenges"""
    title = CharField(max_length=200)
    description = TextField()
    challenge_type = CharField(max_length=50)  # steps, water, medicines
    target_value = IntegerField()
    start_date = DateField()
    end_date = DateField()
    is_active = BooleanField(default=True)
    
class ChallengeParticipant(TimeStampedModel):
    """Users participating in challenges"""
    challenge = ForeignKey(Challenge, on_delete=CASCADE, related_name='participants')
    user = ForeignKey(User, on_delete=CASCADE, related_name='challenges')
    current_progress = IntegerField(default=0)
    completed = BooleanField(default=False)
    completed_at = DateTimeField(null=True)
    
    class Meta:
        unique_together = ['challenge', 'user']
```

#### 11. `gyaan` — Health Tips & Content
```python
class HealthTip(TimeStampedModel):
    """Curated health tips and articles"""
    CATEGORIES = [
        ('heart', 'Heart Health'),
        ('nutrition', 'Nutrition'),
        ('exercise', 'Exercise'),
        ('mental', 'Mental Health'),
        ('diabetes', 'Diabetes'),
        ('general', 'General Wellness'),
    ]
    
    title = CharField(max_length=300)
    content = TextField()
    category = CharField(max_length=50, choices=CATEGORIES)
    image_url = URLField(blank=True)
    reading_time_minutes = IntegerField(default=3)
    is_featured = BooleanField(default=False)
    published_at = DateTimeField()
    
    class Meta:
        ordering = ['-published_at']

class UserTipInteraction(TimeStampedModel):
    """Track user engagement with tips"""
    user = ForeignKey(User, on_delete=CASCADE, related_name='tip_interactions')
    tip = ForeignKey(HealthTip, on_delete=CASCADE, related_name='interactions')
    is_favorite = BooleanField(default=False)
    is_completed = BooleanField(default=False)
    read_at = DateTimeField(null=True)
    
    class Meta:
        unique_together = ['user', 'tip']
```

#### 12. `ai` — AI Health Assistant
```python
class ChatSession(TimeStampedModel):
    """AI chat sessions"""
    user = ForeignKey(User, on_delete=CASCADE, related_name='chat_sessions')
    title = CharField(max_length=200, blank=True)
    is_active = BooleanField(default=True)
    
class ChatMessage(TimeStampedModel):
    """Individual chat messages"""
    session = ForeignKey(ChatSession, on_delete=CASCADE, related_name='messages')
    role = CharField(max_length=20)  # user, assistant
    content = TextField()
    tokens_used = IntegerField(default=0)
    
    class Meta:
        ordering = ['created_at']
```

---

## 🔌 API Endpoints

### URL Structure Convention
```
/api/v1/{app}/{resource}/
/api/v1/{app}/{resource}/{id}/
/api/v1/{app}/{resource}/{id}/{action}/
```

### Complete Endpoint Map

#### Authentication (`/api/v1/auth/`)
| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| POST | `/register/` | Register new user | ✅ Done |
| POST | `/login/` | Get JWT tokens | ✅ Done |
| POST | `/refresh/` | Refresh access token | ✅ Done |
| POST | `/logout/` | Blacklist refresh token | 🔲 TODO |
| POST | `/password/reset/` | Request password reset | 🔲 TODO |
| POST | `/password/reset/confirm/` | Confirm password reset | 🔲 TODO |

#### User (`/api/v1/user/`)
| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| GET | `/profile/` | Get user profile | ✅ Done |
| PATCH | `/profile/` | Update profile | ✅ Done |
| GET | `/link-code/` | Get parent link code | ✅ Done |
| POST | `/link-code/regenerate/` | Generate new code | ✅ Done |
| GET | `/settings/` | Get user settings | 🔲 TODO |
| PATCH | `/settings/` | Update settings | 🔲 TODO |
| POST | `/devices/` | Register FCM token | 🔲 TODO |
| DELETE | `/devices/{token}/` | Remove FCM token | 🔲 TODO |

#### Health (`/api/v1/health/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/readings/` | List readings (filterable by type, date range) |
| POST | `/readings/` | Add new reading |
| GET | `/readings/{id}/` | Get specific reading |
| DELETE | `/readings/{id}/` | Delete reading |
| GET | `/summary/` | Get health summary (latest of each type) |
| GET | `/trends/` | Get weekly/monthly trends |
| GET | `/goals/` | Get health goals |
| PUT | `/goals/` | Set health goals |

#### Medicine (`/api/v1/medicines/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List all medicines |
| POST | `/` | Add new medicine |
| GET | `/{id}/` | Get medicine details |
| PATCH | `/{id}/` | Update medicine |
| DELETE | `/{id}/` | Delete medicine |
| POST | `/{id}/take/` | Mark medicine as taken |
| POST | `/{id}/skip/` | Mark medicine as skipped |
| GET | `/today/` | Get today's schedule |
| GET | `/history/` | Get intake history |

#### Prescriptions (`/api/v1/prescriptions/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List prescriptions |
| POST | `/` | Upload prescription |
| GET | `/{id}/` | Get prescription details |
| DELETE | `/{id}/` | Delete prescription |

#### Steps (`/api/v1/steps/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Get step data (date range) |
| GET | `/today/` | Get today's steps |
| POST | `/manual/` | Add manual steps |
| GET | `/goals/` | Get step goals |
| PUT | `/goals/` | Update step goals |
| POST | `/sync/` | Sync from fitness app |
| GET | `/weekly/` | Get weekly summary |
| GET | `/monthly/` | Get monthly summary |

#### Water (`/api/v1/water/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Get today's water intake |
| POST | `/add/` | Add glass(es) |
| POST | `/remove/` | Remove glass |
| GET | `/history/` | Get history (date range) |
| GET | `/goals/` | Get water goals |
| PUT | `/goals/` | Update water goals |

#### Family (`/api/v1/family/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/link/` | Link to parent using code |
| GET | `/parents/` | List linked parents |
| GET | `/parents/{id}/` | Get parent details |
| GET | `/parents/{id}/health/` | Get parent's health data |
| DELETE | `/parents/{id}/` | Unlink parent |
| GET | `/children/` | List linked children (for parent) |
| PATCH | `/children/{id}/permissions/` | Update child's permissions |

#### Doctors (`/api/v1/doctors/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List doctors |
| POST | `/` | Add doctor |
| GET | `/{id}/` | Get doctor details |
| PATCH | `/{id}/` | Update doctor |
| DELETE | `/{id}/` | Delete doctor |
| POST | `/{id}/set-primary/` | Set as primary doctor |

#### Appointments (`/api/v1/appointments/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List appointments |
| POST | `/` | Create appointment |
| GET | `/{id}/` | Get appointment details |
| PATCH | `/{id}/` | Update appointment |
| DELETE | `/{id}/` | Cancel appointment |
| GET | `/upcoming/` | Get upcoming appointments |

#### Documents (`/api/v1/documents/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List documents |
| POST | `/` | Upload document |
| GET | `/{id}/` | Get document details |
| DELETE | `/{id}/` | Delete document |
| GET | `/health-report/` | Generate health report PDF |

#### SOS (`/api/v1/sos/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/contacts/` | List emergency contacts |
| POST | `/contacts/` | Add emergency contact |
| DELETE | `/contacts/{id}/` | Delete contact |
| PUT | `/contacts/{id}/primary/` | Set as primary |
| POST | `/trigger/` | Trigger SOS alert |
| GET | `/history/` | Get SOS event history |

#### Community (`/api/v1/community/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/leaderboard/` | Get step leaderboard |
| GET | `/challenges/` | List available challenges |
| POST | `/challenges/{id}/join/` | Join a challenge |
| GET | `/challenges/{id}/progress/` | Get challenge progress |

#### BMI (`/api/v1/bmi/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Get BMI history |
| POST | `/` | Save BMI record |
| GET | `/latest/` | Get latest BMI |

#### Gyaan (Health Tips) (`/api/v1/gyaan/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tips/` | List health tips (paginated) |
| GET | `/tips/{id}/` | Get tip details |
| POST | `/tips/{id}/favorite/` | Toggle favorite |
| POST | `/tips/{id}/complete/` | Mark as read/complete |
| GET | `/favorites/` | Get favorited tips |

#### AI Assistant (`/api/v1/ai/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat/` | Send message, get AI response |
| GET | `/sessions/` | List chat sessions |
| GET | `/sessions/{id}/` | Get session with messages |
| DELETE | `/sessions/{id}/` | Delete chat session |

---

## ⚙️ Updated Settings & Dependencies

### Additional Requirements (requirements.txt)
```pip-requirements
# Current
Django>=5.1,<5.2
djangorestframework>=3.15,<4.0
djangorestframework-simplejwt>=5.3,<6.0
django-cors-headers>=4.3,<5.0
drf-spectacular>=0.27,<1.0

# Add these
# Database
psycopg2-binary>=2.9,<3.0          # PostgreSQL

# Background Tasks
celery>=5.3,<6.0
django-celery-beat>=2.5,<3.0       # Periodic tasks
redis>=5.0,<6.0                     # Celery broker + cache

# File handling
Pillow>=10.0,<11.0                  # Image processing
django-storages>=1.14,<2.0          # S3/cloud storage
boto3>=1.34,<2.0                    # AWS S3

# Push Notifications
firebase-admin>=6.0,<7.0            # FCM

# AI
openai>=1.0,<2.0                    # OpenAI API
# OR
google-generativeai>=0.3,<1.0       # Gemini API

# Utilities
python-dotenv>=1.0,<2.0             # Environment variables
django-filter>=24.0,<25.0           # Query filtering
django-cacheops>=7.0,<8.0           # ORM caching

# Production
gunicorn>=21.0,<22.0
whitenoise>=6.6,<7.0                # Static files

# Testing
pytest>=8.0,<9.0
pytest-django>=4.7,<5.0
factory-boy>=3.3,<4.0
```

### Environment Variables (.env)
```env
# Django
DEBUG=True
SECRET_KEY=your-super-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgres://user:pass@localhost:5432/dilcare

# Redis
REDIS_URL=redis://localhost:6379/0

# AWS S3 (for file uploads)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=dilcare-uploads
AWS_S3_REGION_NAME=ap-south-1

# Firebase
FIREBASE_CREDENTIALS_PATH=firebase-adminsdk.json

# AI
OPENAI_API_KEY=sk-...
# OR
GOOGLE_AI_API_KEY=

# SMS (for SOS)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
```

---

## 📋 Implementation Phases

### Phase 1: Health Tracking Core (Week 1-2)
1. Create `health` app
   - HealthReading model + CRUD
   - Status calculation logic (normal/warning/danger)
   - Trend aggregation endpoints
2. Create `medicine` app
   - Medicine + Schedule models
   - Today's schedule endpoint
   - Mark taken/missed functionality
3. Create `bmi` app
   - BMI calculation + history

### Phase 2: Activity Tracking (Week 2-3)
1. Create `steps` app
   - Daily steps tracking
   - Manual step addition
   - Weekly/monthly summaries
2. Create `water` app
   - Daily water intake
   - Add/remove glasses
   - History tracking

### Phase 3: Family & Care (Week 3-4)
1. Create `family` app
   - Link code validation
   - Parent-child linking
   - Permission management
   - Parent health data access
2. Enhance `accounts`
   - User settings
   - Device registration

### Phase 4: Healthcare Providers (Week 4-5)
1. Create `doctor` app
   - Doctor CRUD
   - Appointments
   - File uploads for documents
2. Add prescription uploads to `medicine`

### Phase 5: Emergency & Social (Week 5-6)
1. Create `sos` app
   - Emergency contacts
   - SOS trigger + notifications
2. Create `community` app
   - Leaderboards
   - Challenges

### Phase 6: Content & AI (Week 6-7)
1. Create `gyaan` app
   - Health tips management
   - User interactions (favorites, read)
2. Create `ai` app
   - Chat session management
   - OpenAI/Gemini integration

### Phase 7: Background Jobs & Polish (Week 7-8)
1. Set up Celery + Redis
2. Medicine reminder notifications
3. Appointment reminders
4. Daily summary notifications
5. SOS SMS/notifications

### Phase 8: Production Prep (Week 8+)
1. PostgreSQL migration
2. S3 file storage
3. Security hardening
4. Rate limiting
5. Logging & monitoring
6. API documentation polish
7. Load testing

---

## 🧪 Testing Strategy

### Unit Tests
- Model validations
- Serializer validation
- Business logic in services

### Integration Tests
- Full API endpoint tests
- Authentication flows
- File uploads

### Coverage Target: 80%+

---

## 🔒 Security Considerations

1. **Rate Limiting**: Implement on auth endpoints
2. **Input Validation**: Strong serializer validation
3. **File Upload**: Validate file types, scan for malware
4. **SOS**: Rate limit to prevent abuse
5. **Family Linking**: Ensure proper permission checks
6. **AI**: Implement content filtering
7. **HTTPS Only**: In production
8. **Secrets Management**: Use environment variables

---

## 📚 Key Design Decisions

### 1. UUID Primary Keys
All models use UUIDs - better for distributed systems, no ID enumeration

### 2. Soft Deletes
Critical models use soft delete - data retention, audit trail

### 3. Service Layer
Business logic separated into `services.py` - cleaner views, easier testing

### 4. Snake_case ↔ camelCase
Backend uses snake_case, API serializers transform to camelCase for frontend

### 5. Timezone Handling
All times stored as UTC, converted to user's timezone in serializers

---

## 🚀 Quick Start Commands

```bash
# Create new app
python manage.py startapp {appname}

# After adding models
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver

# Run Celery worker (when set up)
celery -A config worker -l info

# Run Celery beat (when set up)
celery -A config beat -l info
```

---

## 📁 Final Project Structure

```
DilCare_BE/
├── config/                 # Django project settings
│   ├── settings/
│   │   ├── base.py        # Common settings
│   │   ├── dev.py         # Development
│   │   └── prod.py        # Production
│   ├── celery.py          # Celery configuration
│   └── urls.py
├── core/                   # Shared utilities
├── accounts/               # ✅ Users, auth, settings
├── health/                 # 🔲 Health readings
├── medicine/               # 🔲 Medicine reminders
├── steps/                  # 🔲 Step tracking
├── water/                  # 🔲 Water intake
├── bmi/                    # 🔲 BMI calculator
├── family/                 # 🔲 Parent-child linking
├── doctor/                 # 🔲 Doctors, appointments
├── sos/                    # 🔲 Emergency services
├── community/              # 🔲 Challenges, leaderboard
├── gyaan/                  # 🔲 Health tips
├── ai/                     # 🔲 AI assistant
├── media/                  # Uploaded files
├── static/                 # Static files
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── .env                    # Environment variables
├── .gitignore
├── manage.py
└── README.md
```

---

This plan provides a complete blueprint for building a world-class backend for DilCare. Start with Phase 1 and iterate!
