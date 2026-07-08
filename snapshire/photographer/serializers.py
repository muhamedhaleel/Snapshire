from django.contrib.auth.models import User
from rest_framework import serializers
from .models import PhotographerProfile
from django.contrib.auth import authenticate


class SignupSerializer(serializers.ModelSerializer):

    confirm_password = serializers.CharField(write_only=True)

    password = serializers.CharField(
        write_only=True,
        min_length=6
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "confirm_password",
        ]

    def validate_username(self, value):

        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "Username already exists."
            )

        return value

    def validate_email(self, value):

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Email already exists."
            )

        return value

    def validate(self, attrs):

        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {
                    "confirm_password": "Passwords do not match."
                }
            )

        return attrs

    def create(self, validated_data):

        validated_data.pop("confirm_password")

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )

        PhotographerProfile.objects.create(
            user=user
        )

        return user
    
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()

    password = serializers.CharField(
        write_only=True
    )

    def validate(self, attrs):

        username = attrs["username"]
        password = attrs["password"]

        # Check whether the photographer account exists
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "Invalid username or password."
            )

        # Check whether the user is a photographer
        if not hasattr(user, "photographer_profile"):
            raise serializers.ValidationError(
                "Photographer account not found."
            )

        # Check whether the account is blocked
        if not user.is_active:
            raise serializers.ValidationError(
                "Your photographer account has been blocked by the administrator. Please contact the administrator."
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

    


class UpdatePhotographerProfileSerializer(serializers.ModelSerializer):

    username = serializers.CharField(required=False)

    email = serializers.EmailField(required=False)

    phone = serializers.RegexField(
        regex=r'^\d{10}$',
        required=True,
        error_messages={
            "invalid": "Phone number must contain exactly 10 digits."
        }
    )
    bio = serializers.CharField(required=False)
    specialty = serializers.CharField(required=True)
    experience=serializers.CharField(required=True)
    location = serializers.CharField(required=True)
    profile_image = serializers.ImageField(required=True)
    portfolio_link = serializers.URLField(required=False)
    portfolio_pdf = serializers.FileField(required=True)

    class Meta:
        model = PhotographerProfile

        fields = [
            "username",
            "email",
            "phone",
            "bio",
            "specialty",
            "experience",
            "location",
            "profile_image",
            "portfolio_link",
            "portfolio_pdf",
        ]

    def validate_username(self, value):

        user = self.instance.user

        if User.objects.exclude(id=user.id).filter(username=value).exists():
            raise serializers.ValidationError(
                "Username already exists."
            )

        return value

    def validate_email(self, value):

        user = self.instance.user

        if User.objects.exclude(id=user.id).filter(email=value).exists():
            raise serializers.ValidationError(
                "Email already exists."
            )

        return value

    def update(self, instance, validated_data):

        if "username" in validated_data:
            instance.user.username = validated_data["username"]

        if "email" in validated_data:
            instance.user.email = validated_data["email"]

        instance.user.save()

        instance.phone = validated_data.get("phone", instance.phone)
        instance.bio = validated_data.get("bio", instance.bio)
        instance.specialty = validated_data.get("specialty", instance.specialty)
        instance.experience = validated_data.get("experience",instance.experience)
        instance.location = validated_data.get("location", instance.location)
        instance.profile_image = validated_data.get("profile_image", instance.profile_image)
        instance.portfolio_link = validated_data.get("portfolio_link", instance.portfolio_link)
        instance.portfolio_pdf = validated_data.get("portfolio_pdf", instance.portfolio_pdf)

        instance.save()

        return instance

    def to_representation(self, instance):

        return {

            "username": instance.user.username,

            "email": instance.user.email,

            "phone": instance.phone,

            "bio": instance.bio,

            "specialty": instance.specialty,
            "experience": instance.experience,

            "location": instance.location,

            "profile_image": instance.profile_image.url if instance.profile_image else None,

            "portfolio_link": instance.portfolio_link,

            "portfolio_pdf": instance.portfolio_pdf.url if instance.portfolio_pdf else None,

            "plan_mode": instance.plan_mode,
            "verification_status": instance.verification_status,
            "is_verified": instance.is_verified,
        }



class PhotographerProfileSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source="user.username",
        read_only=True
    )

    email = serializers.EmailField(
        source="user.email",
        read_only=True
    )

    class Meta:
        model = PhotographerProfile
        fields = [
            "username",
            "email",
            "phone",
            "bio",
            "specialty",
            "experience",
            "location",
            "profile_image",
            "portfolio_link",
            "portfolio_pdf",
            "plan_mode",
            "verification_status",
           
            "created_at",
        ]



class VerificationSerializer(serializers.Serializer):

    plan_mode = serializers.ChoiceField(
        choices=[
            ("free", "Free"),
            ("gold", "Gold"),
            ("platinum", "Platinum"),
        ]
    )