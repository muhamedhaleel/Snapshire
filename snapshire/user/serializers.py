from django.contrib.auth.models import User
from rest_framework import serializers
from .models import UserProfile
from django.contrib.auth import authenticate


class SignupSerializer(serializers.ModelSerializer):

    phone = serializers.CharField(write_only=True)
    bio = serializers.CharField(write_only=True, required=False)

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User

        fields = [
            "username",
            "email",
            "password",
            "phone",
            "bio",
        ]

    def validate_username(self, value):

        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")

        return value

    def validate_email(self, value):

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")

        return value

    def create(self, validated_data):

        phone = validated_data.pop("phone")
        bio = validated_data.pop("bio", "")

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"]
        )

        UserProfile.objects.create(
            user=user,
            phone=phone,
            bio=bio
        )

        return user
    
class LoginSerializer(serializers.Serializer):

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

        attrs["user"] = user

        return attrs
    

class UpdateProfileSerializer(serializers.ModelSerializer):

    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    phone = serializers.RegexField(
        regex=r'^\d{10}$',
        required=False,
        error_messages={
            "invalid": "Phone number must contain exactly 10 digits and only numbers."
        }
    )

    class Meta:
        model = UserProfile
        fields = [
            "username",
            "email",
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

        instance.phone = validated_data.get("phone", instance.phone)
        instance.bio = validated_data.get("bio", instance.bio)
        instance.location = validated_data.get("location", instance.location)
        instance.gender = validated_data.get("gender", instance.gender)

        instance.save()

        return instance

    def to_representation(self, instance):

        return {
            "username": instance.user.username,
            "email": instance.user.email,
            "phone": instance.phone,
            "bio": instance.bio,
            "location": instance.location,
            "gender": instance.gender,
        }