from django.db import models

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
