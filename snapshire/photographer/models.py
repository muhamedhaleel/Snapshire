from django.contrib.auth.models import User
from django.db import models


def photographer_profile_image_path(instance, filename):
    extension = filename.rsplit('.', 1)[-1].lower()
    return f'photographer_profiles/{instance.user_id}/profile.{extension}'


def portfolio_file_path(instance, filename):
    safe_name = filename.replace(' ', '_')
    return f'photographer_portfolios/{instance.profile.user_id}/{safe_name}'


class PhotographerProfile(models.Model):
    PLAN_FREE = 'free'
    PLAN_GOLD = 'gold'
    PLAN_PLATINUM = 'platinum'

    PLAN_CHOICES = [
        ('', 'Not selected'),
        (PLAN_FREE, 'Free'),
        (PLAN_GOLD, 'Gold'),
        (PLAN_PLATINUM, 'Platinum'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='photographer_profile',
    )
    phone = models.CharField(max_length=20, blank=True, default='')
    bio = models.TextField(blank=True, default='')
    specialty = models.CharField(max_length=100, blank=True, default='')
    experience = models.CharField(max_length=100, blank=True, default='')
    location = models.CharField(max_length=150, blank=True, default='')
    profile_image = models.ImageField(upload_to=photographer_profile_image_path, blank=True, null=True)
    portfolio_link = models.URLField(blank=True,default="")
    portfolio_pdf = models.FileField(upload_to="photographer_portfolios/",blank=True,null=True)
    plan_mode = models.CharField(max_length=20, choices=PLAN_CHOICES, blank=True, default='')
    verification_status = models.CharField(max_length=20, default="Pending")
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Photographer Profile'
        verbose_name_plural = 'Photographer Profiles'

    def __str__(self):
        return self.user.username
    


class WeeklyAvailability(models.Model):

    WEEKDAY_CHOICES = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]

    STATUS_CHOICES = [
        ("available", "Available"),
        ("unavailable", "Unavailable"),
    ]

    photographer = models.ForeignKey(
        PhotographerProfile,
        on_delete=models.CASCADE,
        related_name="weekly_availability"
    )

    weekday = models.IntegerField(
        choices=WEEKDAY_CHOICES
    )

    morning = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="unavailable"
    )

    afternoon = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="unavailable"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ("photographer", "weekday")
        ordering = ["weekday"]

    def __str__(self):
        return f"{self.photographer.user.username} - {self.get_weekday_display()}"


class AvailabilityException(models.Model):

    SESSION_CHOICES = [
        ("morning", "Morning"),
        ("afternoon", "Afternoon"),
        ("full_day", "Full Day"),
    ]

    photographer = models.ForeignKey(
        PhotographerProfile,
        on_delete=models.CASCADE,
        related_name="availability_exceptions"
    )

    date = models.DateField()

    session = models.CharField(
        max_length=20,
        choices=SESSION_CHOICES
    )

    reason = models.CharField(
        max_length=200,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = (
            "photographer",
            "date",
            "session",
        )
        ordering = ["date"]

    def __str__(self):
        return f"{self.photographer.user.username} - {self.date} ({self.session})"










