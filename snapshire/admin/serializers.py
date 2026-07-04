from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers

from user.models import UserProfile
from photographer.models import PhotographerProfile


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
    email = serializers.EmailField(source="user.email")

    status = serializers.SerializerMethodField()

    class Meta:
        model = PhotographerProfile
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

        if obj.user.is_active:
            return "Active"

        return "Blocked"