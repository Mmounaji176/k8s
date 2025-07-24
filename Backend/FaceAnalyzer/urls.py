from django.urls import path

from . import views

urlpatterns = [
    path('face_stats/', views.detection_stats_view, name='detect_faces'),
    path('face_stats/<int:id>', views.detection_stats_view_id, name='detect_faces'),
]