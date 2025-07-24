from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from django.contrib.postgres.fields import ArrayField
from django.db.models import Prefetch
from django.conf import settings
import os

class Zones(models.Model):
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255, choices=(('face', 'face'), ('line', 'line'), ('area', 'area')), default='face')
    def __str__(self):
        return self.name
class Roles(models.Model):
    name = models.CharField(max_length=255)
    def __str__(self):
        return self.name
class CustomUser(AbstractUser):
    roles = models.ManyToManyField(Roles, limit_choices_to={'name__in': ['SUPERADMIN', 'LINE', 'FACE', 'AREA']},default=0)
    zones = models.ManyToManyField(Zones)
    bio = models.CharField(max_length=255, blank=True)
    cover_photo = models.ImageField(upload_to='covers/', null=True, blank=True)
    def __str__(self):
        return self.username

class ImageProc(models.Model):
    
    title = models.CharField(max_length=255,null=True)
    place = models.ForeignKey(Zones, on_delete=models.CASCADE)
    thumbnail = models.ImageField(upload_to='thumbnails', null=True, blank=True)
    url = models.TextField()
    websocket_url = models.TextField(null=True)
    cords = models.TextField(null=True)
    cords_type = models.CharField(max_length=255, null=True,choices=(('line', 'line'), ('region', 'region')), default='line')
    stream_type = models.CharField(max_length=255, choices=(('face', 'face'), ('counting', 'counting')), default='face')
    camera_type = models.CharField(max_length=255, null=True, blank=True)
    camera_number = models.IntegerField(null=True, blank=True)
    model_type = models.CharField(max_length=255, null=True, blank=True)
    category_name = models.CharField(max_length=255, null=True, blank=True)
    procId = models.CharField(max_length=255, null=True)
    taskId = models.CharField(max_length=255, null=True, blank=True)
    cuda_device = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    webrtc_stream_id = models.CharField(max_length=255, null=True, blank=True)
    def __str__(self):
        return self.title
    def save(self,*args , **kwargs):
        if self.cords is None:
            self.cords = "[]"
            return super().save(*args,**kwargs)
        else:
            self.cords = "["+self.cords+"]"
            return super().save(*args,**kwargs)
        
    def delete(self, *args, **kwargs):
        try:
            # Store thumbnail path before deletion
            thumbnail_path = self.thumbnail.path if self.thumbnail else None

            # Get all associated detections before they're cascade deleted
            detections = self.detections_set.all()

            # Delete detection images
            for detection in detections:
                try:
                    # Delete detection frame
                    if detection.detection_frame:
                        if os.path.exists(detection.detection_frame.path):
                            os.remove(detection.detection_frame.path)

                    # Delete detection frame with box
                    if detection.detection_frame_with_box:
                        if os.path.exists(detection.detection_frame_with_box.path):
                            os.remove(detection.detection_frame_with_box.path)
                except Exception as e:
                    print(f"Error deleting detection files for {detection.id}: {str(e)}")

            # Delete thumbnail
            if thumbnail_path and os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)

            # Clean up empty detection directories
            try:
                detection_dir = os.path.join(settings.MEDIA_ROOT, 'detections')
                if os.path.exists(detection_dir):
                    for root, dirs, files in os.walk(detection_dir, topdown=False):
                        for dir_name in dirs:
                            dir_path = os.path.join(root, dir_name)
                            if not os.listdir(dir_path):  # if directory is empty
                                os.rmdir(dir_path)
                                
                # Clean up empty thumbnail directory
                thumbnail_dir = os.path.join(settings.MEDIA_ROOT, 'thumbnails')
                if os.path.exists(thumbnail_dir):
                    for root, dirs, files in os.walk(thumbnail_dir, topdown=False):
                        for dir_name in dirs:
                            dir_path = os.path.join(root, dir_name)
                            if not os.listdir(dir_path):  # if directory is empty
                                os.rmdir(dir_path)
            except Exception as e:
                print(f"Error cleaning up directories: {str(e)}")

        except Exception as e:
            print(f"Error during file cleanup for stream {self.title}: {str(e)}")

        # Call the parent class delete method to complete the deletion
        super().delete(*args, **kwargs)
class Person(models.Model):
    name = models.CharField(max_length=250, unique=True)
    cin = models.CharField(max_length=100,unique=True,null=True)
    company_id = models.CharField(max_length=250,unique=True,null=True)
    detection_count = models.IntegerField(default=0)
    slug = models.SlugField(unique=True, null=True, blank=False)
    created = models.DateTimeField(auto_now_add=True,null=True)
    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return "%s" % (self.name)

class PersonImages(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to="database/", null=True, blank=True)
    encoding = ArrayField(models.FloatField(), default=list)
    created = models.DateTimeField(auto_now_add=True,null=True)
    def __str__(self):
        return "%s" % (self.person.name)
class DetectionPerson(models.Model):
    detection = models.ForeignKey('Detections', on_delete=models.CASCADE)
    person = models.ForeignKey('Person', on_delete=models.CASCADE)
    conf_value = models.FloatField(db_index=True)  # Added index
    marked_person = models.BooleanField(default=False, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, null=True, db_index=True)  # Added index

    def update_marked_person(self):
        self.marked_person = True
        self.save(update_fields=['marked_person'])  # Optimize save operation
        
    class Meta:
        indexes = [
            models.Index(fields=['person', 'conf_value', 'created']),
            models.Index(fields=['detection', 'conf_value']),
            models.Index(fields=['detection', 'person']),
        ]
        # Add index hints for common queries
        index_together = [
            ('person', 'conf_value', 'created'),
            ('detection', 'conf_value', 'created'),
        ]

class Detections(models.Model):
    name = models.CharField(max_length=250, unique=True)
    video_source = models.ForeignKey(ImageProc, on_delete=models.CASCADE, db_index=True)
    detection_frame = models.ImageField(upload_to="detections/", null=True, blank=True)
    detection_frame_with_box = models.ImageField(upload_to="detections/", null=True, blank=True)
    is_read = models.BooleanField(default=False, null=True, blank=True)
    deep_face_processed = models.BooleanField(default=False, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    json_result = models.JSONField(null=True, blank=True,default=dict)
    def add_person(self, person, conf_value):
        return DetectionPerson.objects.create(
            detection=self,
            person=person,
            conf_value=conf_value
        )

    def update_is_read(self):
        self.is_read = True
        self.save(update_fields=['is_read'])  # Optimize save operation
        
    def get_persons(self):
        return self.detectionperson_set.select_related('person').all()  # Optimize related lookup

    def remove_person(self, person):
        self.detectionperson_set.filter(person=person).delete()  # More efficient deletion
    def delete(self, *args, **kwargs):
        try:
            # Store file paths before deletion
            detection_frame_path = None
            detection_frame_box_path = None

            if self.detection_frame:
                detection_frame_path = self.detection_frame.path
            if self.detection_frame_with_box:
                detection_frame_box_path = self.detection_frame_with_box.path

            # Delete the actual files
            if detection_frame_path and os.path.exists(detection_frame_path):
                try:
                    os.remove(detection_frame_path)
                except Exception as e:
                    print(f"Error deleting detection frame for {self.name}: {str(e)}")

            if detection_frame_box_path and os.path.exists(detection_frame_box_path):
                try:
                    os.remove(detection_frame_box_path)
                except Exception as e:
                    print(f"Error deleting detection frame with box for {self.name}: {str(e)}")

            # Clean up empty directories in the detections folder
            try:
                detection_dir = os.path.join(settings.MEDIA_ROOT, 'detections')
                if os.path.exists(detection_dir):
                    for root, dirs, files in os.walk(detection_dir, topdown=False):
                        for dir_name in dirs:
                            dir_path = os.path.join(root, dir_name)
                            if not os.listdir(dir_path):  # if directory is empty
                                os.rmdir(dir_path)
            except Exception as e:
                print(f"Error cleaning up directories: {str(e)}")

        except Exception as e:
            print(f"Error during file cleanup for detection {self.name}: {str(e)}")

        # Call the parent class delete method to complete the deletion
        super().delete(*args, **kwargs)
    @classmethod
    def filter_by_person_name_and_time(cls, person_name, start_time, end_time, place, conf_range):
        base_query = cls.objects.select_related('video_source').prefetch_related(
            models.Prefetch(
                'detectionperson_set',
                queryset=DetectionPerson.objects.select_related('person')
            )
        )
        
        if conf_range == "known":
            return base_query.filter(
                detectionperson__person__name__icontains=person_name,
                detectionperson__conf_value__lte=0.40,
                video_source=place,
                created__range=(start_time, end_time)
            ).distinct().order_by('-created')[:20]
        else:
            return base_query.filter(
                detectionperson__person__name__icontains=person_name,
                detectionperson__conf_value__gt=0.40,
                detectionperson__conf_value__lte=0.45,
                video_source=place,
                created__range=(start_time, end_time)
            ).distinct().order_by('-created')[:20]

    @classmethod
    def filter_by_person_name_and_time_array(cls, person_names, start_time, end_time, place):
        return cls.objects.filter(
            detectionperson__person__name__in=person_names,
            detectionperson__conf_value__gt=0.45,
            video_source=place,
            created__range=(start_time, end_time)
        ).select_related('video_source').prefetch_related(
            models.Prefetch(
                'detectionperson_set',
                queryset=DetectionPerson.objects.select_related('person')
            )
        ).distinct().order_by('-created')[:20]

    class Meta:
        indexes = [
            models.Index(fields=['created']),
            models.Index(fields=['video_source']),
            models.Index(fields=['video_source', 'created']),
        ]
        # Add index hints for common queries
        index_together = [
            ('video_source', 'created'),
        ]