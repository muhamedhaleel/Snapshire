from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers

from user.models import UserProfile
from photographer.models import PhotographerProfile
from user.models import Booking,Feedback,Payment
from .models import PlatformFee

class AdminLoginSerializer(serializers.Serializer):

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):

        user = authenticate(
            username=attrs["username"],
            password=attrs["password"]
        )

        if not user:
            raise serializers.ValidationError(
                "Invalid username or password."
            )

        if not user.is_superuser:
            raise serializers.ValidationError(
                "You are not authorized as an admin."
            )

        if not user.is_active:
            raise serializers.ValidationError(
                "Admin account is inactive."
            )

        attrs["user"] = user

        return attrs


# ===========================
# USER LIST SERIALIZER
# ===========================

class UserListSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(source="user.id")
    username = serializers.CharField(source="user.username")
    email = serializers.EmailField(source="user.email")

    status = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "username",
            "email",
            "phone",
            "bio",
            "status",
        ]

    def get_status(self, obj):

        if obj.user.is_active:
            return "Active"

        return "Blocked"


# ===========================
# PHOTOGRAPHER LIST SERIALIZER
# ===========================

class PhotographerListSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(source="user.id")
    username = serializers.CharField(source="user.username")
    photographer_name = serializers.SerializerMethodField()
    email = serializers.EmailField(source="user.email")

    status = serializers.SerializerMethodField()

    class Meta:
        model = PhotographerProfile
        fields = [
            "id",
            "username",
            "photographer_name",
            "email",
            "phone",
            "specialty",
            "experience",
            "location",
            "plan_mode",
            "verification_status",
            "is_verified",
            "status",
        ]

    def get_status(self, obj):

        if obj.user.is_active:
            return "Active"

        return "Blocked"
    
    def get_photographer_name(self, obj):

        first_name = obj.user.first_name.strip()
        last_name = obj.user.last_name.strip()

        full_name = f"{first_name} {last_name}".strip()

        return full_name if full_name else "Not added"
    


class AdminBookingManagementSerializer(serializers.ModelSerializer):

    user_name = serializers.CharField(
        source="user.username",
        read_only=True
    )

    photographer_name = serializers.CharField(
        source="photographer.user.username",
        read_only=True
    )

    class Meta:
        model = Booking
        fields = [
            "id",
            "user_name",
            "photographer_name",
            "location",
            "date",
            "session",
            "shoot_time",
            "hours",
            "total_amount",
            
            "status",
            "created_at",
        ]



class PendingPhotographerSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="user.id")

    username = serializers.CharField(source="user.username")
    photographer_name = serializers.SerializerMethodField()

    email = serializers.EmailField(source="user.email")

    class Meta:
        model = PhotographerProfile
        fields = [
            "id",
            "username",
            "photographer_name",
            "email",
            "profile_image",
            "specialty",
            "experience",
            "location",
            "verification_status",
            "created_at",
        ]




    def get_photographer_name(self, obj):
    
            first_name = obj.user.first_name.strip()
            last_name = obj.user.last_name.strip()
    
            full_name = f"{first_name} {last_name}".strip()
    
            return full_name if full_name else "Not added"

class PlatformFeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformFee
        fields = ["amount"]





class AdminDashboardSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    total_photographers = serializers.IntegerField()
    total_bookings = serializers.IntegerField()
    total_verified_photographers = serializers.IntegerField()
    total_gold_photographers = serializers.IntegerField()
    total_platinum_photographers = serializers.IntegerField()



class AdminFeedbackSerializer(serializers.ModelSerializer):

    user_id = serializers.IntegerField(
        source="user.id",
        read_only=True
    )

    username = serializers.CharField(
        source="user.username",
        read_only=True
    )

    photographer_id = serializers.IntegerField(
        source="photographer.id",
        read_only=True
    )

    photographer_name = serializers.SerializerMethodField()

    booking_id = serializers.IntegerField(
        source="booking.id",
        read_only=True
    )

    class Meta:
        model = Feedback
        fields = [
            "id",
            "booking_id",
            "user_id",
            "username",
            "photographer_id",
            "photographer_name",
            "rating",
            "comment",
            "created_at",
        ]

    def get_photographer_name(self, obj):
        if not obj.photographer:
            return ""

        return (
            f"{obj.photographer.user.first_name} "
            f"{obj.photographer.user.last_name}"
        ).strip()


class AdminWalletTransactionSerializer(serializers.ModelSerializer):

    booking_id = serializers.IntegerField(
        source="booking.id",
        read_only=True
    )

    user_name = serializers.SerializerMethodField()

    photographer_name = serializers.SerializerMethodField()

    total_amount = serializers.SerializerMethodField()

    platform_fee = serializers.DecimalField(
        source="booking.platform_fee",
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    payment_status = serializers.CharField(
        source="status",
        read_only=True
    )

    payment_date = serializers.DateTimeField(
        source="created_at",
        read_only=True
    )

    class Meta:
        model = Payment
        fields = [
            "booking_id",
            "user_name",
            "photographer_name",
            "total_amount",
            "platform_fee",
            "payment_status",
            "payment_date",
        ]

    def get_user_name(self, obj):

        user = obj.booking.user

        full_name = (
            f"{user.first_name} "
            f"{user.last_name}"
        ).strip()

        return full_name or user.username

    def get_photographer_name(self, obj):

        photographer = obj.booking.photographer

        if not photographer:
            return ""

        user = photographer.user

        full_name = (
            f"{user.first_name} "
            f"{user.last_name}"
        ).strip()

        return full_name or user.username

    def get_total_amount(self, obj):

        booking = obj.booking

        return (
            booking.photographer_amount +
            booking.platform_fee
        )


