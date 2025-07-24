# your_app/management/commands/rerun_processes.py
from django.core.management.base import BaseCommand
# from rq import Queue, Worker, Connection
import redis
from Api.models import ImageProc
from Api.task import mainloop 

class Command(BaseCommand):
    help = 'Re-run all the processes in the database'

    def handle(self, *args, **options):
        queue = Queue(connection=redis.Redis(host='redis', port=6379, db=0))

        stream = ImageProc.objects.all().order_by("-created")
        if not stream:
            self.stdout.write(self.style.WARNING('No ImageProc records found.'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Found {stream.count()} ImageProc records.'))

        for record in stream:
        
            job = queue.enqueue(mainloop, record.url, record.title, record.cuda_device, job_timeout=99999999)
            
            record.procId = job.id
            record.save()

            self.stdout.write(self.style.SUCCESS(f'Enqueued job for record {record.id} with new procId {job.id}.'))

        # with Worker(['my_queue']) as worker:
        #     worker.work() 
        #     self.stdout.write(self.style.SUCCESS('Starting worker to process jobs...'))
            # worker.work()

        self.stdout.write(self.style.SUCCESS('All processes have been re-enqueued and updated.'))
