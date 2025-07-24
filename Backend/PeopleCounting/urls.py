from django.urls import path

from .views import GetStream , GetStreamImage , PostStream, DeleteCounting

urlpatterns = [
    path('streamCounting/<int:id>', GetStream),
    path('addStreamCounting/', PostStream),
    path('streamImage/', GetStreamImage),
    path('streamDelete/<str:stream_id>/<int:id>',DeleteCounting),
]