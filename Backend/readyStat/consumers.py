from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
import json 

class statConsumer(AsyncWebsocketConsumer):
    channel_layer_alias = 'status'  # Define which channel layer to use

    async def connect(self):
        try:
            # Accept the connection
            await self.accept()
            
            # Get the channel layer after connection is accepted
            self.channel_layer = get_channel_layer(self.channel_layer_alias)
            
            # Add to group
            await self.channel_layer.group_add(
                "stat",
                self.channel_name
            )
            print(f"Connected to {self.channel_layer_alias} channel layer")
        except Exception as e:
            print(f"Error in connect: {e}")
            await self.close()

    async def disconnect(self, close_code):
        try:
            if hasattr(self, 'channel_layer'):
                await self.channel_layer.group_discard(
                    "stat",
                    self.channel_name
                )
        except Exception as e:
            print(f"Error in disconnect: {e}")

    async def ready_state(self, event):
        try:
            message = event.get('message', '')
            await self.send(text_data=json.dumps({
                'message': message,
                'type': 'status_update'
            }))
        except Exception as e:
            print(f"Error in ready_state: {e}")