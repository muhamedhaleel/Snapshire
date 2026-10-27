from django.urls import path

from .views import booking_chat_history


urlpatterns = [
    path(
        "bookings/<int:booking_id>/messages/",
        booking_chat_history,
        name="booking-chat-history",
    ),
]