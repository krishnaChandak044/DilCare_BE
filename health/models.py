"""
Health — Models for health readings (BP, Sugar, Weight, Heart Rate).
"""
from django.db import models
from django.conf import settings
from core.models import SoftDeleteModel


class HealthReading(SoftDeleteModel):
    """
    Store health readings: Blood Pressure, Blood Sugar, Weight, Heart Rate.
    Inherits: id (UUID), created_at, updated_at, is_deleted, deleted_at
    """
    READING_TYPES = [
        ('bp', 'Blood Pressure'),
        ('sugar', 'Blood Sugar'),
        ('weight', 'Weight'),
        ('heartRate', 'Heart Rate'),
    ]
    STATUS_CHOICES = [
        ('normal', 'Normal'),
        ('warning', 'Warning'),
        ('danger', 'Danger'),
    ]
    UNITS = {
        'bp': 'mmHg',
        'sugar': 'mg/dL',
        'weight': 'kg',
        'heartRate': 'BPM',
    }

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='health_readings'
    )
    reading_type = models.CharField(max_length=20, choices=READING_TYPES, db_index=True)
    value = models.CharField(max_length=50)  # "120/80" for BP, "95" for sugar
    value_primary = models.FloatField(null=True, blank=True)  # Systolic for BP, main value for others
    value_secondary = models.FloatField(null=True, blank=True)  # Diastolic for BP
    unit = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='normal')
    notes = models.TextField(blank=True, default='')
    recorded_at = models.DateTimeField(db_index=True)  # User-specified time

    class Meta:
        db_table = 'health_readings'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['user', 'reading_type', '-recorded_at']),
            models.Index(fields=['user', '-recorded_at']),
        ]
        verbose_name = 'Health Reading'
        verbose_name_plural = 'Health Readings'

    def __str__(self):
        return f"{self.user.email} - {self.reading_type}: {self.value}"

    def save(self, *args, **kwargs):
        # Auto-set unit based on reading type
        if not self.unit and self.reading_type in self.UNITS:
            self.unit = self.UNITS[self.reading_type]
        
        # Parse value into numeric fields for calculations
        self._parse_value()
        
        # Auto-calculate status based on reading type and value
        self.status = self._calculate_status()
        
        super().save(*args, **kwargs)

    def _parse_value(self):
        """Parse the value string into numeric fields."""
        try:
            if self.reading_type == 'bp' and '/' in self.value:
                parts = self.value.split('/')
                self.value_primary = float(parts[0].strip())
                self.value_secondary = float(parts[1].strip())
            else:
                self.value_primary = float(self.value.strip())
                self.value_secondary = None
        except (ValueError, IndexError):
            pass

    def _calculate_status(self):
        """Calculate status based on reading type and values."""
        if not self.value_primary:
            return 'normal'

        if self.reading_type == 'bp':
            systolic = self.value_primary
            diastolic = self.value_secondary or 0
            # Blood Pressure ranges
            if systolic >= 180 or diastolic >= 120:
                return 'danger'
            elif systolic >= 140 or diastolic >= 90:
                return 'warning'
            elif systolic < 90 or diastolic < 60:
                return 'warning'
            return 'normal'

        elif self.reading_type == 'sugar':
            # Fasting blood sugar ranges (mg/dL)
            sugar = self.value_primary
            if sugar >= 200:
                return 'danger'
            elif sugar >= 126 or sugar < 70:
                return 'warning'
            return 'normal'

        elif self.reading_type == 'heartRate':
            # Resting heart rate ranges (BPM)
            hr = self.value_primary
            if hr > 120 or hr < 40:
                return 'danger'
            elif hr > 100 or hr < 50:
                return 'warning'
            return 'normal'

        elif self.reading_type == 'weight':
            # Weight doesn't have inherent danger levels
            return 'normal'

        return 'normal'


class HealthGoal(SoftDeleteModel):
    """User-defined target ranges for health metrics."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='health_goals'
    )
    reading_type = models.CharField(max_length=20, choices=HealthReading.READING_TYPES)
    min_value = models.FloatField(null=True, blank=True)
    max_value = models.FloatField(null=True, blank=True)
    target_value = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'health_goals'
        unique_together = ['user', 'reading_type']
        verbose_name = 'Health Goal'
        verbose_name_plural = 'Health Goals'

    def __str__(self):
        return f"{self.user.email} - {self.reading_type} goal"
