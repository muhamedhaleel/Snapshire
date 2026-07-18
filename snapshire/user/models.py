from django.contrib.auth.models import User
from django.db import models
from photographer.models import PhotographerProfile
from django.utils import timezone


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    first_name = models.CharField(max_length=100,blank=True,default="")

    last_name = models.CharField(max_length=100,blank=True,default="")
    
    phone = models.CharField(max_length=20, blank=True, default='')
    bio = models.TextField(blank=True, default='')
    location = models.CharField(max_length=100, blank=True, default='')
    gender = models.CharField(
        max_length=10,
        choices=[
            ('Male', 'Male'),
            ('Female', 'Female'),
            ('Other', 'Other'),
        ],
        blank=True,
        default=''
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return self.user.username



class Booking(models.Model):

    SESSION_CHOICES = [
        ("morning", "Morning"),
        ("afternoon", "Afternoon"),
    ]

    STATUS_CHOICES = [
        ("payment_pending", "Payment Pending"),
        ("waiting_photographer", "Waiting for Photographer"),
        ("photographer_accepted", "Photographer Accepted"),
        ("photographer_rejected", "Photographer Rejected"),
        ("waiting_admin", "Waiting for Admin"),
        ("confirmed", "Confirmed"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    photographer = models.ForeignKey(
        PhotographerProfile,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    date = models.DateField()

    session = models.CharField(
        max_length=20,
        choices=SESSION_CHOICES
    )

    location = models.CharField(max_length=255)

    shoot_time = models.TimeField()

    hours = models.PositiveIntegerField()

    requirements = models.TextField(blank=True)

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    advance_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    balance_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="payment_pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.photographer.user.username}"
    


class Notification(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    title = models.CharField(max_length=100)

    message = models.TextField()

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.title}"




class EmailOTP(models.Model):

    email = models.EmailField(unique=True)

    username = models.CharField(max_length=150)

    password = models.CharField(max_length=128)

    otp = models.CharField(max_length=6)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.email
