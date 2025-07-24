# your_app/management/commands/scale_gpu_workers.py
from django.core.management.base import BaseCommand
from celery import Celery
import time
import logging
from Backend.celery import app

class Command(BaseCommand):
    help = 'Dynamically scale Celery workers based on queue length'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting worker scaling...')
        control = app.control

        while True:
            try:
                stats = control.inspect().stats()
                if stats:
                    print(stats)
                    for worker, info in stats.items():
                        tasks = info.get('tasks', {})
                        queue_length = len(tasks)

                        if queue_length > 10:  # Arbitrary threshold
                            # Scale up
                            control.add_consumer(queue='celery', exchange='celery', destination=[worker])
                        elif queue_length < 5:  # Arbitrary threshold
                            # Scale down
                            control.cancel_consumer(queue='celery', destination=[worker])
                else:
                    self.stderr.write('No stats available. Are workers running?')
                time.sleep(10)  # Adjust the sleep time as necessary
            except Exception as e:
                self.stderr.write(f'Error scaling workers: {e}')
                time.sleep(10)