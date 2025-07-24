from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from Api.models import Person , DetectionPerson
from Api.serializers import PersonImageSerializer
from django.db.models import OuterRef, Subquery, F, Window, Max, Count, Q
class PersonDetectionsSerializer(serializers.ModelSerializer):
    last_detection = serializers.SerializerMethodField()
    
    class Meta:
        model = DetectionPerson
        fields = ["last_detection"]
    
    def get_last_detection(self, obj):
        return {
            'detection_frame': obj.detection.detection_frame.url,
            'detection_frame_with_box': obj.detection.detection_frame_with_box.url,
            'camera': obj.detection.video_source.title,
            'place': obj.detection.video_source.place.name,
            'conf_value': obj.conf_value,
            'created': obj.created,
            'person_name' : obj.person.name,
            'person_image' : obj.person.images.first().image.url,
            # 'person_image' : obj.person.images.first(),
        }

class BasePersonSerializer(serializers.ModelSerializer):
    total_detections = serializers.SerializerMethodField()
    last_detection = serializers.SerializerMethodField()
    images = PersonImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(allow_empty_file=False, use_url=False),
        write_only=True
    )

    class Meta:
        model = Person
        fields = ["id", "name", "cin", "company_id", "images", "uploaded_images", "total_detections", "last_detection"]

    def get_serializer_context(self):
        return self.context

    def get_conf_value_range(self):
        filter_range = self.context.get('filter_range', 'known')
        if filter_range == "known":
            return (0.0, 0.40)
        elif filter_range == "high":
            return (0.40, 0.45)
        elif filter_range == "unknown":
            return (0.45, 0.99)
        return (0.0, 0.40)  # Default to known range

    def get_total_detections(self, obj):
        conf_range = self.get_conf_value_range()
        
        highest_conf_by_detection = DetectionPerson.objects.filter(
            detection=OuterRef('detection')
        ).order_by('conf_value').values('conf_value')[:1]

        detection_person_base = DetectionPerson.objects.filter(
            created__range=(self.context.get('start', '1900-01-01'), self.context.get('end', '2100-01-01')),
            conf_value__range=conf_range
        )

        if 'places' in self.context and self.context['places'][0] != "-1":
            detection_person_base = detection_person_base.filter(
                detection__video_source__place__id__in=self.context['places']
            )

        person_detections = detection_person_base.filter(
            person_id=obj.id,
            conf_value=Subquery(highest_conf_by_detection)
        )

        return person_detections.values('detection_id').distinct().count()

    def get_last_detection(self, obj):
        conf_range = self.get_conf_value_range()
        queryset = DetectionPerson.objects.filter(
            person=obj,
            conf_value__range=conf_range
        )
        if 'places' in self.context:
            queryset = queryset.filter(detection__video_source__place_id__in=self.context['places'])
        last_detection = queryset.order_by('-created').select_related('detection__video_source__place').first()
        if last_detection:
            return {
                'camera': last_detection.detection.video_source.title,
                'place': last_detection.detection.video_source.place.name,
                'conf_value': last_detection.conf_value,
                'created': last_detection.created,
            }
        return None

class PersonSerializer(BasePersonSerializer):
    pass

class PersonAllSerializer(BasePersonSerializer):
    pass

class PersonPlacesSerializer(BasePersonSerializer):
    pass

class PersonTimeSerializer(BasePersonSerializer):
    pass