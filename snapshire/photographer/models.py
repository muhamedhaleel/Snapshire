from django.contrib.auth.models import User
from django.db import models


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
    location = models.CharField(max_length=150, blank=True, default='')
    plan_mode = models.CharField(max_length=20, choices=PLAN_CHOICES, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Photographer Profile'
        verbose_name_plural = 'Photographer Profiles'

    def __str__(self):
        return self.user.username

    @property
    def is_profile_complete(self):
        return all([
            self.phone.strip(),
            self.bio.strip(),
            self.specialty.strip(),
            self.location.strip(),
        ])

    @property
    def plan_mode_label(self):
        if not self.plan_mode:
            return 'No plan selected'
        return self.get_plan_mode_display()
