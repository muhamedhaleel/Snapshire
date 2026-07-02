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

        user = authenticate(
            username=attrs["username"],
            password=attrs["password"]
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
        required=False,
        error_messages={
            "invalid": "Phone number must contain exactly 10 digits."
        }
    )

    class Meta:
        model = PhotographerProfile

        fields = [
            "username",
            "email",
            "phone",
            "bio",
            "specialty",
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

            "location": instance.location,

            "profile_image": instance.profile_image.url if instance.profile_image else None,

            "portfolio_link": instance.portfolio_link,

            "portfolio_pdf": instance.portfolio_pdf.url if instance.portfolio_pdf else None,

            "plan_mode": instance.plan_mode,
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
            "location",
            "profile_image",
            "portfolio_link",
            "portfolio_pdf",
            "plan_mode",
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