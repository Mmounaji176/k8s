from django.contrib import admin
from django.urls import path , include
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/',include('Api.urls')),
    path('overview/',include('Overview.urls')),
    path('peoplecounting/',include('PeopleCounting.urls')),
    path('faceanalyzer/',include('FaceAnalyzer.urls')),

]
# urlpatterns += [
#     path('django-rq/', include('django_rq.urls'))
# ]
urlpatterns += static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
