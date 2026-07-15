from django.contrib.auth.models import User
from rest_framework import serializers
from .models import UserProfile 
from photographer.models import PhotographerProfile
from django.contrib.auth import authenticate
from .models import Booking
from rest_framework import serializers
from .models import Notification
import re
from django.contrib.auth.password_validation import validate_password
import re
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password as django_validate_password



class SignupSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "confirm_password",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
        }

    # -------------------------
    # Username Validation
    # -------------------------
    def validate_username(self, value):
        value = value.strip()

        if len(value) < 3 or len(value) > 30:
            raise serializers.ValidationError(
                "Username must be between 3 and 30 characters."
            )

        # Must start with a letter and contain only letters, numbers, underscores
        if not re.fullmatch(r"^[A-Za-z][A-Za-z0-9_]*$", value):
            raise serializers.ValidationError(
                "Username must start with a letter and can contain only letters, numbers and underscores."
            )

        # Cannot be only numbers
        if len(set(value.lower())) == 1:
            raise serializers.ValidationError(
                "Username cannot consist of the same repeated character."
            )

        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                "Username already exists."
            )

        return value

    # -------------------------
    # Password Validation
    # -------------------------
    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must contain at least 8 characters."
            )

        if len(set(value)) == 1:
            raise serializers.ValidationError(
                "Password cannot contain only repeated characters."
            )

        if not re.search(r"[A-Z]", value):
            raise serializers.ValidationError(
                "Password must contain at least one uppercase letter."
            )

        if not re.search(r"[a-z]", value):
            raise serializers.ValidationError(
                "Password must contain at least one lowercase letter."
            )

        if not re.search(r"[0-9]", value):
            raise serializers.ValidationError(
                "Password must contain at least one number."
            )

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise serializers.ValidationError(
                "Password must contain at least one special character."
            )

        # Django built-in password validation
        django_validate_password(value)

        return value

    # -------------------------
    # Confirm Password
    # -------------------------
    def validate(self, attrs):
        if attrs.get("password") != attrs.get("confirm_password"):
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        return attrs

    # -------------------------
    # Create User
    # -------------------------
    def create(self, validated_data):
        validated_data.pop("confirm_password")

        user = User.objects.create_user(
            username=validated_data["username"].strip(),
            email=validated_data["email"].strip().lower(),
            password=validated_data["password"],
        )

        UserProfile.objects.create(user=user)

        return user

    
class LoginSerializer(serializers.Serializer):

    username = serializers.CharField()

    password = serializers.CharField(write_only=True)

    def validate(self, attrs):

        username = attrs["username"]
        password = attrs["password"]

        # Check if username exists
        try:
            user = User.objects.get(username=username)

        except User.DoesNotExist:
            raise serializers.ValidationError(
                "Invalid username or password."
            )

        # Check if it is a normal user account
        if not hasattr(user, "profile"):
            raise serializers.ValidationError(
                "User account not found."
            )

        # Check if the account is blocked
        if not user.is_active:
            raise serializers.ValidationError(
                "Your account has been blocked by the administrator. Please contact the administrator."
            )

        # Authenticate username and password
        user = authenticate(
            username=username,
            password=password
        )

        if not user:
            raise serializers.ValidationError(
                "Invalid username or password."
            )

        attrs["user"] = user

        return attrs

class UpdateProfileSerializer(serializers.ModelSerializer):

    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    first_name=serializers.CharField(required=True)
    last_name=serializers.CharField(required=True)

    phone = serializers.RegexField(
        regex=r'^\d{10}$',
        required=True,
        error_messages={
            "invalid": "Phone number must contain exactly 10 digits and only numbers."
        }
    )
    location=serializers.CharField(required=True)

    class Meta:
        model = UserProfile
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "bio",
            "location",
            "gender",
        ]

    # Username Validation
    def validate_username(self, value):
        user = self.instance.user

        if User.objects.exclude(id=user.id).filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")

        if len(value) < 4:
            raise serializers.ValidationError(
                "Username must be at least 4 characters."
            )

        return value

    # Email Validation
    def validate_email(self, value):
        user = self.instance.user

        if User.objects.exclude(id=user.id).filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")

        return value

    def update(self, instance, validated_data):

        if "username" in validated_data:
            instance.user.username = validated_data["username"]

        if "email" in validated_data:
            instance.user.email = validated_data["email"]

        instance.user.save()
        instance.first_name=validated_data.get("first_name",instance.first_name)
        instance.last_name=validated_data.get("last_name",instance.last_name)
        instance.phone = validated_data.get("phone", instance.phone)
        instance.bio = validated_data.get("bio", instance.bio)
        instance.location = validated_data.get("location", instance.location)
        instance.gender = validated_data.get("gender", instance.gender)

        instance.save()

        return instance

    def to_representation(self, instance):

        return {
            "username": instance.user.username,
            "first_name":instance.user.first_name,
            "last_name":instance.uses.last_name,
            "email": instance.user.email,
            "phone": instance.phone,
            "bio": instance.bio,
            "location": instance.location,
            "gender": instance.gender,
        }
    

class PhotographerViewSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source="user.username",
        read_only=True
    )

    class Meta:
        model = PhotographerProfile
        fields = [
            "id",
            "username",
            "profile_image",
            "specialty",
            "location",
            "portfolio_link",
        ]


class PhotographerDetailSerializer(serializers.ModelSerializer):

    username = serializers.CharField(source="user.username")
    email = serializers.EmailField(source="user.email")

    booking_policy = serializers.SerializerMethodField()

    class Meta:
        model = PhotographerProfile
        fields = [
            "id",
            "username",
            "email",
            "profile_image",
            "specialty",
            "experience",
            "location",
            "bio",
            "portfolio_link",
            "booking_policy",
        ]

    def get_booking_policy(self, obj):

        return {
            "advance_payment": "50% Advance Payment Required",
            "cancellation": "100% refund only if cancelled at least 24 hours before the booking.",
            "late_cancellation": "No refund for cancellations made within 24 hours of the booking.",
            "reschedule": "Rescheduling depends on photographer availability."
        }



from rest_framework import serializers
from photographer.models import Availability


from rest_framework import serializers
from photographer.models import Availability


class PhotographerAvailabilitySerializer(serializers.ModelSerializer):

    class Meta:
        model = Availability
        fields = [
            "id",
            "date",
            "morning_status",
            "afternoon_status",
        ]



class BookingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Booking
        fields = [
            "photographer",
            "date",
            "session",
            "location",
            "shoot_time",
            "hours",
            "requirements",
        ]



class UserBookingStatusSerializer(serializers.ModelSerializer):

    photographer_name = serializers.CharField(
        source="photographer.user.username",
        read_only=True
    )

    class Meta:
        model = Booking
        fields = [
            "id",
            "photographer_name",
            "location",
            "date",
            "session",
            "shoot_time",
            "status"
            
        ]


class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notification
        fields = [
            "id",
            "title",
            "message",
            "is_read",
            "created_at",
        ]



class PhotographerFilterSerializer(serializers.ModelSerializer):

    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = PhotographerProfile
        fields = [
            "id",
            "username",
            "profile_image",
            "specialty",
            "experience",
            "location",
            "plan_mode",
        ]


