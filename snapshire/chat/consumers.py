import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from user.models import Booking
from .models import ChatMessage


CHAT_ALLOWED_STATUS = "photographer_accepted"
MAX_MESSAGE_LENGTH = 2000


class BookingChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope.get("user")
        self.booking_id = self.scope["url_route"]["kwargs"]["booking_id"]
        self.room_group_name = f"booking_chat_{self.booking_id}"

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4401)
            return

        if not await self.has_chat_access():
            await self.close(code=4403)
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.accept()

        await self.send_json({
            "type": "connection_established",
            "booking_id": self.booking_id,
        })

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def receive(self, text_data=None, bytes_data=None):
        if text_data is None:
            await self.send_error("Text messages only.")
            return

        try:
            data = json.loads(text_data)
        except (json.JSONDecodeError, TypeError):
            await self.send_error("Invalid JSON.")
            return

        if not isinstance(data, dict):
            await self.send_error("A JSON object is required.")
            return

        message = data.get("message")

        if not isinstance(message, str):
            await self.send_error("Message must be text.")
            return

        message = message.strip()

        if not message:
            await self.send_error("Message cannot be empty.")
            return

        if len(message) > MAX_MESSAGE_LENGTH:
            await self.send_error("Message is too long.")
            return

        saved = await self.save_message(message)

        if saved is None:
            await self.send_error("Chat is no longer available.")
            await self.close(code=4403)
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                **saved,
            },
        )

    async def chat_message(self, event):
        await self.send_json({
            "type": "chat_message",
            "id": event["id"],
            "booking_id": event["booking_id"],
            "sender_id": event["sender_id"],
            "message": event["message"],
            "created_at": event["created_at"],
        })

    async def booking_status_changed(self, event):
        if event["status"] != CHAT_ALLOWED_STATUS:
            await self.send_json({
                "type": "chat_closed",
                "message": "Chat closed because the booking is no longer accepted.",
            })
            await self.close(code=4403)

    async def send_error(self, message):
        await self.send_json({
            "type": "error",
            "message": message,
        })

    async def send_json(self, content):
        await self.send(text_data=json.dumps(content))

    @database_sync_to_async
    def has_chat_access(self):
        booking = (
            Booking.objects
            .select_related("user", "photographer__user")
            .filter(pk=self.booking_id)
            .first()
        )

        if not booking:
            return False

        is_customer = booking.user_id == self.user.id
        is_photographer = booking.photographer.user_id == self.user.id

        return (
            (is_customer or is_photographer)
            and booking.status == CHAT_ALLOWED_STATUS
        )

    @database_sync_to_async
    def save_message(self, message):
        booking = (
            Booking.objects
            .select_related("user", "photographer__user")
            .filter(pk=self.booking_id)
            .first()
        )

        if not booking or booking.status != CHAT_ALLOWED_STATUS:
            return None

        is_customer = booking.user_id == self.user.id
        is_photographer = booking.photographer.user_id == self.user.id

        if not (is_customer or is_photographer):
            return None

        saved = ChatMessage.objects.create(
            booking=booking,
            sender=self.user,
            message=message,
        )

        return {
            "id": saved.id,
            "booking_id": booking.id,
            "sender_id": saved.sender_id,
            "message": saved.message,
            "created_at": saved.created_at.isoformat(),
        }