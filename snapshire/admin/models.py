from django.db import models
from django.conf import settings

# Create your models here.


from django.db import models


class PlatformFee(models.Model):
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Platform Fee: ₹{self.amount}"




from django.db import models


class VerificationPlan(models.Model):
    PLAN_CHOICES = [
        ("gold", "Gold"),
        ("platinum", "Platinum"),
    ]

    plan_name = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        unique=True
    )
    verification_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_plan_name_display()} - {self.verification_charge}"



class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ("user_blocked", "User Blocked"),
        ("user_unlocked", "User Unlocked"),
        ("photographer_blocked", "Photographer Blocked"),
        ("photographer_unlocked", "Photographer Unlocked"),
        (
            "photographer_verification_approved",
            "Photographer Verification Approved",
        ),
    ]

    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    target_type = models.CharField(max_length=20)
    target_id = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.action} - {self.target_type} {self.target_id}"


class Announcement(models.Model):
    AUDIENCE_CHOICES = [
        ("all", "All Users"),
        ("customers", "Customers"),
        ("photographers", "Photographers"),
    ]

    title = models.CharField(max_length=200)
    message = models.TextField()

    audience = models.CharField(
        max_length=20,
        choices=AUDIENCE_CHOICES,
        default="all",
    )

    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title