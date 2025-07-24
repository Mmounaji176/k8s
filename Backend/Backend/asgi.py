import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from django.urls import path
# import Api.routing
# from Api.consumers import StreamConsumer
from Notifications.consumers import NotificationConsumer
from status.consumers import StatusConsumer
from readyStat.consumers import statConsumer
from FaceAnalyzer.consumers import DatabaseChangeConsumer
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')

django_asgi_app = get_asgi_application()


application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": 
        URLRouter(
                [
                    # path('ws/',StreamConsumer.as_asgi()),
                    path('wsStatus/',StatusConsumer.as_asgi()),
                    path('wsNotification/',NotificationConsumer.as_asgi()),
                    path('wsStat/',statConsumer.as_asgi()),
                    path('ws_faceanalyze/',DatabaseChangeConsumer.as_asgi()),
                ]
            )
        

    }
)