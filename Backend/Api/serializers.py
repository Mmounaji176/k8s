from .models import Zones, ImageProc , Person , PersonImages , Detections , DetectionPerson , CustomUser
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
import face_recognition
import datetime


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['name'] = user.username
        return token


def add_thumbnail_url(data, request):
    if data.get('thumbnail'):
        data['thumbnail_url'] = request.build_absolute_uri(data['thumbnail'])
    return data
class PersonImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonImages
        fields = ('id', 'image', 'created') 

    def __init__(self, *args, **kwargs):
        include_encoding = kwargs.pop('include_encoding', False)
        super().__init__(*args, **kwargs)
        if include_encoding:
            self.fields['encoding'] = serializers.ListField()

class PersonSerializer(serializers.ModelSerializer):
    total_detections = serializers.SerializerMethodField()
    last_detection = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(allow_empty_file=False, use_url=False),
        write_only=True
    )

    class Meta:
        model = Person
        fields = ["id", "name", "cin", "company_id", "images", "uploaded_images", 
                 "total_detections", "last_detection"]

    def get_images(self, obj):
        include_encoding = self.context.get('include_encoding', False)
        serializer = PersonImageSerializer(
            obj.images.all(), 
            many=True, 
            include_encoding=include_encoding
        )
        return serializer.data

    def get_total_detections(self, obj):
        return obj.detectionperson_set.filter(conf_value__lte=0.40).count()

    def get_last_detection(self, obj):
        last_detection = DetectionPerson.objects.filter(
            person=obj, 
            conf_value__lte=0.40
        ).order_by('-created').select_related('detection__video_source__place').first()
        
        if last_detection:
            return {
                'camera': last_detection.detection.video_source.title,
                'place': last_detection.detection.video_source.place.name,
                'conf_value': last_detection.conf_value,
                'created': last_detection.created,
            }
        return None

    def create(self, validated_data):
        uploaded_images = validated_data.pop("uploaded_images")
        person = Person.objects.create(**validated_data)

        for image in uploaded_images:
            try:
                face = face_recognition.load_image_file(image)
                face_encodings = face_recognition.face_encodings(face)
                if not face_encodings:
                    raise ValidationError("No face detected in the image")
                PersonImages.objects.create(
                    person=person, 
                    image=image, 
                    encoding=face_encodings[0].tolist()
                )
            except Exception as e:
                raise ValidationError(f"Error processing image: {str(e)}")

        return person

class CostumUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'zones', 'bio', 'cover_photo', 'roles']
class ZonesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zones
        fields = '__all__'


class ImageProcSerializer(serializers.ModelSerializer):
    # stream_status = serializers.SerializerMethodField()
    place_name = serializers.SerializerMethodField()
    def get_place_name(self, obj):
        return obj.place.name
    class Meta:
        model = ImageProc
        fields = '__all__'
class ImageProcPlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageProc
        fields = ('id','title','place')
class DetectionPersonSerializer(serializers.ModelSerializer):
    person = PersonSerializer()
    camera = serializers.SerializerMethodField()
    place = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    class Meta:
        model = DetectionPerson
        fields = ('person', 'conf_value','marked_person','camera','place', 'url')
    def get_camera(self, obj):
        return obj.detection.video_source.title
    def get_place(self, obj):
        return obj.detection.video_source.place.name
    def get_url(self, obj):
        return obj.detection.video_source.url


class DetectionsSerializer(serializers.ModelSerializer):
    detection_persons = DetectionPersonSerializer(many=True, source='get_persons',read_only=True)
    class Meta:
        model = Detections
        fields = ('id', 'name', 'is_read', 'video_source', 'detection_frame', 'detection_frame_with_box', 'created', 'detection_persons', 'json_result','deep_face_processed')
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        
        if 'detection_persons' in ret:
            ret['detection_persons'] = sorted(ret['detection_persons'], key=lambda x: x['conf_value'])
        return self.convert_datetime_fields(ret)
    
    def convert_datetime_fields(self, data):
        for key, value in data.items():
            if isinstance(value, datetime.datetime):
                data[key] = value.isoformat()
            elif isinstance(value, list):
                data[key] = [self.convert_datetime_fields(item) if isinstance(item, dict) else item for item in value]
            elif isinstance(value, dict):
                data[key] = self.convert_datetime_fields(value)
        return data


class DetectionsWithVideSourceSerializero(serializers.ModelSerializer):
    detection_persons = DetectionPersonSerializer(many=True, source='get_persons',read_only=True)
    video_source = ImageProcSerializer()
    class Meta:
        model = Detections
        fields = ('name', 'video_source', 'detection_frame', 'created', 'detection_persons')


class DetectionPersonSerializer2(serializers.ModelSerializer):
    detection = DetectionsWithVideSourceSerializero()
    person = PersonSerializer()
    class Meta:
        model = DetectionPerson
        fields = '__all__'



