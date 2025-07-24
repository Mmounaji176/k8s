from django.db.models import Max, Min, Avg
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from collections import defaultdict
from Api.models import Detections
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@api_view(['GET'])
def detection_stats_view(request):
    try:
        # Extract detections from the database
        detections = Detections.objects.all()
        
        stats = {
            'age': {
                'max': None,
                'min': None,
                'average': None
            },
            'gender_counts': defaultdict(int),
            'emotion_counts': defaultdict(int),
            'detections_with_json_result': 0  # Counter for detections with json_result
        }
        
        total_age = 0
        count = 0
        
        # Process each detection
        for detection in detections:
            if detection.json_result and 'results' in detection.json_result:
                stats['detections_with_json_result'] += 1  # Increment the counter
                
                for result in detection.json_result['results']:
                    # Process age
                    age = result.get('age')
                    if age is not None:
                        if stats['age']['max'] is None or age > stats['age']['max']:
                            stats['age']['max'] = age
                        if stats['age']['min'] is None or age < stats['age']['min']:
                            stats['age']['min'] = age
                        total_age += age
                        count += 1
                    
                    # Process gender
                    gender = result.get('dominant_gender')
                    if gender:
                        stats['gender_counts'][gender] += 1
                    
                    # Process emotion
                    emotion = result.get('dominant_emotion')
                    if emotion:
                        stats['emotion_counts'][emotion] += 1
        
        # Calculate average age
        if count > 0:
            stats['age']['average'] = round(total_age / count, 2)
        
        # Convert defaultdict to regular dict for JSON serialization
        stats['gender_counts'] = dict(stats['gender_counts'])
        stats['emotion_counts'] = dict(stats['emotion_counts'])
        
        return Response(stats, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@csrf_exempt
@api_view(['GET'])
def detection_stats_view_id(request,id):
    try:
        # Extract detections from the database
        detections = Detections.objects.filter(video_source=id)
        
        stats = {
            'age': {
                'max': None,
                'min': None,
                'average': None
            },
            'gender_counts': defaultdict(int),
            'emotion_counts': defaultdict(int),
            'detections_with_json_result': 0  # Counter for detections with json_result
        }
        
        total_age = 0
        count = 0
        
        # Process each detection
        for detection in detections:
            if detection.json_result and 'results' in detection.json_result:
                stats['detections_with_json_result'] += 1  # Increment the counter
                
                for result in detection.json_result['results']:
                    # Process age
                    age = result.get('age')
                    if age is not None:
                        if stats['age']['max'] is None or age > stats['age']['max']:
                            stats['age']['max'] = age
                        if stats['age']['min'] is None or age < stats['age']['min']:
                            stats['age']['min'] = age
                        total_age += age
                        count += 1
                    
                    # Process gender
                    gender = result.get('dominant_gender')
                    if gender:
                        stats['gender_counts'][gender] += 1
                    
                    # Process emotion
                    emotion = result.get('dominant_emotion')
                    if emotion:
                        stats['emotion_counts'][emotion] += 1
        
        # Calculate average age
        if count > 0:
            stats['age']['average'] = round(total_age / count, 2)
        
        # Convert defaultdict to regular dict for JSON serialization
        stats['gender_counts'] = dict(stats['gender_counts'])
        stats['emotion_counts'] = dict(stats['emotion_counts'])
        
        return Response(stats, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )