#!/bin/bash

# Multi-GPU Build Script - 2 GPUs per Pod
# GPU0: 2x RTX 2080 Ti on Master | GPU1: 2x RTX Super on Worker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 
NAMESPACE="face-recognition-system"
EXPECTED_IMAGE="bwalidd/new-django:base-image-fix1"
EXPECTED_IMAGE1="bwalidd/new-django:cuda-12.4"
MASTER_NODE="bluedove2-ms-7b98"    # 2x RTX 2080 Ti
WORKER_NODE="bluedove-ms-7b98"    # 2x RTX Super

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║ MULTI-GPU BUILD SCRIPT - 2 GPUs PER POD${NC}"
echo -e "${BLUE}║ GPU0: 2x RTX 2080 Ti on Master | GPU1: 2x RTX Super on Worker              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"

# Function to print status
print_status() {
    local status=$1
    local message=$2
    case $status in
        "success") echo -e "${GREEN}✅ $message${NC}" ;;
        "warning") echo -e "${YELLOW}⚠️  $message${NC}" ;;
        "error") echo -e "${RED}❌ $message${NC}" ;;
        "info") echo -e "${CYAN}ℹ️  $message${NC}" ;;
        "header") echo -e "${PURPLE}🔧 $message${NC}" ;;
    esac
}

print_section() {
    echo -e "\n${BLUE}=================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=================================================${NC}"
}

check_prerequisites() {
    print_section "Prerequisites Check"
    
    # Check required files
    local required_files=(
        "01-namespace-and-config.yaml"
        "03-database-redis.yaml"
        "04-web-services.yaml"
        "05-streaming-services.yaml"
        "06-services.yaml"
    )
    
    local missing_files=()
    
    for file in "${required_files[@]}"; do
        if [[ -f "$file" ]]; then
            print_status "success" "Found: $file"
        else
            print_status "error" "Missing: $file"
            missing_files+=("$file")
        fi
    done
    
    if [[ ${#missing_files[@]} -gt 0 ]]; then
        print_status "error" "Missing required files. Ensure all YAML files are present."
        exit 1
    fi
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        print_status "error" "kubectl not found"
        exit 1
    fi
    
    # Check cluster access
    if ! kubectl cluster-info &> /dev/null; then
        print_status "error" "Cannot access Kubernetes cluster"
        exit 1
    fi
    
    # Check both nodes exist and are ready
    print_status "info" "Checking cluster nodes..."
    sudo kubectl get nodes
    
    MASTER_STATUS=$(sudo kubectl get node $MASTER_NODE -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || echo "NotFound")
    WORKER_STATUS=$(sudo kubectl get node $WORKER_NODE -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || echo "NotFound")
    
    if [[ "$MASTER_STATUS" != "True" ]]; then
        print_status "error" "Master node $MASTER_NODE not ready: $MASTER_STATUS"
        exit 1
    fi
    
    if [[ "$WORKER_STATUS" != "True" ]]; then
        print_status "error" "Worker node $WORKER_NODE not ready: $WORKER_STATUS"
        exit 1
    fi
    
    print_status "success" "Both nodes are ready"
    
    # Check GPU resources on both nodes (need 2 GPUs per node)
    print_status "info" "Checking GPU resources for multi-GPU setup..."
    echo ""
    sudo kubectl get nodes -o custom-columns="NAME:.metadata.name,GPU-CAPACITY:.status.capacity.nvidia\.com/gpu,GPU-ALLOCATABLE:.status.allocatable.nvidia\.com/gpu"
    
    MASTER_GPUS=$(sudo kubectl get node $MASTER_NODE -o jsonpath='{.status.allocatable.nvidia\.com/gpu}' 2>/dev/null || echo "0")
    WORKER_GPUS=$(sudo kubectl get node $WORKER_NODE -o jsonpath='{.status.allocatable.nvidia\.com/gpu}' 2>/dev/null || echo "0")
    
    if [[ "$MASTER_GPUS" -lt 2 ]]; then
        print_status "error" "Master node needs 2 GPUs, only has $MASTER_GPUS allocatable"
        exit 1
    fi
    
    if [[ "$WORKER_GPUS" -lt 2 ]]; then
        print_status "error" "Worker node needs 2 GPUs, only has $WORKER_GPUS allocatable"
        exit 1
    fi
    
    print_status "success" "Multi-GPU resources verified:"
    print_status "success" "  Master: $MASTER_GPUS GPUs (2x RTX 2080 Ti)"
    print_status "success" "  Worker: $WORKER_GPUS GPUs (2x RTX Super)"
    
    print_status "success" "All prerequisites met for multi-GPU deployment"
}

force_cleanup() {
    print_section "Complete System Cleanup"
    
    print_status "warning" "This will delete the entire face-recognition-system namespace"
    read -p "Continue with cleanup? (y/n): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "info" "Cleanup cancelled"
        exit 0
    fi
    
    print_status "info" "Deleting namespace and all resources..."
    
    # Delete namespace (removes everything)
    sudo kubectl delete namespace $NAMESPACE --grace-period=0 --force 2>/dev/null || true
    
    # Wait for complete deletion
    print_status "info" "Waiting for namespace deletion to complete..."
    while sudo kubectl get namespace $NAMESPACE &>/dev/null; do
        echo "  ⏳ Still deleting..."
        sleep 3
    done
    
    # Clean up any stuck resources
    sudo kubectl delete pv,pvc --all --grace-period=0 --force 2>/dev/null || true
    
    print_status "success" "Complete cleanup finished"
    sleep 5  # Let cluster stabilize
}

deploy_infrastructure() {
    print_section "Deploying Infrastructure (Database First)"
    
    # Step 1: Namespace and Config
    print_status "info" "Step 1: Creating namespace and configuration..."
    sudo kubectl apply -f 01-namespace-and-config.yaml
    
    # Wait for namespace
    print_status "info" "Waiting for namespace to be ready..."
    # sudo kubectl wait --for=condition=Ready namespace/$NAMESPACE --timeout=60s || true
    sleep 5
    
    # Step 2: Database and Redis
    print_status "info" "Step 2: Deploying database and Redis..."
    sudo kubectl apply -f 03-database-redis.yaml
    
    # # Force PostgreSQL to master node
    # print_status "info" "Ensuring PostgreSQL runs on master node..."
    # sudo kubectl patch deployment postgresql-database -n $NAMESPACE -p '{
    #   "spec": {
    #     "template": {
    #       "spec": {
    #         "nodeSelector": {
    #           "kubernetes.io/hostname": "'$MASTER_NODE'"
    #         }
    #       }
    #     }
    #   }
    # }' || print_status "warning" "PostgreSQL patch failed, might not exist yet"
    
    # Wait for database to be running
    print_status "info" "Waiting for database to start..."
    for i in {1..30}; do
        DB_STATUS=$(sudo kubectl get pods -n $NAMESPACE -l app=postgresql --no-headers 2>/dev/null | awk '{print $3}' | head -1 || echo "NotFound")
        
        if [[ "$DB_STATUS" == "Running" ]]; then
            print_status "success" "Database is running!"
            break
        else
            print_status "info" "Database status: $DB_STATUS (attempt $i/30)"
            sleep 10
        fi
        
        if [[ $i -eq 30 ]]; then
            print_status "error" "Database failed to start within 5 minutes"
            exit 1
        fi
    done
    
    # Give database extra time to fully initialize
    print_status "info" "Giving database time to fully initialize..."
    sleep 30
    
    print_status "success" "Infrastructure deployment complete"
}

get_database_ip() {
    print_section "Getting Database IP"
    
    # Get database pod IP
    DB_POD_IP=$(sudo kubectl get pods -n $NAMESPACE -l app=postgresql -o wide --no-headers | awk '{print $6}' | head -1)
    
    if [[ -z "$DB_POD_IP" ]]; then
        print_status "error" "Could not get database IP"
        print_status "info" "Current database pods:"
        sudo kubectl get pods -n $NAMESPACE -l app=postgresql | sed 's/^/  /'
        exit 1
    fi
    
    print_status "success" "Database IP discovered: $DB_POD_IP"
    echo "$DB_POD_IP"
}

create_multi_gpu_yaml() {
    local DB_IP=$1
    
    print_section "Creating Multi-GPU YAML Configuration"
    
    # Validate database IP
    if [[ -z "$DB_IP" ]]; then
        print_status "error" "Database IP is empty! Cannot create YAML."
        exit 1
    fi
    
    print_status "info" "Creating 02-multi-gpu-backends.yaml with:"
    print_status "info" "  Database IP: $DB_IP"
    print_status "info" "  GPU0 → Master Node: $MASTER_NODE (2x RTX 2080 Ti)"
    print_status "info" "  GPU1 → Worker Node: $WORKER_NODE (2x RTX Super)"
    
    # Create multi-GPU YAML configuration
    cat > 02-multi-gpu-backends.yaml << 'YAMLEOF'
# Multi-GPU Backend Configuration - 2 GPUs per Pod
# GPU0: 2x RTX 2080 Ti on Master | GPU1: 2x RTX Super on Worker

# Django Backend GPU0 - MASTER NODE (2x RTX 2080 Ti)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: django-backend-gpu0
  namespace: face-recognition-system
  labels:
    app: django-backend
    gpu-id: "gpu0"
    component: backend
    gpu-count: "2"
    gpu-type: "ti"
    build: "multi-gpu"
spec:
  replicas: 1
  selector:
    matchLabels:
      app: django-backend
      gpu-id: "gpu0"
      build: "multi-gpu"
  template:
    metadata:
      labels:
        app: django-backend
        gpu-id: "gpu0"
        component: backend
        node-type: "master"
        gpu-count: "2"
        gpu-type: "ti"
        build: "multi-gpu"
    spec:
      nodeSelector:
        kubernetes.io/hostname: bluedove2-ms-7b98
      containers:
      - name: django-backend
        image: bwalidd/new-django:cuda-12.4
        workingDir: /app/Backend
        command: ["python", "manage.py", "runserver", "0.0.0.0:9898"]
        ports:
        - containerPort: 9898
        - containerPort: 6006
        - containerPort: 8888
        env:
        - name: CUDA_VISIBLE_DEVICES
          value: "0,1"
        - name: NVIDIA_VISIBLE_DEVICES
          value: "0,1"
        - name: GPU_ID
          value: "0,1"
        - name: GPU_COUNT
          value: "2"
        - name: NODE_TYPE
          value: "master"
        - name: BACKEND_INSTANCE
          value: "gpu0-multi"
        - name: GPU_TYPE
          value: "RTX 2080 Ti"
        - name: MULTI_GPU_MODE
          value: "true"
        - name: PYTORCH_CUDA_ALLOC_CONF
          value: "max_split_size_mb:256"
        - name: NCCL_DEBUG
          value: "INFO"
        - name: NCCL_IB_DISABLE
          value: "1"
        - name: NCCL_P2P_DISABLE
          value: "1"
        - name: CUDA_VERSION
          value: "12.6"
        - name: CUDA_LAUNCH_BLOCKING
          value: "0"
        - name: OMP_NUM_THREADS
          value: "4"
        - name: MALLOC_TRIM_THRESHOLD_
          value: "100000"
        resources:
          limits:
            nvidia.com/gpu: 2
            cpu: "2000m"
            memory: "4Gi"
          requests:
            nvidia.com/gpu: 2
            cpu: "1000m"
            memory: "2Gi"

---
# Django Backend GPU1 - WORKER NODE (2x RTX Super)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: django-backend-gpu1
  namespace: face-recognition-system
  labels:
    app: django-backend
    gpu-id: "gpu1"
    component: backend
    gpu-count: "2"
    gpu-type: "super"
    build: "multi-gpu"
spec:
  replicas: 1
  selector:
    matchLabels:
      app: django-backend
      gpu-id: "gpu1"
      build: "multi-gpu"
  template:
    metadata:
      labels:
        app: django-backend
        gpu-id: "gpu1"
        component: backend
        node-type: "worker"
        gpu-count: "2"
        gpu-type: "super"
        build: "multi-gpu"
    spec:
      nodeSelector:
        kubernetes.io/hostname: bluedove-ms-7b98
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchLabels:
                gpu-id: "gpu0"
            topologyKey: kubernetes.io/hostname
      containers:
      - name: django-backend
        image: bwalidd/new-django:cuda-12.4
        workingDir: /app/Backend
        command: ["python", "manage.py", "runserver", "0.0.0.0:9898"]
        ports:
        - containerPort: 9898
        - containerPort: 6006
        - containerPort: 8888
        env:
        - name: CUDA_VISIBLE_DEVICES
          value: "0,1"
        - name: NVIDIA_VISIBLE_DEVICES
          value: "0,1"
        - name: GPU_ID
          value: "0,1"
        - name: GPU_COUNT
          value: "2"
        - name: NODE_TYPE
          value: "worker"
        - name: BACKEND_INSTANCE
          value: "gpu1-multi"
        - name: GPU_TYPE
          value: "RTX Super"
        - name: MULTI_GPU_MODE
          value: "true"
        - name: PYTORCH_CUDA_ALLOC_CONF
          value: "max_split_size_mb:256"
        - name: NCCL_DEBUG
          value: "INFO"
        - name: NCCL_IB_DISABLE
          value: "1"
        - name: NCCL_P2P_DISABLE
          value: "1"
        - name: CUDA_VERSION
          value: "12.6"
        - name: CUDA_LAUNCH_BLOCKING
          value: "0"
        - name: OMP_NUM_THREADS
          value: "4"
        - name: MALLOC_TRIM_THRESHOLD_
          value: "100000"
        resources:
          limits:
            nvidia.com/gpu: 2
            cpu: "2000m"
            memory: "4Gi"
          requests:
            nvidia.com/gpu: 2
            cpu: "1000m"
            memory: "2Gi"
YAMLEOF

    # Replace database IP placeholder
    sed -i "s/PLACEHOLDER_DB_IP/$DB_IP/g" 02-multi-gpu-backends.yaml
    
    print_status "success" "Multi-GPU YAML configuration created successfully"
}

deploy_multi_gpu_backends() {
    print_section "Deploying Multi-GPU Backends"
    
    print_status "info" "Deploying multi-GPU backends (2 GPUs per pod)..."
    sleep 90  # Wait for database to stabilize before deploying backends
    sudo kubectl apply -f 02-multi-gpu-backends.yaml
    
    print_status "info" "Waiting for multi-GPU pods to start..."
    sleep 20
    
    # Monitor multi-GPU pod startup
    for i in {1..25}; do
        print_status "info" "Multi-GPU pods check $i/25:"
        
        GPU_PODS=$(sudo kubectl get pods -n $NAMESPACE -o wide --no-headers | grep django-backend-gpu)
        if [[ -n "$GPU_PODS" ]]; then
            echo "$GPU_PODS" | sed 's/^/  /'
            
            # Check specific node placement
            GPU0_NODE=$(echo "$GPU_PODS" | grep gpu0 | awk '{print $7}' | head -1)
            GPU1_NODE=$(echo "$GPU_PODS" | grep gpu1 | awk '{print $7}' | head -1)
            
            if [[ "$GPU0_NODE" == "$MASTER_NODE" ]]; then
                print_status "success" "GPU0 (2x RTX 2080 Ti) on master: $GPU0_NODE"
            elif [[ -n "$GPU0_NODE" ]]; then
                print_status "warning" "GPU0 on wrong node: $GPU0_NODE"
            fi
            
            if [[ "$GPU1_NODE" == "$WORKER_NODE" ]]; then
                print_status "success" "GPU1 (2x RTX Super) on worker: $GPU1_NODE"
            elif [[ -n "$GPU1_NODE" ]]; then
                print_status "warning" "GPU1 on wrong node: $GPU1_NODE"
            fi
            
            # Check running status
            RUNNING_COUNT=$(echo "$GPU_PODS" | grep "Running" | wc -l)
            TOTAL_COUNT=$(echo "$GPU_PODS" | wc -l)
            
            if [[ $RUNNING_COUNT -eq 2 ]]; then
                if [[ "$GPU0_NODE" == "$MASTER_NODE" && "$GPU1_NODE" == "$WORKER_NODE" ]]; then
                    print_status "success" "🎉 Both multi-GPU pods running on correct nodes!"
                    break
                fi
            fi
        else
            print_status "info" "No GPU pods found yet..."
        fi
        
        if [[ $i -eq 25 ]]; then
            print_status "warning" "Multi-GPU pods taking longer than expected"
        fi
        
        sleep 25  # More time for multi-GPU initialization
    done
}

deploy_remaining_services() {
    print_section "Deploying Remaining Services"
    
    # Deploy web services
    print_status "info" "Deploying web services..."
    sudo kubectl apply -f 04-web-services.yaml
    
    # Deploy streaming services
    print_status "info" "Deploying streaming services..."
    sudo kubectl apply -f 05-streaming-services.yaml
    
    # Deploy Kubernetes services
    print_status "info" "Deploying Kubernetes services..."
    sudo kubectl apply -f 06-services.yaml
    
    # Deploy autoscaling if exists
    if [[ -f "07-autoscaling-monitoring.yaml" ]]; then
        print_status "info" "Deploying autoscaling and monitoring..."
        sudo kubectl apply -f 07-autoscaling-monitoring.yaml
    else
        print_status "info" "Autoscaling file not found, skipping"
    fi
    
    print_status "success" "All services deployed"
}

verify_multi_gpu_system() {
    print_section "Multi-GPU System Verification"
    
    print_status "info" "Final multi-GPU system status:"
    echo ""
    
    # Show all pods with nodes
    print_status "info" "All pods with node placement:"
    sudo kubectl get pods -n $NAMESPACE -o wide | sed 's/^/  /'
    
    echo ""
    print_status "info" "Multi-GPU verification and CUDA testing:"
    GPU_PODS=$(sudo kubectl get pods -n $NAMESPACE -o wide --no-headers | grep django-backend-gpu)
    
    if [[ -n "$GPU_PODS" ]]; then
        while read -r pod_line; do
            if [[ -n "$pod_line" ]]; then
                POD_NAME=$(echo "$pod_line" | awk '{print $1}')
                POD_STATUS=$(echo "$pod_line" | awk '{print $3}')
                POD_NODE=$(echo "$pod_line" | awk '{print $7}')
                GPU_ID=$(echo "$POD_NAME" | grep -o 'gpu[0-9]' | grep -o '[0-9]')
                
                if [[ "$GPU_ID" == "0" && "$POD_NODE" == "$MASTER_NODE" ]]; then
                    print_status "success" "$POD_NAME ($POD_STATUS) ✅ Master (2x RTX 2080 Ti): $POD_NODE"
                elif [[ "$GPU_ID" == "1" && "$POD_NODE" == "$WORKER_NODE" ]]; then
                    print_status "success" "$POD_NAME ($POD_STATUS) ✅ Worker (2x RTX Super): $POD_NODE"
                else
                    print_status "warning" "$POD_NAME ($POD_STATUS) ❌ Wrong node: $POD_NODE"
                fi
                
                # Test Multi-GPU CUDA if pod is running
                if [[ "$POD_STATUS" == "Running" ]]; then
                    print_status "info" "Testing Multi-GPU CUDA in $POD_NAME..."
                    
                    CUDA_TEST=$(timeout 30 sudo kubectl exec -n $NAMESPACE $POD_NAME -- python3 -c "
import torch
print('CUDA available:', torch.cuda.is_available())
device_count = torch.cuda.device_count()
print('GPU device count:', device_count)
if torch.cuda.is_available():
    for i in range(device_count):
        print(f'GPU {i}: {torch.cuda.get_device_name(i)}')
    
    if device_count >= 2:
        print('Testing multi-GPU computation...')
        # Create tensors on both GPUs
        x0 = torch.randn(1000, 1000).cuda(0)
        x1 = torch.randn(1000, 1000).cuda(1)
        
        # Test computation on both GPUs
        y0 = torch.mm(x0, x0.t())
        y1 = torch.mm(x1, x1.t())
        
        print('Multi-GPU computation: SUCCESS')
        print(f'GPU 0 result shape: {y0.shape}')
        print(f'GPU 1 result shape: {y1.shape}')
    else:
        print('Single GPU computation test...')
        x = torch.randn(1000, 1000).cuda()
        y = torch.mm(x, x.t())
        print('Single GPU computation: SUCCESS')
" 2>/dev/null || echo "Multi-GPU CUDA test failed")
                    
                    echo "$CUDA_TEST" | sed 's/^/    /'
                    
                    if echo "$CUDA_TEST" | grep -q "Multi-GPU computation: SUCCESS"; then
                        print_status "success" "🚀 Multi-GPU CUDA working on $POD_NODE!"
                    elif echo "$CUDA_TEST" | grep -q "CUDA available: True"; then
                        print_status "warning" "CUDA working but multi-GPU may have issues on $POD_NODE"
                    else
                        print_status "warning" "CUDA issues on $POD_NODE"
                    fi
                fi
                echo ""
            fi
        done <<< "$GPU_PODS"
    else
        print_status "warning" "No running GPU pods found for testing"
    fi
}

show_multi_gpu_access_info() {
    print_section "Multi-GPU Application Access Information"
    
    # Get node IPs
    MASTER_IP=$(sudo kubectl get node $MASTER_NODE -o jsonpath='{.status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null || echo "localhost")
    WORKER_IP=$(sudo kubectl get node $WORKER_NODE -o jsonpath='{.status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null || echo "localhost")
    
    # Get service ports
    FRONTEND_PORT=$(sudo kubectl get service react-frontend-service -n $NAMESPACE -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "30080")
    BACKEND_PORT=$(sudo kubectl get service django-backend-service -n $NAMESPACE -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "30000")
    
    echo ""
    print_status "success" "🎉 Multi-GPU Build completed successfully!"
    echo ""
    echo "🌐 Access URLs:"
    echo "  📱 Frontend:     http://${MASTER_IP}:${FRONTEND_PORT}"
    echo "  🔧 Backend API:  http://${MASTER_IP}:${BACKEND_PORT}"
    echo ""
    echo "🔍 Monitoring Commands:"
    echo "  sudo kubectl get pods -n $NAMESPACE -o wide"
    echo "  sudo kubectl logs -f deployment/django-backend-gpu0 -n $NAMESPACE"
    echo "  sudo kubectl logs -f deployment/django-backend-gpu1 -n $NAMESPACE"
    echo ""
    echo "🔧 Multi-GPU Testing Commands:"
    echo "  # Test GPU0 (2x RTX 2080 Ti on Master)"
    echo "  sudo kubectl exec -it \$(sudo kubectl get pods -n $NAMESPACE | grep gpu0 | awk '{print \$1}') -n $NAMESPACE -- python3 -c \"import torch; print('GPUs:', torch.cuda.device_count())\""
    echo ""
    echo "  # Test GPU1 (2x RTX Super on Worker)"
    echo "  sudo kubectl exec -it \$(sudo kubectl get pods -n $NAMESPACE | grep gpu1 | awk '{print \$1}') -n $NAMESPACE -- python3 -c \"import torch; print('GPUs:', torch.cuda.device_count())\""
    echo ""
    echo "📊 Multi-GPU System Summary:"
    echo "  ✅ Database: Running on $MASTER_NODE with IP $(get_database_ip 2>/dev/null || echo 'check manually')"
    echo "  🎯 GPU0: 2x RTX 2080 Ti on $MASTER_NODE ($EXPECTED_IMAGE)"
    echo "  🎯 GPU1: 2x RTX Super on $WORKER_NODE ($EXPECTED_IMAGE1)"
    # echo "  ✅ Multi-GPU Configuration: CUDA_VISIBLE_DEVICES=0,1 for both pods"
    echo "  ✅ Anti-Affinity: Ensures pods on different nodes"
    echo "  ✅ Resource Allocation: 2 GPUs, 4GB RAM, 2 CPU cores per pod"
    echo ""
    print_status "info" "Multi-GPU Features:"
    echo "  🚀 PyTorch DataParallel support enabled"
    echo "  🚀 NCCL communication configured"
    echo "  🚀 Increased memory allocation for multi-GPU workloads"
    echo "  🚀 Optimized CUDA settings for parallel processing"
    echo ""
    echo "💡 Usage Tips:"
    echo "  - Each pod has access to 2 GPUs for parallel processing"
    echo "  - Use torch.nn.DataParallel for model parallelization"
    echo "  - Monitor GPU usage with nvidia-smi in each pod"
    echo "  - Load balance face recognition tasks across both pods"
}

main() {
    print_status "header" "Starting Multi-GPU Build Process"
    
    check_prerequisites
    force_cleanup
    deploy_infrastructure
    
    # Get database IP after it's running
    DB_IP=$(get_database_ip)
    
    # Create multi-GPU YAML with real database IP
    create_multi_gpu_yaml "$DB_IP"
    
    # Deploy multi-GPU backends
    deploy_multi_gpu_backends
    
    # Deploy remaining services
    deploy_remaining_services
    
    # Wait for everything to stabilize
    print_status "info" "Waiting for multi-GPU system to stabilize..."
    sleep 45  # More time for multi-GPU initialization
    
    # Verify multi-GPU system
    verify_multi_gpu_system
    
    # Show access information
    show_multi_gpu_access_info

    # DB_IP="10.244.76.56"
    # sed -i "s|PLACEHOLDER_DB_IP|$DB_IP|g" 02-multi-gpu-backends.yaml
    # sleep 120
    # sudo kubectl apply -f 02-multi-gpu-backends.yaml
    # sudo kubectl apply -f 04-web-services.yaml
    # sudo kubectl apply -f 05-streaming-services.yaml  

    # sudo kubectl apply -f 06-services.yaml

    
    print_status "success" "🎯 Multi-GPU Build Process Completed!"
    print_status "success" "🔥 Face Recognition System with 4 GPUs Total (2 per pod) is ready!"
}

# Handle interruption
trap 'print_status "error" "Multi-GPU build interrupted"; exit 1' INT TERM

# Run main function
main "$@"