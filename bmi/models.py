"""
BMI — Model for Body Mass Index records.
"""
from django.db import models
from django.conf import settings
from core.models import SoftDeleteModel


def compute_bmi(weight_kg: float, height_cm: float) -> float:
    """Calculate BMI from weight (kg) and height (cm)."""
    if height_cm <= 0:
        return 0.0
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 1)


def compute_category(bmi: float) -> str:
    """Return BMI category label."""
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal"
    if bmi < 30:
        return "Overweight"
    return "Obese"


class BMIRecord(SoftDeleteModel):
    """
    A BMI measurement record for a user.
    BMI and category are auto-computed from weight and height on save.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bmi_records",
    )
    weight = models.FloatField(help_text="Weight in kilograms")
    height = models.FloatField(help_text="Height in centimetres")
    bmi = models.FloatField(editable=False)
    category = models.CharField(max_length=20, editable=False)
    date = models.DateField()
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        verbose_name = "BMI Record"
        verbose_name_plural = "BMI Records"

    def save(self, *args, **kwargs):
        self.bmi = compute_bmi(self.weight, self.height)
        self.category = compute_category(self.bmi)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} — BMI {self.bmi} ({self.date})"
