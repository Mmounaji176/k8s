from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"wsStatus/", consumers.StatusConsumer.as_asgi()),
]