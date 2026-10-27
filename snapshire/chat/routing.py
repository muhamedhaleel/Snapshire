from django.urls import path

from .consumers import BookingChatConsumer


websocket_urlpatterns = [
    path(
        "ws/bookings/<int:booking_id>/chat/",
        BookingChatConsumer.as_asgi(),
    ),
]