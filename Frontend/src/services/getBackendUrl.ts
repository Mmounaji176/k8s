// export function getBackendUrlForGpuId(gpu_id: number | string) {
//   // Use Kubernetes DNS to reach the backend service by GPU ID
//   return `http://django-backend-gpu-${gpu_id}-service:9898`;
//   // For in-cluster DNS:
//   // return `http://django-backend-gpu-${gpu_id}-service.face-recognition-system.svc.cluster.local:9898`;
// }

// export function getRandomBackendUrl() {
//   // Use a generic backend service for CPU/general tasks
//   // return "http://django-backend-gpu-0-service:9898";
//   return "http://localhost:9898"; // For local development
// }


export function getBackendUrlForGpuId(gpu_id: number | string) {
  return `/gpu${gpu_id}`;
}

export function getRandomBackendUrl() {
  return "";
}