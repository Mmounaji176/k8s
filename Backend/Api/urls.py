from django.urls import path 
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import PresentPersons ,markPerson ,markRead ,Stream ,getDetectionsPerson ,zones,StreamFilter, FilterStream , searchProfiles, PersonImageView ,getStream , getEachPersonDetections, getDetectionsPersons , ProfileDetections, CameraFeed, getGPUStatus, gpu_registry_view

# , camerafeed
# from . import views
urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('camerafeed/',CameraFeed),
    path('stream/',Stream),
    path('stream/<int:id>',FilterStream,name="filterStream"),
    path('stream_page/<int:id>', getStream , name="getStream"),
    path('stream_detections/<int:id>/<str:isknown>',getDetectionsPersons,name="getdetection"),
    path('stream_detections/<int:iduser>/<int:id>/<str:isknown>',getDetectionsPerson),
    path('streamfilter/<int:place>/<str:detectiontype>',StreamFilter,name="stream"),
    path('profile/',PersonImageView,name='ProfleUpload'),
    path('profile/<int:id>',PersonImageView,name='ProfleUpload'),
    path('profileDetections/<int:id>',ProfileDetections,name="profileDetections"),
    path('detectionsProfile/<int:id>',getEachPersonDetections),
    path('profile/<str:name>',searchProfiles),
    path('zones/',zones),
    path('zones/<int:place>',zones),
    path('zones/<str:zonetype>',zones),
    path('mark_read',markRead),
    path('marked_person',markPerson),
    path('presentPersons/<int:place_id>',PresentPersons),
    path('camera-feed/', CameraFeed, name='camera-feed'),
    path('gpu-status/', getGPUStatus, name='gpu-status'),
    path('gpus/', gpu_registry_view, name='gpu-registry'),
]