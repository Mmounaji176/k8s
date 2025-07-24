# celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')

app = Celery('Backend')


app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.update(
    broker_url='redis://:admin@redis-primary-service:6379/0',  
    result_backend='redis://:admin@redis-primary-service:6379/0',
    broker_connection_retry_on_startup=True,
)
app.conf.task_routes = {
    'Api.task.mainloop': {'queue': 'solo_queue'},
}
app.conf.task_queues = {
    'solo_queue': {
        'exchange': 'solo_queue',
        'routing_key': 'solo_queue',
    }
}