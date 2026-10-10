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
        ("work_started", "Work Started"),
        ("in_progress", "Work In Progress"),
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

    photographer_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    platform_fee = models.DecimalField(
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
    reject_reason = models.TextField(
        blank=True,
        null=True
    )

    cancellation_reason = models.TextField(
    blank=True,
    null=True
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


class PasswordResetOTP(models.Model):
    email = models.EmailField(unique=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.email

class Payment(models.Model):

    PAYMENT_TYPE_CHOICES = [
        ("advance", "Advance"),
        ("balance", "Balance"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("created", "Created"),
        ("paid", "Paid"),
        ("failed", "Failed"),
    ]

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    razorpay_order_id = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True
    )

    razorpay_payment_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    razorpay_signature = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="created"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.booking.id} - {self.payment_type}"


class Feedback(models.Model):

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name="feedback"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="feedbacks"
    )

    photographer = models.ForeignKey(
        PhotographerProfile,
        on_delete=models.CASCADE,
        related_name="feedbacks"
    )

    rating = models.PositiveIntegerField()

    comment = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    feedback_by = models.CharField(
    max_length=20,
    choices=[
        ("user", "User"),
        ("photographer", "Photographer"),
    ],
    default="user",
    )

    def __str__(self):

        return (
            f"{self.photographer.user.username} "
            f"- {self.rating} stars"
        )
    
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User


class UserWallet(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="wallet"
    )

    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "User Wallet"
        verbose_name_plural = "User Wallets"

    def __str__(self):
        return f"{self.user.username} - ₹{self.balance}"
    

class WalletTransaction(models.Model):

    TRANSACTION_REFUND = "refund"

    TRANSACTION_TYPES = [
        (
            TRANSACTION_REFUND,
            "Refund"
        ),
    ]

    STATUS_PENDING = "pending"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (
            STATUS_PENDING,
            "Pending"
        ),
        (
            STATUS_COMPLETED,
            "Completed"
        ),
        (
            STATUS_FAILED,
            "Failed"
        ),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="wallet_transactions"
    )

    wallet = models.ForeignKey(
        UserWallet,
        on_delete=models.CASCADE,
        related_name="transactions"
    )

    booking = models.ForeignKey(
        "Booking",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wallet_transactions"
    )

    payment = models.ForeignKey(
        "Payment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wallet_transactions"
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )

    description = models.CharField(
        max_length=255,
        blank=True,
        default=""
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.transaction_type} - "
            f"₹{self.amount}"
        )





class RescheduleRequest(models.Model):

    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_ACCEPTED, "Accepted"),
        (STATUS_REJECTED, "Rejected"),
    ]

    SESSION_CHOICES = [
        ("morning", "Morning"),
        ("afternoon", "Afternoon"),
    ]

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="reschedule_requests"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reschedule_requests"
    )

    photographer = models.ForeignKey(
        PhotographerProfile,
        on_delete=models.CASCADE,
        related_name="reschedule_requests"
    )

    old_date = models.DateField()
    old_time = models.TimeField()

    new_date = models.DateField()
    new_time = models.TimeField()

    new_session = models.CharField(
        max_length=20,
        choices=SESSION_CHOICES
    )

    description = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    responded_at = models.DateTimeField(
        null=True,
        blank=True
    )