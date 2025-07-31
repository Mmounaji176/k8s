import os
import time
import redis
import socket
import json

REDIS_URL = os.getenv('REDIS_CHANNEL_URL', 'redis://:admin@redis-channels-service:6380/0')
REGISTRY_KEY = 'gpu_registry'
HEARTBEAT_INTERVAL = 10  # seconds
STALE_THRESHOLD = 30    # seconds

r = redis.Redis.from_url(REDIS_URL)


def get_pod_id():
    """Return the unique identifier (hostname) for the current pod."""
    return os.getenv('HOSTNAME', socket.gethostname())


def get_node_name():
    """Return the Kubernetes node name where this pod is running."""
    return os.getenv('NODE_NAME', 'unknown-node')


def get_service_name():
    """Return the backend service name for this pod, either from env or by convention."""
    # Try to get from env, else infer from GPU_SERVICE_NAME or GPU_GROUP or fallback to pod_id
    # Recommend setting BACKEND_SERVICE_NAME in deployment
    svc = os.getenv('BACKEND_SERVICE_NAME')
    if svc:
        return svc
    # Fallback: try to infer from pod_id or group
    group = os.getenv('GPU_GROUP')
    if group:
        return f'django-backend-gpu-{group}-service'
    # Fallback: use pod_id (not recommended)
    pod_id = get_pod_id()
    return f'django-backend-gpu-{pod_id}-service'


def register_pod_gpus(gpu_ids, prefix_gpu_ids=None):
    """Register all GPUs managed by this pod in the Redis registry."""
    pod_id = get_pod_id()
    node = get_node_name()
    service = get_service_name()
    now = int(time.time())
    
    # Create GPU entries with prefix information
    gpus = []
    for i, gpu_id in enumerate(gpu_ids):
        gpu_info = {
            'id': gpu_id, 
            'status': 'idle', 
            'last_heartbeat': now
        }
        
        # Add prefix GPU ID if provided
        if prefix_gpu_ids and i < len(prefix_gpu_ids):
            gpu_info['prefix_id'] = prefix_gpu_ids[i]
        
        gpus.append(gpu_info)
    
    pod_info = {
        'node': node,
        'service': service,
        'gpus': gpus,
        'last_heartbeat': now
    }
    
    # Add prefix GPU IDs to pod info if provided
    if prefix_gpu_ids:
        pod_info['prefix_gpu_ids'] = prefix_gpu_ids
    
    r.hset(REGISTRY_KEY, pod_id, json.dumps(pod_info))


def update_gpu_status(gpu_id, status):
    pod_id = get_pod_id()
    now = int(time.time())
    pod_info = r.hget(REGISTRY_KEY, pod_id)
    if not pod_info:
        return
    pod_info = json.loads(pod_info)
    for gpu in pod_info['gpus']:
        if gpu['id'] == gpu_id:
            gpu['status'] = status
            gpu['last_heartbeat'] = now
    pod_info['last_heartbeat'] = now
    r.hset(REGISTRY_KEY, pod_id, json.dumps(pod_info))


def heartbeat():
    """Update the last_heartbeat timestamp for all GPUs managed by this pod."""
    pod_id = get_pod_id()
    now = int(time.time())
    pod_info = r.hget(REGISTRY_KEY, pod_id)
    if not pod_info:
        return
    pod_info = json.loads(pod_info)
    pod_info['last_heartbeat'] = now
    for gpu in pod_info['gpus']:
        gpu['last_heartbeat'] = now
    r.hset(REGISTRY_KEY, pod_id, json.dumps(pod_info))


def get_all_gpus():
    """Return a list of all registered GPUs and their status from the registry."""
    all_pods = r.hgetall(REGISTRY_KEY)
    print(f"All registered pods: {all_pods.keys()} ")
    result = []
    for pod_id, pod_info in all_pods.items():
        pod_info = json.loads(pod_info)
        service = pod_info.get('service', None)
        prefix_gpu_ids = pod_info.get('prefix_gpu_ids', [])
        
        for gpu in pod_info['gpus']:
            gpu_info = {
                'pod': pod_id.decode() if isinstance(pod_id, bytes) else pod_id,
                'node': pod_info['node'],
                'gpu_id': gpu['id'],
                'status': gpu['status'],
                'last_heartbeat': gpu['last_heartbeat'],
                'service': service
            }
            
            # Add prefix GPU ID if available
            if 'prefix_id' in gpu:
                gpu_info['prefix_gpu_id'] = gpu['prefix_id']
            
            result.append(gpu_info)
    return result


def cleanup_stale_entries():
    """Remove GPUs from the registry that have not sent a heartbeat within the stale threshold."""
    now = int(time.time())
    all_pods = r.hgetall(REGISTRY_KEY)
    for pod_id, pod_info in all_pods.items():
        pod_info = json.loads(pod_info)
        if now - pod_info.get('last_heartbeat', 0) > STALE_THRESHOLD:
            r.hdel(REGISTRY_KEY, pod_id)


def find_and_mark_idle_gpu():
    """Find an idle GPU in the registry, mark it as busy, and return its pod_id and gpu_id."""
    all_pods = r.hgetall(REGISTRY_KEY)
    now = int(time.time())
    for pod_id, pod_info in all_pods.items():
        pod_info = json.loads(pod_info)
        for gpu in pod_info['gpus']:
            if gpu['status'] == 'idle' and now - gpu['last_heartbeat'] < STALE_THRESHOLD:
                gpu['status'] = 'busy'
                gpu['last_heartbeat'] = now
                pod_info['last_heartbeat'] = now
                r.hset(REGISTRY_KEY, pod_id, json.dumps(pod_info))
                return (pod_id.decode() if isinstance(pod_id, bytes) else pod_id, gpu['id'])
    return (None, None)


def mark_gpu_idle(pod_id, gpu_id):
    """Mark the specified GPU as idle in the registry."""
    pod_info = r.hget(REGISTRY_KEY, pod_id)
    if not pod_info:
        return
    pod_info = json.loads(pod_info)
    for gpu in pod_info['gpus']:
        if gpu['id'] == gpu_id:
            gpu['status'] = 'idle'
            gpu['last_heartbeat'] = int(time.time())
    pod_info['last_heartbeat'] = int(time.time())
    r.hset(REGISTRY_KEY, pod_id, json.dumps(pod_info)) 





# {
#   "gpus": [
#     {
#       "pod": "pod-0-uuid",
#       "node": "worker-node-1",
#       "gpu_id": 0,
#       "prefix_gpu_id": 0,
#       "status": "idle",
#       "last_heartbeat": 1710000000,
#       "service": "django-backend-gpu0-service"
#     },
#     {
#       "pod": "pod-0-uuid",
#       "node": "worker-node-1",
#       "gpu_id": 1,
#       "prefix_gpu_id": 1,
#       "status": "busy",
#       "last_heartbeat": 1710000001,
#       "service": "django-backend-gpu0-service"
#     },
#     {
#       "pod": "pod-1-uuid",
#       "node": "worker-node-2",
#       "gpu_id": 0,
#       "prefix_gpu_id": 2,
#       "status": "idle",
#       "last_heartbeat": 1710000003,
#       "service": "django-backend-gpu1-service"
#     },
#     {
#       "pod": "pod-1-uuid",
#       "node": "worker-node-2",
#       "gpu_id": 1,
#       "prefix_gpu_id": 3,
#       "status": "idle",
#       "last_heartbeat": 1710000004,
#       "service": "django-backend-gpu1-service"
#     }
#     // ... and so on for other GPUs
#   ]
# }