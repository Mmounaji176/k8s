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
EXPECTED_IMAGE1="bwalidd/new-django:cuda-12.6"
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
        "02-multi-gpu-backends.yaml"
        "03-database-redis.yaml"
        "04-web-services.yaml"
        "05-streaming-services.yaml"
        "06-services.yaml"
        "08-ingress.yaml"
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
    kubectl get nodes
    
    MASTER_STATUS=$(kubectl get node $MASTER_NODE -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || echo "NotFound")
    WORKER_STATUS=$(kubectl get node $WORKER_NODE -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || echo "NotFound")
    
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
    kubectl get nodes -o custom-columns="NAME:.metadata.name,GPU-CAPACITY:.status.capacity.nvidia\.com/gpu,GPU-ALLOCATABLE:.status.allocatable.nvidia\.com/gpu"
    
    MASTER_GPUS=$(kubectl get node $MASTER_NODE -o jsonpath='{.status.allocatable.nvidia\.com/gpu}' 2>/dev/null || echo "0")
    WORKER_GPUS=$(kubectl get node $WORKER_NODE -o jsonpath='{.status.allocatable.nvidia\.com/gpu}' 2>/dev/null || echo "0")
    
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
    kubectl delete namespace $NAMESPACE --grace-period=0 --force 2>/dev/null || true
    
    # Wait for complete deletion
    print_status "info" "Waiting for namespace deletion to complete..."
    while kubectl get namespace $NAMESPACE &>/dev/null; do
        echo "  ⏳ Still deleting..."
        sleep 3
    done
    
    # Clean up any stuck resources
    kubectl delete pv,pvc --all --grace-period=0 --force 2>/dev/null || true
    
    print_status "success" "Complete cleanup finished"
    sleep 5  # Let cluster stabilize
}

force_cleanup_nuclear() {
    print_status "warning" "NUCLEAR OPTION: This will forcibly remove everything"
    read -p "Are you absolutely sure? (type 'yes'): " -r
    
    if [[ $REPLY != "yes" ]]; then
        print_status "info" "Nuclear cleanup cancelled"
        return 1
    fi
    
    # Get namespace as JSON, remove finalizers, and replace
    kubectl get namespace $NAMESPACE -o json > /tmp/ns.json 2>/dev/null
    if [ -f /tmp/ns.json ]; then
        # Remove finalizers from the JSON
        jq '.spec.finalizers = []' /tmp/ns.json | kubectl replace --raw "/api/v1/namespaces/$NAMESPACE/finalize" -f - 2>/dev/null || true
        rm -f /tmp/ns.json
    fi
    
    # Force delete everything possible
    kubectl delete all --all -n $NAMESPACE --grace-period=0 --force 2>/dev/null || true
    kubectl delete pvc --all -n $NAMESPACE --grace-period=0 --force 2>/dev/null || true
    kubectl delete namespace $NAMESPACE --grace-period=0 --force 2>/dev/null || true
    
    print_status "info" "Nuclear cleanup complete"
}

deploy_infrastructure() {
    print_section "Deploying Infrastructure (Database First)"
    
    # Step 1: Namespace and Config
    print_status "info" "Step 1: Creating namespace and configuration..."
    kubectl apply -f 01-namespace-and-config.yaml
    
    # Wait for namespace
    print_status "info" "Waiting for namespace to be ready..."
    # kubectl wait --for=condition=Ready namespace/$NAMESPACE --timeout=60s || true
    sleep 5
    
    # Step 2: Database and Redis
    print_status "info" "Step 2: Deploying database and Redis..."
    kubectl apply -f 03-database-redis.yaml

    # Wait for postgres-service to exist
    print_status "info" "Waiting for postgres-service to be created..."
    until kubectl get service postgres-service -n $NAMESPACE &> /dev/null; do
        echo "  ⏳ -----------> Still waiting for postgres-service..."
        sleep 2
    done

    # Wait for Postgres pod to be Ready
    print_status "info" "Waiting for Postgres pod to be Ready..."
    kubectl wait --for=condition=Ready pod -l app=postgresql -n $NAMESPACE --timeout=120s

    # Wait for database to be running
    print_status "info" "Waiting for database to start..."
    for i in {1..30}; do
        DB_STATUS=$(kubectl get pods -n $NAMESPACE -l app=postgresql --no-headers 2>/dev/null | awk '{print $3}' | head -1 || echo "NotFound")
        
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
    DB_POD_IP=$(kubectl get pods -n $NAMESPACE -l app=postgresql -o wide --no-headers | awk '{print $6}' | head -1)
    
    if [[ -z "$DB_POD_IP" ]]; then
        print_status "error" "Could not get database IP"
        print_status "info" "Current database pods:"
        kubectl get pods -n $NAMESPACE -l app=postgresql | sed 's/^/  /'
        exit 1
    fi
    
    print_status "success" "Database IP discovered: $DB_POD_IP"
    echo "$DB_POD_IP"
}


# Add this to your build script in the deploy_multi_gpu_backends function


deploy_multi_gpu_backends() {
    print_section "Deploying Multi-GPU Backends with Proper Migration Timing"
    
    print_status "info" "Step 1: Deploying GPU0 first for migrations..."
    
    # Deploy only GPU0 first using the correct label selector
    kubectl apply -f 02-multi-gpu-backends.yaml --selector=app=django-backend,gpu-id=gpu0
    
    # Wait for GPU0 to be ready
    print_status "info" "Waiting for GPU0 pod to be ready..."
    kubectl wait --for=condition=Ready pod -l app=django-backend,gpu-id=gpu0 -n $NAMESPACE --timeout=500s
    
    # Run migrations on GPU0
    print_status "info" "Running migrations on GPU0..."
    GPU0_POD=$(kubectl get pods -n $NAMESPACE -l app=django-backend,gpu-id=gpu0 -o jsonpath='{.items[0].metadata.name}')
    
    kubectl exec -n $NAMESPACE $GPU0_POD -- python manage.py migrate
    
    # Create superuser
    kubectl exec -n $NAMESPACE $GPU0_POD -- python manage.py shell -c "
from Api.models import CustomUser
from django.contrib.auth import get_user_model

User = get_user_model()

try:
    if not User.objects.filter(username='bluedove').exists():
        user = User.objects.create_superuser(
            username='bluedove',
            email='root@root.com',
            password='Bluedove1234'
        )
        print('✅ Superuser created successfully')
    else:
        print('ℹ️  Superuser already exists')
except Exception as e:
    print(f'❌ Error creating superuser: {e}')
"
    
    print_status "success" "GPU0 initialized with migrations complete"
    
    # Now deploy GPU1
    print_status "info" "Step 2: Deploying GPU1 (migrations already complete)..."
    kubectl apply -f 02-multi-gpu-backends.yaml --selector=app=django-backend,gpu-id=gpu1
    
    # Wait for both pods
    print_status "info" "Waiting for both GPU pods to be ready..."
    kubectl wait --for=condition=Ready pod -l app=django-backend -n $NAMESPACE --timeout=500s
    
    print_status "success" "Multi-GPU backends deployed with proper migration timing"
}

deploy_remaining_services() {
    print_section "Deploying Remaining Services"
    
    # Deploy web services
    print_status "info" "Deploying web services..."
    kubectl apply -f 04-web-services.yaml
    
    # Deploy streaming services
    print_status "info" "Deploying streaming services..."
    kubectl apply -f 05-streaming-services.yaml
    
    # Deploy Kubernetes services
    print_status "info" "Deploying Kubernetes services..."
    kubectl apply -f 06-services.yaml
    
    # Deploy autoscaling if exists
    if [[ -f "07-autoscaling-monitoring.yaml" ]]; then
        print_status "info" "Deploying autoscaling and monitoring..."
        kubectl apply -f 07-autoscaling-monitoring.yaml
    else
        print_status "info" "Autoscaling file not found, skipping"
    fi

    kubectl apply -f 08-ingress.yaml
  
    
    print_status "success" "All services deployed"
}

run_django_migrations() {
    print_section "Running Django Database Migrations"
    POD_NAME=$(kubectl get pods -n $NAMESPACE -l app=django-backend -o jsonpath='{.items[0].metadata.name}')
    if [[ -z "$POD_NAME" ]]; then
        print_status "error" "No running backend pod found for migrations"
        exit 1
    fi
    print_status "info" "Running migrations in pod: $POD_NAME"
    kubectl exec -n $NAMESPACE $POD_NAME -- python manage.py migrate
    
    # Create superuser using custom user model
    print_status "info" "Creating superuser with custom user model..."
    kubectl exec -n $NAMESPACE $POD_NAME -c django-backend -- python manage.py shell -c "
from Api.models import CustomUser
from django.contrib.auth import get_user_model

User = get_user_model()  # This gets your custom user model

if not User.objects.filter(username='bluedove').exists():
    user = User.objects.create_superuser(
        username='bluedove',
        email='root@root.com',
        password='Bluedove1234'
    )
    print('Superuser created successfully with custom user model')
else:
    print('Superuser already exists')
"
}

run_django_migrations1() {
    print_section "Running Django Database Migrations"
    
    # Wait for pods to be fully ready first
    print_status "info" "Waiting for backend pods to be ready..."
    kubectl wait --for=condition=Ready pod -l app=django-backend -n $NAMESPACE --timeout=500s
    
    # Give pods extra time to fully initialize
    sleep 30
    
    # Get the first available pod that's actually running
    local max_attempts=10
    local attempt=1
    local POD_NAME=""
    
    while [[ $attempt -le $max_attempts ]]; do
        print_status "info" "Attempt $attempt/$max_attempts: Finding available backend pod..."
        
        # Get all running backend pods
        RUNNING_PODS=$(kubectl get pods -n $NAMESPACE -l app=django-backend --field-selector=status.phase=Running -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")
        
        if [[ -n "$RUNNING_PODS" ]]; then
            # Pick the first running pod
            POD_NAME=$(echo $RUNNING_PODS | awk '{print $1}')
            
            # Verify the pod is actually ready for exec
            POD_STATUS=$(kubectl get pod $POD_NAME -n $NAMESPACE -o jsonpath='{.status.phase}' 2>/dev/null || echo "")
            POD_READY=$(kubectl get pod $POD_NAME -n $NAMESPACE -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || echo "")
            
            if [[ "$POD_STATUS" == "Running" && "$POD_READY" == "True" ]]; then
                print_status "success" "Found ready pod: $POD_NAME"
                break
            else
                print_status "warning" "Pod $POD_NAME not fully ready (Status: $POD_STATUS, Ready: $POD_READY)"
                POD_NAME=""
            fi
        else
            print_status "warning" "No running backend pods found"
        fi
        
        sleep 10
        ((attempt++))
    done
    
    if [[ -z "$POD_NAME" ]]; then
        print_status "error" "No ready backend pod found after $max_attempts attempts"
        print_status "info" "Current pod status:"
        kubectl get pods -n $NAMESPACE -l app=django-backend -o wide | sed 's/^/  /'
        exit 1
    fi
    
    # Test connection to the pod before running migrations
    print_status "info" "Testing connection to pod $POD_NAME..."
    if ! kubectl exec -n $NAMESPACE $POD_NAME -- echo "Connection test successful" &>/dev/null; then
        print_status "error" "Cannot connect to pod $POD_NAME"
        exit 1
    fi
    
    print_status "success" "Connection to $POD_NAME verified"
    
    # Run Django check first
    print_status "info" "Running Django system check..."
    if ! kubectl exec -n $NAMESPACE $POD_NAME -- python manage.py check; then
        print_status "error" "Django system check failed"
        exit 1
    fi
    
    print_status "success" "Django system check passed"
    
    # Run migrations
    print_status "info" "Running database migrations..."
    if ! kubectl exec -n $NAMESPACE $POD_NAME -- python manage.py migrate; then
        print_status "error" "Database migrations failed"
        exit 1
    fi
    
    print_status "success" "Database migrations completed"
    
    # Create superuser
    print_status "info" "Creating superuser..."
    kubectl exec -n $NAMESPACE $POD_NAME -- python manage.py shell -c "
from Api.models import CustomUser
from django.contrib.auth import get_user_model

User = get_user_model()

try:
    if not User.objects.filter(username='bluedove').exists():
        user = User.objects.create_superuser(
            username='bluedove',
            email='root@root.com',
            password='Bluedove1234'
        )
        print('✅ Superuser created successfully')
    else:
        print('ℹ️  Superuser already exists')
except Exception as e:
    print(f'❌ Error creating superuser: {e}')
    import traceback
    traceback.print_exc()
"
    
    print_status "success" "Superuser creation completed"
}


verify_multi_gpu_system() {
    print_section "Multi-GPU System Verification"
    
    print_status "info" "Final multi-GPU system status:"
    echo ""
    
    # Show all pods with nodes
    print_status "info" "All pods with node placement:"
    kubectl get pods -n $NAMESPACE -o wide | sed 's/^/  /'
    
    echo ""
    print_status "info" "Multi-GPU verification and CUDA testing:"
    GPU_PODS=$(kubectl get pods -n $NAMESPACE -o wide --no-headers | grep django-backend-gpu)
    
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
                    
                    CUDA_TEST=$(timeout 30 kubectl exec -n $NAMESPACE $POD_NAME -- python3 -c "
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
    MASTER_IP=$(kubectl get node $MASTER_NODE -o jsonpath='{.status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null || echo "localhost")
    WORKER_IP=$(kubectl get node $WORKER_NODE -o jsonpath='{.status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null || echo "localhost")
    
    # Get service ports
    FRONTEND_PORT=$(kubectl get service react-frontend-service -n $NAMESPACE -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "30080")
    BACKEND_PORT=$(kubectl get service django-backend-service -n $NAMESPACE -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "30000")
    
    echo ""
    print_status "success" "🎉 Multi-GPU Build completed successfully!"
    echo ""
    echo "🌐 Access URLs:"
    echo "  📱 Frontend:     http://${MASTER_IP}:${FRONTEND_PORT}"
    echo "  🔧 Backend API:  http://${MASTER_IP}:${BACKEND_PORT}"
    echo ""
    echo "🔍 Monitoring Commands:"
    echo "  kubectl get pods -n $NAMESPACE -o wide"
    echo "  kubectl logs -f deployment/django-backend-gpu0 -n $NAMESPACE"
    echo "  kubectl logs -f deployment/django-backend-gpu1 -n $NAMESPACE"
    echo ""
    echo "🔧 Multi-GPU Testing Commands:"
    echo "  # Test GPU0 (2x RTX 2080 Ti on Master)"
    echo "  kubectl exec -it \$(kubectl get pods -n $NAMESPACE | grep gpu0 | awk '{print \$1}') -n $NAMESPACE -- python3 -c \"import torch; print('GPUs:', torch.cuda.device_count())\""
    echo ""
    echo "  # Test GPU1 (2x RTX Super on Worker)"
    echo "  kubectl exec -it \$(kubectl get pods -n $NAMESPACE | grep gpu1 | awk '{print \$1}') -n $NAMESPACE -- python3 -c \"import torch; print('GPUs:', torch.cuda.device_count())\""
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
    # force_cleanup
    force_cleanup_nuclear
    deploy_infrastructure
    
    # Get database IP after it's running
    DB_IP=$(get_database_ip)
    
    # Create multi-GPU YAML with real database IP
    # create_multi_gpu_yaml "$DB_IP"
    
    # Deploy multi-GPU backends
    deploy_multi_gpu_backends
    # run_django_migrations
    # run_django_migrations1
    deploy_remaining_services
    # Deploy remaining services
    
    # Wait for everything to stabilize
    print_status "info" "Waiting for multi-GPU system to stabilize..."
    sleep 15  # More time for multi-GPU initialization
    
    # Verify multi-GPU system
    verify_multi_gpu_system
    
    # Show access information
    show_multi_gpu_access_info

    # DB_IP="10.244.76.56"
    # sed -i "s|PLACEHOLDER_DB_IP|$DB_IP|g" 02-multi-gpu-backends.yaml
    # sleep 120
    # kubectl apply -f 02-multi-gpu-backends.yaml
    # kubectl apply -f 04-web-services.yaml
    # kubectl apply -f 05-streaming-services.yaml  

    # kubectl apply -f 06-services.yaml

    
    print_status "success" "🎯 Multi-GPU Build Process Completed!"
    print_status "success" "🔥 Face Recognition System with 4 GPUs Total (2 per pod) is ready!"
}

# Handle interruption
trap 'print_status "error" "Multi-GPU build interrupted"; exit 1' INT TERM

# Run main function
main "$@"



