from django.shortcuts import render


from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from user.models import Booking
from .models import ChatMessage
from .serializers import ChatMessageSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def booking_chat_history(request, booking_id):
    booking = (
        Booking.objects
        .select_related("user", "photographer__user")
        .filter(pk=booking_id)
        .first()
    )

    if booking is None:
        return Response(
            {"success": False, "message": "Booking not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    is_customer = booking.user_id == request.user.id
    is_photographer = booking.photographer.user_id == request.user.id

    if not (is_customer or is_photographer):
        return Response(
            {"success": False, "message": "You cannot access this chat."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if booking.status != "photographer_accepted":
        return Response(
            {"success": False, "message": "Chat is not available."},
            status=status.HTTP_403_FORBIDDEN,
        )

    messages = (
        ChatMessage.objects
        .filter(booking=booking)
        .order_by("-created_at", "-id")[:50]
    )

    messages = list(reversed(messages))

    return Response({
        "success": True,
        "booking_id": booking.id,
        "data": ChatMessageSerializer(messages, many=True).data,
    })