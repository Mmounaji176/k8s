#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    local status=$1
    local message=$2
    case $status in
        "success") echo -e "${GREEN}✅ $message${NC}" ;;
        "warning") echo -e "${YELLOW}⚠️  $message${NC}" ;;
        "error") echo -e "${RED}❌ $message${NC}" ;;
        "info") echo -e "${BLUE}ℹ️  $message${NC}" ;;
    esac
}

# Function to wait for pods to be ready
wait_for_pods() {
    local namespace=$1
    local label=$2
    local count=$3
    local timeout=$4
    
    print_status "info" "Waiting for $count pods with label $label to be ready..."
    
    for i in $(seq 1 $timeout); do
        ready_pods=$(kubectl get pods -n $namespace -l $label -o jsonpath='{.items[*].status.containerStatuses[*].ready}' | tr ' ' '\n' | grep -c "true")
        
        if [ "$ready_pods" -eq "$count" ]; then
            print_status "success" "All pods are ready!"
            return 0
        fi
        
        print_status "info" "Ready pods: $ready_pods/$count (attempt $i/$timeout)"
        sleep 5
    done
    
    print_status "error" "Timeout waiting for pods to be ready"
    return 1
}

# Function to get PostgreSQL pod IP
get_postgres_ip() {
    local namespace=$1
    local postgres_ip=$(kubectl get pods -n $namespace -l app=postgresql -o jsonpath='{.items[0].status.podIP}')
    echo $postgres_ip
}

# Function to run migrations
run_migrations() {
    local namespace=$1
    local pod_name=$2
    
    print_status "info" "Running database migrations..."
    
    # Run migrations
    sudo kubectl exec -n $namespace $pod_name -- python manage.py makemigrations
    sudo kubectl exec -n $namespace $pod_name -- python manage.py migrate
    
    # Create superuser if it doesn't exist
    print_status "info" "Creating superuser (if not exists)..."
    sudo kubectl exec -n $namespace $pod_name -- python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('bluedove', 'admin@example.com', 'bluedove1234')
EOF
    
    print_status "success" "Database migrations completed"
}

# Main deployment process
print_status "info" "Starting Kubernetes deployment..."

# 1. Create namespace and config
print_status "info" "Step 1: Creating namespace and configuration..."
sudo kubectl apply -f 01-namespace-and-config.yaml
sleep 5

# 2. Deploy database and Redis
print_status "info" "Step 2: Deploying database and Redis..."
sudo kubectl apply -f 03-database-redis.yaml
wait_for_pods "face-recognition-system" "app=postgresql" 1 30
wait_for_pods "face-recognition-system" "app=redis" 1 30

# Get PostgreSQL IP and update host IP in multi-GPU backends
print_status "info" "Updating host IP in multi-GPU backends configuration..."
POSTGRES_IP=$(get_postgres_ip "face-recognition-system")
if [ -z "$POSTGRES_IP" ]; then
    print_status "error" "Failed to get PostgreSQL pod IP"
    exit 1
fi

# Update host IP in 02-multi-gpu-backends.yaml
sed -i.bak "s/kubernetes.io\/hostname: .*/kubernetes.io\/hostname: $POSTGRES_IP/g" 02-multi-gpu-backends.yaml
print_status "success" "Updated host IP to $POSTGRES_IP in multi-GPU backends configuration"

# 3. Deploy multi-GPU backends
print_status "info" "Step 3: Deploying multi-GPU backends..."
sudo kubectl apply -f 02-multi-gpu-backends.yaml
wait_for_pods "face-recognition-system" "app=django-backend" 2 60

# Run migrations on the master node (GPU0)
GPU0_POD=$(kubectl get pods -n face-recognition-system -l app=django-backend,gpu-id=gpu0 -o jsonpath='{.items[0].metadata.name}')
run_migrations "face-recognition-system" "$GPU0_POD"

# 4. Deploy web services
print_status "info" "Step 4: Deploying web services..."
sudo kubectl apply -f 04-web-services.yaml
wait_for_pods "face-recognition-system" "app=react-frontend" 1 30

# 5. Deploy streaming services
print_status "info" "Step 5: Deploying streaming services..."
sudo kubectl apply -f 05-streaming-services.yaml
wait_for_pods "face-recognition-system" "app=mediamtx" 1 30

# 6. Deploy Kubernetes services
print_status "info" "Step 6: Deploying Kubernetes services..."
sudo kubectl apply -f 06-services.yaml

# 7. Verify deployment
print_status "info" "Step 7: Verifying deployment..."
sudo kubectl get pods -n face-recognition-system -o wide

# 8. Show access information
print_status "info" "Step 8: Access Information"
echo "Frontend: http://localhost:30999"
echo ""
print_status "info" "Backend Access Points:"
echo "1. Direct Access (for debugging):"
echo "   - Master Node (GPU0): http://localhost:30801"
echo "   - Worker Node (GPU1): http://localhost:30802"
echo ""
echo "2. Load Balanced Access (recommended for production):"
echo "   - Backend Load Balancer: http://localhost:30898"
echo ""
print_status "info" "Admin Access Information"
echo "Recommended Admin URL: http://localhost:30898/admin"
echo "Username: bluedove"
echo "Password: Bluedove1234"
echo ""
print_status "info" "Note: If you need to run migrations manually, use:"
echo "kubectl exec -n face-recognition-system <pod-name> -- python manage.py migrate"

print_status "success" "Deployment completed successfully!" 