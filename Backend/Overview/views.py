from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from rest_framework.pagination import PageNumberPagination
from Api.models import Person , DetectionPerson , Detections , Zones
from Api.serializers import DetectionsSerializer
from .serializers import PersonDetectionsSerializer, PersonSerializer, PersonPlacesSerializer, PersonTimeSerializer, PersonAllSerializer
from django.db.models import OuterRef, Subquery
from Api.serializers import PersonSerializer as ApiPersonSerializer
from django.db.models import OuterRef, Subquery, DateTimeField, Value, F, Q, Min
from django.http import JsonResponse

def get_conf_value_range(filter_range):
    if filter_range == "known":
        return (0.0, 0.40)
    elif filter_range == "high":
        return (0.40, 0.45)
    elif filter_range == "unknown":
        return (0.45, 0.99)
    return (0.0, 0.40)  
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20  
    page_size_query_param = 'page_size'
    max_page_size = 100  
    
@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def overview(request):
    paginator = PageNumberPagination()
    paginator.page_size = 20
    
    last_detection_subquery = DetectionPerson.objects.filter(
        person=OuterRef('pk'),
        conf_value__lte=0.40
    ).order_by('-created').values('created')[:1]
    
    persons = Person.objects.annotate(
        last_detection_date=Subquery(last_detection_subquery),
    ).filter(last_detection_date__isnull=False)
    persons = persons.order_by('-last_detection_date')
    
    result_page = paginator.paginate_queryset(persons, request)
    serializer = PersonSerializer(result_page, many=True, context={'count':1,'request':request})
    print(serializer.data) 
    return paginator.get_paginated_response(serializer.data)

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def detailed_overview(request, id, filter_range):
    paginator = PageNumberPagination()
    paginator.page_size = 20
    conf_range = get_conf_value_range(filter_range)
    
    try:
        person = Person.objects.get(id=id)
    except Person.DoesNotExist:
        return Response({'error': 'Person not found'}, status=404)
    
    last_detections = DetectionPerson.objects.filter(
        person=person,
        conf_value__range=conf_range
    ).order_by('-created').select_related('detection__video_source__place')
    
    result_page = paginator.paginate_queryset(last_detections, request)
    
    serializer = PersonDetectionsSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def filterd_detailed_overview(request, id, start_date_time, end_date_time, places, filter_range):
    places = places.split(',')
    paginator = PageNumberPagination()
    paginator.page_size = 20
    conf_range = get_conf_value_range(filter_range)
    person = None
    last_detections = None
    try:
        if id != "-1":
            person = Person.objects.get(id=id)
    except Person.DoesNotExist:
        return Response({'error': 'Person not found'}, status=404)
    if person is None:
        last_detections = DetectionPerson.objects.filter(
            conf_value__range=conf_range,
            created__range=(start_date_time, end_date_time)
        ).distinct()
    else:
        last_detections = DetectionPerson.objects.filter(
            person=person,
            conf_value__range=conf_range,
            created__range=(start_date_time, end_date_time)
        )
    
    if places[0] != "-1":
        last_detections = last_detections.filter(detection__video_source__place__id__in=places)
    
    last_detections = last_detections.order_by('-created').select_related('detection__video_source__place')
    
    result_page = paginator.paginate_queryset(last_detections, request)
    
    serializer = PersonDetectionsSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)




@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getDetectionsPersons(request, id, start_date_time, end_date_time, places, filter_range):
    places = places.split(',')
    paginator = PageNumberPagination()
    paginator.page_size = 20
    conf_range = get_conf_value_range(filter_range)
    person = None
    last_detections = None
    try:
        if id != "-1":
            person = Person.objects.get(id=id)
    except Person.DoesNotExist:
        return Response({'error': 'Person not found'}, status=404)
    if person is None:
        last_detections = DetectionPerson.objects.filter(
            conf_value__range=conf_range,
            created__range=(start_date_time, end_date_time)
        ).distinct()
    else:
        last_detections = DetectionPerson.objects.filter(
            person=person,
            conf_value__range=conf_range,
            created__range=(start_date_time, end_date_time)
        )
    
    if places[0] != "-1":
        last_detections = last_detections.filter(detection__video_source__place__id__in=places)
    
    last_detections = last_detections.order_by('-created').select_related('detection__video_source__place')
    
    result_page = paginator.paginate_queryset(last_detections, request)
    
    serializer = PersonDetectionsSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)
@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def overview_search(request, id, start_date_time, end_date_time, places, filter_range):
    paginator = PageNumberPagination()
    paginator.page_size = 20
    array_of_places = places.split(',')
    conf_range = get_conf_value_range(filter_range)
    
    context = {
        'start': start_date_time,
        'end': end_date_time,
        'filter_range': filter_range,
    }

    if array_of_places[0] != "-1":
        context['places'] = array_of_places
    else:
        zones = Zones.objects.all()
        places_ids = [zone.id for zone in zones]
        context['places'] = places_ids
        
    highest_conf_by_detection = DetectionPerson.objects.filter(
        detection=OuterRef('detection')
    ).order_by('conf_value').values('conf_value')[:1]

    detection_person_base = DetectionPerson.objects.filter(
        created__range=(start_date_time, end_date_time),
        conf_value__range=conf_range,
        conf_value=Subquery(highest_conf_by_detection)  
    )

    if array_of_places[0] != "-1":
        detection_person_base = detection_person_base.filter(
            detection__video_source__place__id__in=array_of_places
        )


    last_detection_subquery = detection_person_base.filter(
        person=OuterRef('pk')
    ).order_by('-created').values('created')[:1]

    persons = Person.objects.annotate(
        last_detection_date=Subquery(last_detection_subquery),
    ).filter(last_detection_date__isnull=False)

    if id != "-1":
        persons = persons.filter(id=id)

    persons = persons.order_by('-last_detection_date')

    result_page = paginator.paginate_queryset(persons, request)

    if id != "-1" and array_of_places[0] != "-1":
        serializer = PersonAllSerializer(result_page, many=True, context=context)
    elif id != "-1" and array_of_places[0] == "-1":
        serializer = PersonSerializer(result_page, many=True, context=context)
    elif array_of_places[0] != "-1" and id == "-1":
        serializer = PersonPlacesSerializer(result_page, many=True, context=context)
    else:
        serializer = PersonTimeSerializer(result_page, many=True, context=context)

    return paginator.get_paginated_response(serializer.data)
@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def extraDetails(request, id, start_date_time, end_date_time, places, filter_range):
    conf_range = get_conf_value_range(filter_range)
    array_of_places = places.split(',')
    
    highest_conf_by_detection = DetectionPerson.objects.filter(
        detection=OuterRef('detection')
    ).order_by('conf_value').values('conf_value')[:1]

    detection_person_base = DetectionPerson.objects.filter(
        created__range=(start_date_time, end_date_time),
        conf_value__range=conf_range
    )

    if array_of_places[0] != "-1":
        detection_person_base = detection_person_base.filter(
            detection__video_source__place__id__in=array_of_places
        )

    if id != "-1":
        person_detections = detection_person_base.filter(
            person_id=id,
            conf_value=Subquery(highest_conf_by_detection) 
        ).values('detection_id')

        detections_query = Detections.objects.filter(
            id__in=Subquery(person_detections)
        ).select_related(
            'video_source'
        ).distinct().order_by('-created')
    else:
        detections_query = Detections.objects.filter(
            detectionperson__in=detection_person_base.filter(
                conf_value=Subquery(highest_conf_by_detection)
            )
        ).select_related(
            'video_source'
        ).distinct().order_by('-created')

    paginator = StandardResultsSetPagination()
    result_page = paginator.paginate_queryset(detections_query, request)

    serializer = DetectionsSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)