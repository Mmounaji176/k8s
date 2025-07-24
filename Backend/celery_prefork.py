import os
import torch
from gpu_registry import register_pod_gpus, heartbeat
import threading
import time

# GPU configuration
app.conf.update(
    gpu_count=2,
    gpu_devices="0,1",
    cuda_visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES', '0,1'),
    pytorch_cuda_alloc_conf='max_split_size_mb:256',
    nccl_debug='INFO',
    nccl_ib_disable='1',
    nccl_p2p_disable='1',
    cuda_version='12.6',
    cuda_launch_blocking='0',
    omp_num_threads='4',
    malloc_trim_threshold='100000',
) 

# Register GPUs on pod startup
if __name__ == "__main__" or True:
    gpu_count = torch.cuda.device_count()
    gpu_ids = list(range(gpu_count))
    register_pod_gpus(gpu_ids)

    # Start heartbeat thread
    def heartbeat_thread():
        while True:
            heartbeat()
            time.sleep(10)

    t = threading.Thread(target=heartbeat_thread, daemon=True)
    t.start() 