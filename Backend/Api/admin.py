from django.contrib import admin
from .models import Roles ,Zones, Person , ImageProc , Detections , PersonImages , DetectionPerson , CustomUser

admin.site.register(Person)
admin.site.register(ImageProc)
admin.site.register(Detections)
admin.site.register(PersonImages)
admin.site.register(DetectionPerson)
admin.site.register(CustomUser)
admin.site.register(Zones)
admin.site.register(Roles)
