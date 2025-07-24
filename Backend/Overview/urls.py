from django.urls import path , register_converter
from .views import overview , detailed_overview , overview_search , filterd_detailed_overview , getDetectionsPersons , extraDetails
from .helpers.dateConverter import DateConverter
register_converter(DateConverter, 'date')
urlpatterns = [
    path('<str:filter_range>', overview),
    path('<int:id>/<str:filter_range>', detailed_overview),
    
    path('detailed/<str:id>/<date:start_date_time>/<date:end_date_time>/<str:places>/<str:filter_range>',filterd_detailed_overview),
    path('<str:id>/<date:start_date_time>/<date:end_date_time>/<str:places>/<str:filter_range>', overview_search),
    path('detailed_extra/<str:id>/<date:start_date_time>/<date:end_date_time>/<str:places>/<str:filter_range>',extraDetails),
]