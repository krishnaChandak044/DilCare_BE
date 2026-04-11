"""
Family — Models for family groups.
A Family is a group of up to 5 members who can view each other's health data.
"""
import string
import random

from django.db import models
from django.conf import settings
from core.models import TimeStampedModel, SoftDeleteModel


def generate_invite_code(length=6):
    """Generate a random 6-character alphanumeric invite code."""
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))


class Family(TimeStampedModel):
    """
    A family group that connects members.
    Free plan: 4 members, Plus: 6, Premium: 10.
    Created by one user, others join via invite_code.
    """
    PLAN_CHOICES = [
        ("free", "Free"),          # up to 4 members
        ("plus", "Plus"),          # up to 6 members — ₹99/month
        ("premium", "Premium"),    # up to 10 members — ₹199/month
    ]
    PLAN_LIMITS = {"free": 4, "plus": 6, "premium": 10}

    name = models.CharField(max_length=100, help_text="e.g. 'Sharma Family'")
    invite_code = models.CharField(
        max_length=6,
        unique=True,
        default=generate_invite_code,
        help_text="6-char code to invite members",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_families",
    )
    plan = models.CharField(
        max_length=10,
        choices=PLAN_CHOICES,
        default="free",
        help_text="Subscription plan (free/plus/premium)",
    )
    max_members = models.PositiveIntegerField(default=4)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Families"

    def __str__(self):
        return f"{self.name} ({self.invite_code}) [{self.plan}]"

    def save(self, *args, **kwargs):
        """Auto-sync max_members based on plan."""
        self.max_members = self.PLAN_LIMITS.get(self.plan, 4)
        super().save(*args, **kwargs)

    @property
    def member_count(self):
        return self.memberships.count()

    @property
    def is_full(self):
        return self.member_count >= self.max_members

    @property
    def slots_remaining(self):
        return max(0, self.max_members - self.member_count)

    def regenerate_invite_code(self):
        """Generate a new unique invite code."""
        while True:
            new_code = generate_invite_code()
            if not Family.objects.filter(invite_code=new_code).exists():
                self.invite_code = new_code
                self.save(update_fields=["invite_code"])
                return new_code


class FamilyMembership(TimeStampedModel):
    """
    A user's membership in a family.
    role: 'admin' (creator, can remove members) or 'member'.
    """
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("member", "Member"),
    ]

    family = models.ForeignKey(
        Family,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="family_membership",
        help_text="Each user can belong to only one family",
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="member")
    nickname = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="e.g. 'Papa', 'Mummy', 'Dadi'",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["joined_at"]

    def __str__(self):
        return f"{self.user.email} in {self.family.name} ({self.role})"


# ─── Keep old model for backward compatibility (deprecated) ───────────
class FamilyLink(SoftDeleteModel):
    """
    DEPRECATED — Old parent-child linking model.
    Kept for migration compatibility. Use Family + FamilyMembership instead.
    """
    RELATIONSHIP_CHOICES = [
        ("father", "Father"),
        ("mother", "Mother"),
        ("grandfather", "Grandfather"),
        ("grandmother", "Grandmother"),
        ("guardian", "Guardian"),
        ("other", "Other"),
    ]

    child = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="linked_parents",
    )
    parent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="linked_children",
    )
    relationship = models.CharField(
        max_length=20,
        choices=RELATIONSHIP_CHOICES,
        default="other",
    )
    is_active = models.BooleanField(default=True)
    linked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-linked_at"]
        unique_together = ["child", "parent"]

    def __str__(self):
        return f"[DEPRECATED] {self.child.email} → {self.parent.email}"
