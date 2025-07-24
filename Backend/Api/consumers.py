# from channels.generic.websocket import AsyncWebsocketConsumer
# import json
# import cv2
# import base64
# import asyncio
# import ffmpeg

# class StreamConsumer(AsyncWebsocketConsumer):

#     async def connect(self):
#         await self.accept()
#         self.cap = None 
#         self.process = None

#     async def receive(self, text_data=None, bytes_data=None):
#         stream_link = text_data
#         rtmp_url = "rtmp://stream/app/1"
#         try:
#             if not self.cap:
#                 self.cap = cv2.VideoCapture(stream_link)
#             self.process = (
#                 ffmpeg
#                 .input('pipe:', format='rawvideo', pix_fmt='bgr24', s=f"{int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
#                 .output(rtmp_url, format='flv', vcodec='libx264', pix_fmt='yuv420p')
#                 .glxobal_args('-loglevel', 'error')
#                 .run_async(pipe_stdin=True)
#             )
#         except Exception as e:
#             print(e)
#             await self.send(text_data=json.dumps({"message":"error"}))
#             return
#         # while True:
#         #     ret = self.cap.grab()
#         #     if ret:
#         #         ret, frame = self.cap.retrieve() 
#         #         if not ret:
#         #             pass
#         #         _, buffer = cv2.imencode('.jpg', frame)
#         #         frame_base64 = base64.b64encode(buffer.tobytes()).decode('utf-8')
#         #         await self.send(text_data=json.dumps({"frame": frame_base64}))
#         #     await asyncio.sleep(0.010)
#             # await asyncio.sleep(1.5)

#     async def disconnect(self, close_code):
#         if self.cap:
#             self.cap.release()
#         await self.send(text_data=json.dumps({"message":"end"}))
