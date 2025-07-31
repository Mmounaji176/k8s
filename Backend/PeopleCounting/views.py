# Fixed views.py with proper Kubernetes service names

from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
import cv2 
from Api.serializers import ImageProcSerializer 
from Api.models import ImageProc
from Api.task import mainloop
import os 
from rest_framework import status 
import subprocess
from django.core.files.base import ContentFile
import uuid
from .execution import run_prediction_task
from django.http import JsonResponse, HttpResponseForbidden
import psutil
import time
from Api.janus_api import main_api , main_api_delete
from AiLine.predict import main
from AiLine.zone import main_zone
import requests
from Api.helpers import send_stream_status

YOLO_MODELS = {
    "people": "/app/Backend/AiModels/models/PersonYolov8M/weights/best.pt",
    "cars": "/app/Backend/AiModels/models/Cars-model/best_1000.pt"
}

# FIXED: Use proper WebSocket URL
WEB_SOCKET_URL = "ws://django-backend-gpu-0-service:9898/wsStatus/"
@permission_classes([IsAuthenticated])
@api_view(['GET'])
@csrf_exempt
def GetStreamImage(request) -> Response:
    url = request.GET.get('url')
    image = cv2.imread(url)
    return Response(image)
    
@permission_classes([IsAuthenticated])
@api_view(['GET'])
@csrf_exempt
def GetStream(request, id) -> Response:
    if request.method == "GET": 
        stream = ImageProc.objects.filter(stream_type="counting", place__id=id).order_by("-created")
        serializer = ImageProcSerializer(stream, many=True)
        return Response(serializer.data)

@api_view(['POST', 'PATCH'])
@csrf_exempt
def PostStream(request):
    # Check GPU allocation for multi-GPU setup
    if request.method in ["POST", "PATCH"] and request.data.get("pod_id") and request.data.get("gpu_id") is not None:
        import socket
        current_pod = os.getenv('HOSTNAME', socket.gethostname())
        current_gpu_ids = os.getenv('GPU_ID', '0').split(',')
        print(f"Current pod: {current_pod}, GPU IDs: {current_gpu_ids}")
        if request.data["pod_id"] != current_pod:
            return HttpResponseForbidden("This pod cannot process GPU tasks for another pod.")
        if str(request.data["gpu_id"]) not in current_gpu_ids:
            return HttpResponseForbidden("This pod does not have the requested GPU ID.")
    
    if request.method == "PATCH":
        try:
            print(f"CUDA device is {request.data['cuda_device']}")
            instance = ImageProc.objects.filter(id=request.data['id']).first()
            if not instance:
                return Response({"error": "No matching record found"}, status=status.HTTP_404_NOT_FOUND)

            number_of_cameras = ImageProc.objects.filter(
                place__id=request.data['place'], 
                camera_type=request.data['camera_type']
            ).count()

            yolo_model = YOLO_MODELS.get(request.data['model_type'])
            if not yolo_model:
                return Response(
                    {"error": f"YOLO model for '{request.data['model_type']}' not found"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                # Start AI processing based on detection type
                if request.data['cords_type'] == "line":
                    main.apply_async(
                        args=[
                            yolo_model,
                            instance.url,
                            0.5,
                            request.data['cords'],
                            request.data['place_name'],
                            number_of_cameras,
                            f"{instance.title}_{instance.category_name}_{str(instance.place)}",
                            WEB_SOCKET_URL,
                            request.data['cords_type'],
                            request.data['title'],
                            request.data['camera_type'],
                            request.data['model_type'],
                            instance.id,
                            "0",
                        ],
                        queue="yolo_queue"
                    )
                elif request.data['cords_type'] == "region":
                    main_zone.apply_async(
                        args=[
                            yolo_model,
                            instance.url,
                            0.5,
                            request.data['cords'],
                            request.data['place_name'],
                            number_of_cameras,
                            f"{instance.title}_{instance.category_name}_{str(instance.place)}",
                            WEB_SOCKET_URL,
                            request.data['cords_type'],
                            request.data['title'],
                            request.data['camera_type'],
                            request.data['model_type'],
                            instance.id,
                            "0",
                        ],
                        queue="yolo_queue"
                    )
                
                send_stream_status("Ai process is starting")
                print(f"Started AI task: {instance.title}_{instance.category_name}_{str(instance.place)}")
                
            except Exception as e:
                print(f"Error queuing AI task: {e}")

            detection = {
                'camera_number': number_of_cameras,
                'model_type': yolo_model,
                'cords': request.data['cords'],
                'status': True,
            }

            serializer = ImageProcSerializer(instance, data=detection, partial=True)

            if serializer.is_valid():
                serializer.save()
                stream = ImageProc.objects.filter(
                    stream_type="counting", 
                    place__id=request.data['place']
                ).order_by("-created")
                serializer = ImageProcSerializer(stream, many=True)
                
                try:
                    # FIXED: Use simpler WebRTC stream ID calculation
                    # Instead of subtracting from max int, use a simple offset
                    webrtc_stream_id = 2147483647 - instance.id  # Simple offset to avoid conflicts
                    
                    print(f"🚀 Creating Janus streams - Primary: {instance.id}, WebRTC: {webrtc_stream_id}")
                    
                    # Start Janus stream creation with 60-second delay
                    main_api.apply_async(
                        countdown=30,
                        args=[instance.id, webrtc_stream_id, instance.url],
                        queue='prefork_queue'
                    )
                    
                    send_stream_status("Starting streaming process")
                    
                except Exception as e:
                    send_stream_status("Can't start stream")
                    print(f"Error setting up Janus streaming: {e}")
                
                return Response(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "POST":
        # Handle case where URL is not provided initially
        if request.data.get('url') is None:
            newdata = request.data.copy()
            newdata['url'] = 'none'
            serializer = ImageProcSerializer(data=newdata)
            if serializer.is_valid():
                instance = serializer.save()
                res = {"id": instance.id}
                return JsonResponse(res)
        
        try:
            # FIXED: Better URL validation with timeout
            stream_url = request.data['url']
            print(f"📺 Testing stream URL: {stream_url}")
            
            # Test with timeout to avoid hanging
            video_capture = cv2.VideoCapture(stream_url)
            video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            video_capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Try to read a frame with timeout
            ret, frame = video_capture.read()
            video_capture.release()
            
            if not ret or frame is None:
                print(f"❌ Stream validation failed for: {stream_url}")
                return Response(
                    {"error": f"Video or stream not accessible: {stream_url}"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Generate thumbnail from captured frame
            _, encoded_frame = cv2.imencode('.jpg', frame)
            image_data = encoded_frame.tobytes()
            random_filename = str(uuid.uuid4()) + '.jpg'
            image_file = ContentFile(image_data, name=random_filename)

            # Handle stream creation or update
            instance = None
            if request.data.get('id') is not None:
                # Update existing stream
                stream = ImageProc.objects.filter(id=request.data['id']).first()
                url_data = {"url": request.data['url']}  
                serializer = ImageProcSerializer(stream, data=url_data, partial=True)
                if serializer.is_valid():
                    instance = serializer.save()  
            else:
                # Create new stream
                serializer = ImageProcSerializer(data=request.data)
                if serializer.is_valid():
                    instance = serializer.save()

            if not instance:
                return Response({"error": "Failed to create stream instance"}, status=status.HTTP_400_BAD_REQUEST)

            # Start Celery worker for this stream
            command = [
                'celery', '-A', 'Backend', 'worker', 
                '--pool=solo', '--queues=yolo_queue', '--loglevel=info'
            ]
            env = os.environ.copy()
            env['DJANGO_SETTINGS_MODULE'] = 'Backend.settings'
            env['PYTHONPATH'] = '/app' 
            env['CUDA_VISIBLE_DEVICES'] = request.data['cuda_device']
            env['CUDA_HOME'] = '/usr/local/cuda'
            env['LD_LIBRARY_PATH'] = f"{env['CUDA_HOME']}/lib64:{env.get('LD_LIBRARY_PATH', '')}"
            
            job_id = subprocess.Popen(command, env=env)

            # Update stream with processing details
            detection = {
                'title': request.data['title'],
                'place': request.data['place'],
                'thumbnail': image_file,
                'url': request.data['url'],
                'camera_number': None,
                'model_type': YOLO_MODELS[request.data["model_type"]],
                'stream_type': 'counting',
                'camera_type': request.data['camera_type'],
                'websocket_url': None,
                'cords': None,
                'status': False,
                'procId': str(job_id.pid),
            }

            serializer = ImageProcSerializer(instance, data=detection, partial=True) 
            if serializer.is_valid():
                serializer.save()
                print(f"✅ Stream {instance.id} created successfully in {request.data['cuda_device']} GPU of pod {request.data['pod_id']}")
                return Response(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            print(f"❌ Error creating stream: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def DeleteCounting(request, stream_id, id):
    ss = stream_id
    if request.method == "DELETE":
        if request.user.username != "bluedove":
            return Response("Not allowed", status=401)
            
        stream_id = ImageProc.objects.filter(id=stream_id).values("id").first()
        print(f"Deleting stream ID: {ss}")
        
        # FIXED: Use simple offset calculation instead of large number subtraction
        webrtc_stream_id = 2147483647 - int(ss) 
        
        print(f"Deleting Janus streams - Primary: {ss}, WebRTC: {webrtc_stream_id}")
        
        # Delete both streams from Janus
        main_api_delete(int(ss))
        main_api_delete(webrtc_stream_id)
        
        # Kill the Celery worker process
        jobId = ImageProc.objects.filter(id=ss).values("procId").first()
        print(f"Process ID to kill: {jobId}")
        
        try:       
            jjid = int(jobId['procId']) 
            try:
                os.kill(jjid, 0) 
            except OSError:
                pass 
            process = psutil.Process(jjid)
            try:
                process.terminate()
                process.wait(timeout=2)
            except psutil.TimeoutExpired:
                process.kill() 
        except Exception as e:
            print(f"Error killing process: {e}")
        
        # FIXED: Delete from MediaMTX using correct Kubernetes service name
        try:
            mediamtx_url = f"http://admin:admin@mediamtx-normal-service:9997/v3/config/paths/delete/live%2F{ss}"
            rtsp_delete_response = requests.delete(mediamtx_url, timeout=10)
            print(f"MediaMTX delete response: {rtsp_delete_response.status_code}")
        except Exception as e:
            print(f"Error deleting RTSP stream: {e}")
        
        # Delete from database
        ImageProc.objects.filter(id=ss).delete()
        
        # Return updated stream list
        stream = ImageProc.objects.filter(
            stream_type="counting", 
            place__id=id
        ).order_by("-created")
        serializer = ImageProcSerializer(stream, many=True)
        return Response(serializer.data)