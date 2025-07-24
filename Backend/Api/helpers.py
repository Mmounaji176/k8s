from .models import Detections , Person
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
def get_detections_with_persons(video_source_id):
    detections = Detections.objects.filter(video_source_id=video_source_id).order_by("-created")
    detections_with_persons = []
    for detection in detections:
        persons = detection.get_persons()
        detections_with_persons.append({'detection': detection, 'persons': persons})
    return detections_with_persons

def get_persons():
    persons = Person.objects.all()
    return persons


def send_stream_status(message: str):
    try:
        channel_layer = get_channel_layer('status')
        print(f"Sending message: {message} to status channel")
        async_to_sync(channel_layer.group_send)(
            "stat",
            {
                "type": "ready_state",
                "message": message
            }
        )
        print("Message sent successfully")
    except Exception as e:
        print(f"Error sending message: {e}")