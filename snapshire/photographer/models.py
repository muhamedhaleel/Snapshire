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
    location = models.CharField(max_length=150, blank=True, default='')
    profile_image = models.ImageField(upload_to=photographer_profile_image_path, blank=True, null=True)
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


class PortfolioLink(models.Model):
    profile = models.ForeignKey(
        PhotographerProfile,
        on_delete=models.CASCADE,
        related_name='portfolio_links',
    )
    url = models.URLField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.url


class PortfolioFile(models.Model):
    profile = models.ForeignKey(
        PhotographerProfile,
        on_delete=models.CASCADE,
        related_name='portfolio_files',
    )
    file = models.FileField(upload_to=portfolio_file_path)
    original_name = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.original_name or self.file.name

    def save(self, *args, **kwargs):
        if self.file and not self.original_name:
            self.original_name = self.file.name
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.file:
            self.file.delete(save=False)
        super().delete(*args, **kwargs)
