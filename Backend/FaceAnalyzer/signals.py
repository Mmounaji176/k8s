from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from Api.models import Detections
import logging


@receiver([post_save, post_delete], sender=Detections)
def notify_database_change(sender, instance, **kwargs):
    try:
        channel_layer = get_channel_layer()
        print(f"Signal triggered: {kwargs.get('signal')} for {instance}")

        async_to_sync(channel_layer.group_send)(
            "database_changes",
            {
                "type": "database_change",
                "data": { 
                    "id": instance.id,
                    "json_result":instance.json_result,
                }
            }
        )
    except Exception as e:
        print(f"Error in signal: {e}")