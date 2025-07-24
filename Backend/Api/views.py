from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from .models import Zones, ImageProc , Person , Detections , DetectionPerson , CustomUser
from .serializers import ImageProcSerializer ,ZonesSerializer ,ImageProcPlaceSerializer,CostumUserSerializer, PersonSerializer ,DetectionPersonSerializer2, DetectionsSerializer ,DetectionPersonSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from .task import mainloop 
from .janus_api import main_api_delete
# from rq import Queue
# from rq.worker import Worker
import redis
from rest_framework.pagination import PageNumberPagination
# from rq.command import send_stop_job_command
from redis import Redis
import redis
import cv2
from django.core.files.base import ContentFile
import uuid
from .helpers import get_detections_with_persons , send_stream_status
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
# from rq.job import Job
from datetime import timedelta
from django.db.models import OuterRef, Subquery, DateTimeField, Value, F, Q, Min, Max
from django.db import models
from celery.app.control import Control
import subprocess
import os 
from django.db.models.functions import Coalesce
from django.http import JsonResponse
import requests
from .gpu_registry import get_all_gpus, find_and_mark_idle_gpu, mark_gpu_idle

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def StreamFilter(request, place=None, detectiontype=None):

    allowed_places = CustomUser.objects.filter(id=request.user.id)
    userSerializer = CostumUserSerializer(allowed_places, many=True)
    allowd_zones = userSerializer.data[0]['zones']

    if request.method == "GET" and place is not None and detectiontype is not None: 
        stream = ImageProc.objects.filter(stream_type="face",place__id=place,place__type=detectiontype,thumbnail__isnull=False,place__id__in=allowd_zones).order_by("-created")
        serializer = ImageProcSerializer(stream, many=True)
        return Response(serializer.data)
    else:
        stream = ImageProc.objects.filter(stream_type="face",thumbnail__isnull=False).order_by("-created")
        serializer = ImageProcSerializer(stream, many=True)
        return Response(serializer.data)
@csrf_exempt
@api_view(['GET', 'POST','GET'])
@permission_classes([IsAuthenticated])
def Stream(request, flag=None, title=None):
    if request.method == "GET": 
        stream = ImageProc.objects.filter(thumbnail__isnull=False).order_by("-created")
        serializer = ImageProcSerializer(stream, many=True)
        return Response(serializer.data)
    elif request.method == "POST" and request.data.get('url') is None:
        if request.user.username != "bluedove":
            return Response("Not allowed", status=401)
        newdata = request.data.copy()
        newdata['url'] = 'none'
        serializer = ImageProcSerializer(data=newdata)
        if serializer.is_valid():
            instance = serializer.save()
            res = {"id":instance.id}
            return JsonResponse(res)
            
            
    elif request.data.get('url') is not None and request.method == 'POST':
        try:
            video_capture = cv2.VideoCapture(request.data['url'])
            ret, frame = video_capture.read()
            _, encoded_frame = cv2.imencode('.jpg', frame)
        except:
            send_stream_status("Can't get stream from URL")
            return Response({"error": "Video or stream not found. 1"}, status=status.HTTP_404_NOT_FOUND)
        
        if ret == False:
            send_stream_status("Can't get stream from URL 2")
            return Response({"error": "Video or stream not found. 2"}, status=status.HTTP_404_NOT_FOUND)
        
        send_stream_status("Get stream from URL")
        instance = None
        if request.data.get('id') is not None:
            stream = ImageProc.objects.filter(id=request.data['id']).first()
            data = {"url": request.data['url']}
            serializer = ImageProcSerializer(stream, data, partial=True)
            if serializer.is_valid():
                instance = serializer.save()  
        else:
            newdata = request.data.copy()
            serializer = ImageProcSerializer(data=newdata)
            if serializer.is_valid():
                instance = serializer.save()
                newdata['webrtc_stream_id'] = int(instance.id) + 1

        # Find and mark an idle GPU as busy
        pod_id, gpu_id = find_and_mark_idle_gpu()
        if pod_id is None:
            return Response({"error": "No idle GPU available"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # Set up environment variables
        env = os.environ.copy()
        env['DJANGO_SETTINGS_MODULE'] = 'Backend.settings'
        env['PYTHONPATH'] = '/app'
        env['CUDA_VISIBLE_DEVICES'] = str(gpu_id)
        env['CUDA_HOME'] = '/usr/local/cuda'
        env['LD_LIBRARY_PATH'] = f"{env['CUDA_HOME']}/lib64:{env['LD_LIBRARY_PATH']}"
        
        # Configure Celery worker
        command = [
            'celery',
            '-A', 'Backend',
            'worker',
            '--queues=solo_queue',
            '--pool=solo',
            '--concurrency=1',
            '-Ofair',
            '--heartbeat-interval=30',
        ]
        
        # Start Celery worker
        try:
            process = subprocess.Popen(
                command,
                env=env,
                cwd='/app/Backend/'
            )
            LOGGER.info(f"Started worker on GPU {gpu_id} (pod {pod_id})")
        except Exception as e:
            LOGGER.error(f"Error starting worker: {str(e)}")
            # Mark GPU as idle again if failed
            mark_gpu_idle(pod_id, gpu_id)
            return Response({"error": "Failed to start worker"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({"status": "success", "gpu_id": gpu_id, "pod_id": pod_id})
    else:
        return Response("error", status=status.HTTP_400_BAD_REQUEST)
            
@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def markPerson(request):
    if request.method == 'POST':
        instance = DetectionPerson.objects.get(detection__id=request.data.get('detection_id'),person__id=request.data.get('person_id'))
        instance.update_marked_person()
        return Response(status=status.HTTP_200_OK)
@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getStream(request , id):
    instance = ImageProc.objects.get(id=id)
    serializer = ImageProcSerializer(instance)
    return Response(serializer.data)

import psutil
@csrf_exempt
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def FilterStream(request,id):

    if request.method == "DELETE":
        if request.user.username != "bluedove":
            return Response("Not allowed", status=401)
        stream_id = ImageProc.objects.filter(id=id).values("id").first()
        id2 = (2147483647 - id)
        main_api_delete(id)
        main_api_delete(id2)
        jobId = ImageProc.objects.filter(id=id).values("procId").first()
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
            print("error is ",e)
        try:
            rtsp_delete_respons = requests.delete(f"http://admin:admin@normal_stream:9997/v3/config/paths/delete/live/{id}")
            print(f"rtsp_delete_respons is {rtsp_delete_respons}")
        except Exception as e:
            print(f"Error deleting rtsp stream {e}")
        ImageProc.objects.filter(id=id).delete()
        stream = ImageProc.objects.all().order_by("-created")
        serializer = ImageProcSerializer(stream, many=True)
        return Response(serializer.data)
       
from django.views.decorators.cache import  cache_page
from django.core.cache import cache
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20  
    page_size_query_param = 'page_size'
    max_page_size = 100  

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def markRead(request):
    if request.method == 'POST':
        instance = Detections.objects.get(id=request.data.get('id'))
        instance.update_is_read()
        return Response(status=status.HTTP_200_OK)
@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getDetectionsPersons(request, id, isknown):
    if request.method == 'GET':
        instance = get_cached_detections_queryset(id, isknown)

        paginator = StandardResultsSetPagination()
        result_page = paginator.paginate_queryset(instance, request)

        serializer = DetectionsSerializer(result_page, many=True)

        return paginator.get_paginated_response(serializer.data)
   
def get_cached_detections_queryset(id, isknown):
    cache_key = f"detections_queryset_{id}_{isknown}"
    
    instance = cache.get(cache_key)
    
    if not instance:
        min_conf_subquery = DetectionPerson.objects.filter(
            detection=OuterRef('pk')
        ).values('detection').annotate(
            min_conf=Min('conf_value')
        ).values('min_conf')

        queryset = Detections.objects.filter(video_source_id=id).annotate(
            min_conf_value=Subquery(min_conf_subquery)
        ).select_related('video_source').order_by("-created")
        
        if isknown == "known":
            instance = queryset.filter(min_conf_value__lte=0.40)
        elif isknown == "high":
            instance = queryset.filter(min_conf_value__gt=0.40, min_conf_value__lte=0.45)
        else:
            instance = queryset.filter(min_conf_value__gt=0.45)

        cache.set(cache_key, instance, timeout=10) 
    
    return instance
@api_view(['GET'])
@csrf_exempt
@permission_classes([IsAuthenticated])
def getDetectionsPerson(request,iduser, id, isknown):
    if request.method == 'GET':
        val = get_detections_with_persons(id)
        paginator = PageNumberPagination()
        paginator.page_size = 20
        instance = None 
        if isknown == "known":
            instance = Detections.objects.filter(video_source_id=id).order_by("-created").filter(detectionperson__conf_value__lte=0.40).filter(detectionperson__person__id=iduser)
        else:
            instance = Detections.objects.filter(video_source_id=id).order_by("-created").filter(detectionperson__conf_value__gt=0.40).filter(detectionperson__person__id=iduser)
        result_page = paginator.paginate_queryset(instance, request)
        serializer = DetectionsSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)


@api_view(['GET', 'POST','DELETE','PATCH'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def PersonImageView(request, *args, **kwargs):
    if request.method == 'POST':
        if request.user.username != "bluedove":
            return Response("Not allowed", status=401)
        serializer = PersonSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            paginator = PageNumberPagination()
            paginator.page_size = 20
            persons = Person.objects.all().order_by("-created")
            result_page = paginator.paginate_queryset(persons, request)
            serializer = PersonSerializer(result_page, many=True)

            return paginator.get_paginated_response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'PATCH' and kwargs.get('id') is not None:
        person_id = kwargs.get('id')
        try:
            person = Person.objects.get(pk=person_id)
        except Person.DoesNotExist:
            return Response({'error': 'Person not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = PersonSerializer(person, data=request.data, partial=request.method == 'PATCH')
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'GET' and kwargs.get('id') is None:
        paginator = PageNumberPagination()
        paginator.page_size = 20
        
        last_detection_subquery = DetectionPerson.objects.filter(
            person_id=OuterRef('pk')
            ,conf_value__lte=0.40
        ).order_by('-created').values('created')[:1]
        
        persons = Person.objects.annotate(
            last_detection_date=Coalesce(Subquery(last_detection_subquery, output_field=DateTimeField()), Value(None))
        ).order_by(F('last_detection_date').desc(nulls_last=True))
        persons = persons.order_by('last_detection_date')
        
        result_page = paginator.paginate_queryset(persons, request)
        serializer = PersonSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    elif request.method == 'GET' and kwargs.get('id') is not None:
        paginator = PageNumberPagination()
        paginator.page_size = 20
        persons = Person.objects.filter(id=kwargs.get('id'))
        result_page = paginator.paginate_queryset(persons, request)
        serializer = PersonSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    elif request.method == 'DELETE' and kwargs.get('id') is not None:
        if request.user.username != "bluedove":
            return Response("Not allowed", status=401)
        person = Person.objects.get(id=kwargs.get('id'))
        person.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
        
@csrf_exempt
@permission_classes([IsAuthenticated])
@api_view(['GET'])
def ProfileDetections(request,id):
    if request.method == 'GET':
        persons = Person.objects.get(id=id)
        serializer = PersonSerializer(persons,context={'exclude_encoding': True})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getEachPersonDetections(request, id):
    if request.method == 'GET':
        paginator = PageNumberPagination()
        paginator.page_size = 20
        try:
            detection_persons = None
            detection_persons = DetectionPerson.objects.filter(person_id=id,conf_value__lte=0.40)
            result_page = paginator.paginate_queryset(detection_persons, request)
            serializer = DetectionPersonSerializer2(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Detections.DoesNotExist:
            return Response({"error": "Detection not found."}, status=status.HTTP_404_NOT_FOUND)

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def searchProfiles(request,name):
    if request.method == 'GET':
        paginator = PageNumberPagination()
        paginator.page_size = 5
        try:
            persons = Person.objects.filter(name__contains=name)
            result_page = paginator.paginate_queryset(persons, request)
            serializer = PersonSerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Detections.DoesNotExist:
            return Response({"error": "Detection not found."}, status=status.HTTP_404_NOT_FOUND)
def stop_and_delete_stream(stream_id):
    try:
        id2 = (2147483647 - id)
        main_api_delete(stream_id)
        main_api_delete(id2)
        stream = ImageProc.objects.filter(id=stream_id).first()
        if not stream or not stream.procId:
            return
            
        try:
            process_id = int(stream.procId)
            
            try:
                os.kill(process_id, 0)
            except OSError:
                return
                
            process = psutil.Process(process_id)
            try:
                process.terminate()
                process.wait(timeout=2)
            except psutil.TimeoutExpired:
                process.kill()
            except Exception as e:
                print(f"Error terminating process {process_id}: {e}")
                
        except ValueError:
            print(f"Invalid process ID: {stream.procId}")
            
    except Exception as e:
        print(f"Error stopping stream {stream_id}: {e}")

@csrf_exempt
@api_view(['GET','POST','DELETE'])
@permission_classes([IsAuthenticated])
def zones(request, zonetype=None, place=None):
    allowed_places = CustomUser.objects.filter(id=request.user.id)
    userSerializer = CostumUserSerializer(allowed_places, many=True)
    allowd_zones = userSerializer.data[0]['zones']
    
    if request.method == 'GET' and zonetype is not None:
        try:
            places = Zones.objects.filter(type=zonetype, id__in=allowd_zones)
            serialzer = ZonesSerializer(places, many=True)
            return Response(serialzer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": "zones not found.1"}, status=status.HTTP_404_NOT_FOUND)
            
    elif request.method == 'GET' and place is None:
        try:
            places = Zones.objects.filter(id__in=allowd_zones)
            serialzer = ZonesSerializer(places, many=True)
            return Response(serialzer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": "zones not found.2"}, status=status.HTTP_404_NOT_FOUND)
            
    elif request.method == 'GET' and place is not None:
        try:
            places = Zones.objects.filter(id=place, id__in=allowd_zones)
            serialzer = ZonesSerializer(places, many=True)
            return Response(serialzer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": "zones not found.3"}, status=status.HTTP_404_NOT_FOUND)
            
    elif request.method == 'POST':
        if request.user.username != "bluedove":
            return Response("Not allowed", status=401)
        try:
            serializer = ZonesSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                places = Zones.objects.all()
                serialzer = ZonesSerializer(places, many=True)
                
                root_user = CustomUser.objects.get(username="bluedove")
                root_user.zones.set(places)
                return Response(serialzer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)
            
    elif request.method == 'DELETE' and place is not None:
        if request.user.username != "bluedove":
            return Response("Not allowed", status=401)
        try:
            zone_streams = ImageProc.objects.filter(place_id=place)
            
            for stream in zone_streams:
                stop_and_delete_stream(stream.id)
                stream.delete()
            
            Zones.objects.filter(id=place).delete()
            
            places = Zones.objects.all()
            serialzer = ZonesSerializer(places, many=True)
            return Response(serialzer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"Error deleting zone: {e}")
            return Response({"error": "Failed to delete zone"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    return Response({"error": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST)




@permission_classes([IsAuthenticated])
@api_view(['GET'])
@csrf_exempt
def PresentPersons(request, place_id):
    if request.method == 'GET':
        paginator = PageNumberPagination()
        paginator.page_size = 20
        try:
            last_detection_subquery = DetectionPerson.objects.filter(
                person_id=OuterRef('pk'),
                detection__video_source__place_id=place_id,
                conf_value__lte=0.40
            ).order_by('-created').values('created')[:1]
            
            persons = Person.objects.filter(
                detectionperson__detection__video_source__place_id=place_id,
                detectionperson__conf_value__lte=0.40
            ).annotate(
                last_detection_date=Coalesce(Subquery(last_detection_subquery, output_field=DateTimeField()), Value(None)),
                total_detections=models.Count('detectionperson', filter=models.Q(detectionperson__conf_value__lte=0.40))
            ).distinct().order_by(
                F('last_detection_date').desc(nulls_last=True),
                '-total_detections'
            )
            
            result_page = paginator.paginate_queryset(persons, request)
            serializer = PersonSerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def CameraFeed(request):
    if request.method == 'GET':
        from django.db import connection
        
        with connection.cursor() as cursor:
            # Get sequence name for Api_imageproc table
            cursor.execute("""
                SELECT column_default 
                FROM information_schema.columns 
                WHERE table_name = 'api_imageproc' 
                AND column_name = 'id';
            """)
            seq_info = cursor.fetchone()
            print("Sequence info:", seq_info)
            
            if seq_info:
                # Extract sequence name from the default value (typically looks like "nextval('sequence_name'::regclass)")
                sequence_name = seq_info[0].split("'")[1]
                print("Sequence name:", sequence_name)
                
                # Get current value
                cursor.execute(f"SELECT last_value FROM {sequence_name}")
                last_value = cursor.fetchone()[0]
                print("Last value:", last_value)
                
                # Get next value without permanently incrementing
                cursor.execute(f"SELECT nextval('{sequence_name}')")
                next_id = cursor.fetchone()[0]
                print("Next ID:", next_id)
                
                # Reset the sequence to previous value
                cursor.execute(f"SELECT setval('{sequence_name}', {next_id - 1}, true)")
            else:
                # If we can't get the sequence info, use a fallback method
                cursor.execute("""
                    SELECT coalesce(max(id), 0) + 1 
                    FROM "Api_imageproc";
                """)
                next_id = cursor.fetchone()[0]
                print("Fallback next ID:", next_id)
            
        streamLink = f'rtsp://{os.environ.get("STREAM_IP")}:{os.environ.get("STREAM_PORT")}/live/{next_id}'
        return JsonResponse({"rtsp_link": streamLink})
    
    return Response({"error": "no stream link"}, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getGPUStatus(request):
    if request.method == 'GET':
        try:
            # Run nvidia-smi to get GPU status
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu', '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return Response({"error": "Failed to get GPU status"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Parse the output
            gpu_status = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    index, name, mem_used, mem_total, gpu_util, temp = line.split(', ')
                    gpu_status.append({
                        'index': int(index),
                        'name': name,
                        'memory_used': float(mem_used),
                        'memory_total': float(mem_total),
                        'gpu_utilization': float(gpu_util),
                        'temperature': float(temp)
                    })
            
            return Response(gpu_status)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(["GET"])
@permission_classes([AllowAny])
def gpu_registry_view(request):
    """Return all registered GPUs and their status."""
    gpus = get_all_gpus()
    return Response({"gpus": gpus})