from django.db import models

from django.conf import settings
from django.db import models


class ChatMessage(models.Model):
    booking = models.ForeignKey(
        "user.Booking",
        on_delete=models.CASCADE,
        related_name="chat_messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sent_chat_messages",
    )
    message = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(fields=["booking", "created_at"]),
        ]

    def __str__(self):
        return f"Booking {self.booking_id}: message {self.id}"