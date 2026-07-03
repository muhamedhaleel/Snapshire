from django.contrib.auth import authenticate
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.models import User
from rest_framework import serializers


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


class UserListSerializer(serializers.ModelSerializer):

    phone = serializers.CharField(source="profile.phone", read_only=True)
    bio = serializers.CharField(source="profile.bio", read_only=True)

    status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone",
            "bio",
            "status",
        ]

    def get_status(self, obj):

        if obj.is_active:
            return "Active"

        return "Blocked"
    






class PhotographerListSerializer(serializers.ModelSerializer):

    phone = serializers.CharField(
        source="photographer_profile.phone",
        read_only=True
    )

    specialty = serializers.CharField(
        source="photographer_profile.specialty",
        read_only=True
    )

    location = serializers.CharField(
        source="photographer_profile.location",
        read_only=True
    )

    plan_mode = serializers.CharField(
        source="photographer_profile.plan_mode",
        read_only=True
    )

    verification_status = serializers.CharField(
        source="photographer_profile.verification_status",
        read_only=True
    )

    is_verified = serializers.BooleanField(
        source="photographer_profile.is_verified",
        read_only=True
    )

    status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone",
            "specialty",
            "location",
            "plan_mode",
            "verification_status",
            "is_verified",
            "status",
        ]

    def get_status(self, obj):

        if obj.is_active:
            return "Active"

        return "Blocked"