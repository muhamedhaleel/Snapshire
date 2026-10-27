from rest_framework import serializers

from .models import ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    sender_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "booking",
            "sender_id",
            "message",
            "created_at",
        ]