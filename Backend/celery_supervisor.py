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
        self.gpu_count = 2  # 2 GPUs per node
        
    def _start_worker(self, worker_id):
        # Configure GPU device for each worker
        gpu_device = (worker_id - 1) % 2  # Map worker to GPU device (0 or 1)
        
        cmd = (
            f"CUDA_VISIBLE_DEVICES={gpu_device} "
            f"celery -A Backend.celery_prefork worker "
            f"--queues=prefork_queue "
            f"--pool=prefork "
            f"--concurrency=10 "  # Reduced concurrency per worker
            f"-Ofair "
            f"--heartbeat-interval=30 "
            f"-n workerRecognition_gpu{gpu_device}@%h"
        )
        try:
            process = subprocess.Popen(
                cmd,
                shell=True,
                cwd='/app/Backend/',
                env=dict(os.environ, CUDA_VISIBLE_DEVICES=str(gpu_device))
            )
            self.workers[worker_id] = process
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

        # Start N workers (all GPU workers, regardless of node)
        for worker_id in range(1, self.gpu_count + 1):
            self._start_worker(worker_id)

        while self.running:
            for worker_id, process in list(self.workers.items()):
                if not self._check_worker_health(worker_id, process):
                    logger.warning(f"Worker {worker_id} is not responding")
                    self._restart_worker(worker_id)
            time.sleep(30)

if __name__ == "__main__":
    supervisor = CelerySupervisor()
    supervisor.start_and_monitor()