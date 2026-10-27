from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from user.models import Booking


@receiver(post_save, sender=Booking)
def close_chat_when_booking_not_accepted(
    sender, instance, **kwargs
):
    if instance.status == "photographer_accepted":
        return

    booking_id = instance.pk

    def notify_chat_group():
        channel_layer = get_channel_layer()

        if channel_layer is None:
            return

        async_to_sync(channel_layer.group_send)(
            f"booking_chat_{booking_id}",
            {
                "type": "booking_status_changed",
                "status": instance.status,
            },
        )

    transaction.on_commit(notify_chat_group)