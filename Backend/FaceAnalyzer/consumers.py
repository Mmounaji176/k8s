from channels.generic.websocket import AsyncWebsocketConsumer
import json
from Api.models import Detections 
class DatabaseChangeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("database_changes", self.channel_name)
        await self.accept()
        await self.send(text_data=json.dumps({
            "type": "database_change",
            "data": "hello1"
        }))

    async def disconnect(self, close_code):
        await self.send(text_data=json.dumps({
            "type": "database_change",
            "data": "hello2"
        }))
        await self.channel_layer.group_discard("database_changes", self.channel_name)

    async def database_change(self, event):
        await self.send(text_data=json.dumps({
            "type": "database_change",
            "data": event["data"]
        }))