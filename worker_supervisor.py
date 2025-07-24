# worker_supervisor.py
import subprocess
import time
import psutil
import logging
import signal
import sys
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CelerySupervisor')

class CelerySupervisor:
    def __init__(self):
        self.workers = {}
        self.running = True
        
    def _start_worker(self, worker_id):
        cmd = (
            f"celery -A Backend.celery_prefork worker "
            f"--queues=prefork_queue "
            f"--concurrency=8 "
            f"--max-tasks-per-child=50 "
            f"--prefetch-multiplier=1 "
            f"-Ofair "
            f"--heartbeat-interval=30 "
            f"-n worker{worker_id}@%h"
        )
        try:
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            self.workers[worker_id] = process
            logger.info(f"Started worker {worker_id}")
            return process
        except Exception as e:
            logger.error(f"Error starting worker {worker_id}: {str(e)}")
            return None

    def _check_worker_health(self, worker_id, process):
        if process.poll() is not None:
            return False
        try:
            process_obj = psutil.Process(process.pid)
            return process_obj.status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def _restart_worker(self, worker_id):
        logger.warning(f"Restarting worker {worker_id}")
        if worker_id in self.workers:
            old_process = self.workers[worker_id]
            try:
                os.killpg(os.getpgid(old_process.pid), signal.SIGTERM)
            except:
                pass
        self._start_worker(worker_id)

    def start_and_monitor(self):
        def cleanup(*args):
            logger.info("Shutting down workers...")
            self.running = False
            for worker_id in list(self.workers.keys()):
                if worker_id in self.workers:
                    try:
                        process = self.workers[worker_id]
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    except:
                        pass
            sys.exit(0)

        signal.signal(signal.SIGTERM, cleanup)
        signal.signal(signal.SIGINT, cleanup)

        # Start initial workers
        self._start_worker(1)
        self._start_worker(2)

        while self.running:
            for worker_id, process in list(self.workers.items()):
                if not self._check_worker_health(worker_id, process):
                    logger.warning(f"Worker {worker_id} is not responding")
                    self._restart_worker(worker_id)
            time.sleep(30)

if __name__ == "__main__":
    supervisor = CelerySupervisor()
    supervisor.start_and_monitor()