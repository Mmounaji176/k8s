from channels.generic.websocket import AsyncWebsocketConsumer
import json 
import asyncio

class StatusConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.running = True 
    async def connect(self):
        await self.accept()
        while self.running:
            gpu_utilization = await self.gpu_utilization()
            memory_usage = await self.memory_usage()
            memory_usage_percentage = await self.memory_usage_percentage()
            status_data = {
                "gpu_usage": gpu_utilization,
                "memory_usage": memory_usage,
                "memory_usage_percentage":memory_usage_percentage
            }

            await self.send(text_data=json.dumps({"status": status_data}))
            await asyncio.sleep(1.2)

    async def gpu_utilization(self):
        command = ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"]
        process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

        gpu_utilization = [(utilization) for utilization in (await process.stdout.read()).decode().strip().split('\n')]
        return gpu_utilization

    async def memory_usage(self):
        command = ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"]
        process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

        gpu_memory_usage = [(memory) for memory in (await process.stdout.read()).decode().strip().split('\n')]
        return gpu_memory_usage

    async def memory_usage_percentage(self):
        command = ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"]
        process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

        output = (await process.stdout.read()).decode().strip()

        gpu_memory_info = [line.split(",") for line in output.split('\n')]

        memory_usage_percentages = []

        for info in gpu_memory_info:
            if len(info) == 2:
                used_memory, total_memory = map(int, info)
                if total_memory != 0:
                    memory_usage_percentage = (used_memory / total_memory) * 100
                    memory_usage_percentages.append(memory_usage_percentage)
                else:
                    memory_usage_percentages.append(None)
            else:
                memory_usage_percentages.append(None)

        return memory_usage_percentages


    async def receive(self, text_data=None, bytes_data=None):
        self.close()
    async def disconnect(self, close_code):
        self.running = False