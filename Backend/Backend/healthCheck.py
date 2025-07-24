
from Backend.celery_prefork import app, periodic_task_to_do, cleanup_old_temp_files , cleanup_old_detections

app.conf.timezone = "UTC"

app.conf.beat_schedule = {
    'add-every-five-seconds': {  
        'task': 'periodic_task_to_do',
        'schedule': 5.0,   
    },
}

@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    # Schedule process periodic_task_to_do to run every 5 seconds

    sender.add_periodic_task(
        30.0,
        cleanup_old_temp_files.s(),
        name="cleanup-old-temp-files",
        )
    sender.add_periodic_task(
        3600.0,
        cleanup_old_detections.s(),
        name="cleanup-old-detections",
    )

app.autodiscover_tasks() # to discover tasks


