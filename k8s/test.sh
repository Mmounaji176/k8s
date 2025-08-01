#!/bin/bash

# Face Recognition System Database Connectivity Checker
# This script checks connectivity and database access for GPU pods

set -e

NAMESPACE="face-recognition-system"
DB_POD="postgresql-database-7b956fd868-9jvmz"
GPU0_POD="django-backend-gpu0-86c94b778d-ksw2r"
GPU1_POD="django-backend-gpu1-745fbbddf7-ptkh4"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Face Recognition System Database Connectivity Checker ===${NC}"
echo "Namespace: $NAMESPACE"
echo "Database Pod: $DB_POD"
echo "GPU0 Pod: $GPU0_POD"
echo "GPU1 Pod: $GPU1_POD"
echo ""

# Function to run command and show result
run_check() {
    local description="$1"
    local command="$2"
    local expected_success="$3"
    
    echo -e "${YELLOW}Checking: $description${NC}"
    echo "Command: $command"
    
    if eval "$command" >/dev/null 2>&1; then
        if [ "$expected_success" = "true" ]; then
            echo -e "${GREEN}✓ PASS${NC}"
        else
            echo -e "${RED}✗ UNEXPECTED SUCCESS${NC}"
        fi
    else
        if [ "$expected_success" = "false" ]; then
            echo -e "${GREEN}✓ EXPECTED FAILURE${NC}"
        else
            echo -e "${RED}✗ FAIL${NC}"
        fi
    fi
    echo ""
}

# Function to get pod info
get_pod_info() {
    local pod_name="$1"
    echo -e "${BLUE}=== Pod Information: $pod_name ===${NC}"
    
    echo "Pod Status:"
    kubectl get pod $pod_name -n $NAMESPACE -o wide
    echo ""
    
    echo "Pod IP and Node:"
    kubectl get pod $pod_name -n $NAMESPACE -o jsonpath='{.status.podIP} (Node: {.spec.nodeName})'
    echo -e "\n"
    
    echo "Environment Variables (database related):"
    kubectl exec $pod_name -n $NAMESPACE -- env | grep -E "(DB|DATABASE|POSTGRES|REDIS)" || echo "No database env vars found"
    echo ""
}

# Function to test database connectivity from pod
test_db_connectivity() {
    local pod_name="$1"
    local pod_label="$2"
    
    echo -e "${BLUE}=== Database Connectivity Test: $pod_label ===${NC}"
    
    # Test network connectivity to database pod
    echo "Testing network connectivity to database pod..."
    DB_IP=$(kubectl get pod $DB_POD -n $NAMESPACE -o jsonpath='{.status.podIP}')
    echo "Database Pod IP: $DB_IP"
    
    # Ping test
    echo "Ping test:"
    kubectl exec $pod_name -n $NAMESPACE -- ping -c 3 $DB_IP 2>/dev/null && echo -e "${GREEN}✓ Ping successful${NC}" || echo -e "${RED}✗ Ping failed${NC}"
    
    # Port connectivity test (PostgreSQL default port 5432)
    echo "Port 5432 connectivity test:"
    kubectl exec $pod_name -n $NAMESPACE -- nc -zv $DB_IP 5432 2>/dev/null && echo -e "${GREEN}✓ Port 5432 accessible${NC}" || echo -e "${RED}✗ Port 5432 not accessible${NC}"
    
    # DNS resolution test
    echo "DNS resolution test:"
    kubectl exec $pod_name -n $NAMESPACE -- nslookup postgresql-database 2>/dev/null && echo -e "${GREEN}✓ DNS resolution successful${NC}" || echo -e "${RED}✗ DNS resolution failed${NC}"
    
    # Test database connection if possible
    echo "Database connection test:"
    kubectl exec $pod_name -n $NAMESPACE -- python -c "
import os
import psycopg2
try:
    # Try to get database credentials from environment
    db_host = os.environ.get('DB_HOST', 'postgresql-database')
    db_port = os.environ.get('DB_PORT', '5432')
    db_name = os.environ.get('DB_NAME', 'postgres')
    db_user = os.environ.get('DB_USER', 'postgres')
    db_password = os.environ.get('DB_PASSWORD', '')
    
    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password
    )
    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    version = cursor.fetchone()
    print('✓ Database connection successful')
    print(f'PostgreSQL version: {version[0][:50]}...')
    cursor.close()
    conn.close()
except Exception as e:
    print(f'✗ Database connection failed: {e}')
" 2>/dev/null || echo -e "${RED}✗ Python/psycopg2 test failed${NC}"
    
    echo ""
}

# Function to compare configurations
compare_pod_configs() {
    echo -e "${BLUE}=== Configuration Comparison ===${NC}"
    
    echo "Comparing environment variables:"
    echo "GPU0 env vars:"
    kubectl exec $GPU0_POD -n $NAMESPACE -- env | grep -E "(DB|DATABASE|POSTGRES)" | sort > /tmp/gpu0_env.txt
    echo "GPU1 env vars:"
    kubectl exec $GPU1_POD -n $NAMESPACE -- env | grep -E "(DB|DATABASE|POSTGRES)" | sort > /tmp/gpu1_env.txt
    
    if diff /tmp/gpu0_env.txt /tmp/gpu1_env.txt > /dev/null; then
        echo -e "${GREEN}✓ Environment variables are identical${NC}"
    else
        echo -e "${RED}✗ Environment variables differ:${NC}"
        diff /tmp/gpu0_env.txt /tmp/gpu1_env.txt || true
    fi
    
    echo ""
    echo "Comparing network policies and service access..."
    
    # Check if pods can reach each other
    GPU0_IP=$(kubectl get pod $GPU0_POD -n $NAMESPACE -o jsonpath='{.status.podIP}')
    GPU1_IP=$(kubectl get pod $GPU1_POD -n $NAMESPACE -o jsonpath='{.status.podIP}')
    
    echo "GPU0 can reach GPU1:"
    kubectl exec $GPU0_POD -n $NAMESPACE -- ping -c 2 $GPU1_IP >/dev/null 2>&1 && echo -e "${GREEN}✓ Yes${NC}" || echo -e "${RED}✗ No${NC}"
    
    echo "GPU1 can reach GPU0:"
    kubectl exec $GPU1_POD -n $NAMESPACE -- ping -c 2 $GPU0_IP >/dev/null 2>&1 && echo -e "${GREEN}✓ Yes${NC}" || echo -e "${RED}✗ No${NC}"
    
    echo ""
}

# Function to check resource constraints
check_resources() {
    echo -e "${BLUE}=== Resource Usage Check ===${NC}"
    
    for pod in $GPU0_POD $GPU1_POD; do
        echo "Resource usage for $pod:"
        kubectl top pod $pod -n $NAMESPACE 2>/dev/null || echo "kubectl top not available"
        
        echo "Resource limits and requests:"
        kubectl describe pod $pod -n $NAMESPACE | grep -A 10 "Limits\|Requests" || echo "No resource limits found"
        echo ""
    done
}

# Function to check logs for errors
check_logs() {
    echo -e "${BLUE}=== Recent Logs Check ===${NC}"
    
    echo "GPU0 recent logs (last 20 lines):"
    kubectl logs $GPU0_POD -n $NAMESPACE --tail=20 | grep -i -E "(error|exception|fail|database|connection)" || echo "No database-related errors found"
    echo ""
    
    echo "GPU1 recent logs (last 20 lines):"
    kubectl logs $GPU1_POD -n $NAMESPACE --tail=20 | grep -i -E "(error|exception|fail|database|connection)" || echo "No database-related errors found"
    echo ""
    
    echo "Database logs (last 20 lines):"
    kubectl logs $DB_POD -n $NAMESPACE --tail=20 | grep -i -E "(error|exception|fail|connection|authentication)" || echo "No connection-related errors found"
    echo ""
}

# Function to run Django-specific database tests
run_django_tests() {
    echo -e "${BLUE}=== Django Database Tests ===${NC}"
    
    for pod in $GPU0_POD $GPU1_POD; do
        pod_label=$(echo $pod | grep -o "gpu[0-9]")
        echo "Testing Django database connectivity for $pod_label:"
        
        kubectl exec $pod -n $NAMESPACE -- python manage.py dbshell --command="SELECT 1;" 2>/dev/null && \
            echo -e "${GREEN}✓ Django database shell works${NC}" || \
            echo -e "${RED}✗ Django database shell failed${NC}"
        
        kubectl exec $pod -n $NAMESPACE -- python manage.py check --database=default 2>/dev/null && \
            echo -e "${GREEN}✓ Django database check passed${NC}" || \
            echo -e "${RED}✗ Django database check failed${NC}"
        
        echo ""
    done
}

# Main execution
main() {
    echo -e "${BLUE}Starting comprehensive database connectivity check...${NC}\n"
    
    # Check if namespace and pods exist
    run_check "Namespace exists" "kubectl get namespace $NAMESPACE" "true"
    run_check "Database pod exists" "kubectl get pod $DB_POD -n $NAMESPACE" "true"
    run_check "GPU0 pod exists" "kubectl get pod $GPU0_POD -n $NAMESPACE" "true"
    run_check "GPU1 pod exists" "kubectl get pod $GPU1_POD -n $NAMESPACE" "true"
    
    # Get pod information
    get_pod_info $DB_POD
    get_pod_info $GPU0_POD
    get_pod_info $GPU1_POD
    
    # Test database connectivity
    test_db_connectivity $GPU0_POD "GPU0"
    test_db_connectivity $GPU1_POD "GPU1"
    
    # Compare configurations
    compare_pod_configs
    
    # Check resources
    check_resources
    
    # Check logs
    check_logs
    
    # Run Django-specific tests
    run_django_tests
    
    echo -e "${BLUE}=== Summary ===${NC}"
    echo "1. Check the environment variables comparison above"
    echo "2. Verify network connectivity results"
    echo "3. Review resource usage and limits"
    echo "4. Examine logs for specific error messages"
    echo "5. If Django tests fail, check database migrations and settings"
    echo ""
    echo -e "${YELLOW}Next steps if issues are found:${NC}"
    echo "- If env vars differ: Update deployment configs"
    echo "- If network fails: Check NetworkPolicies and Services"
    echo "- If resources are maxed: Increase limits"
    echo "- If Django tests fail: Check DATABASE_URL and migrations"
    
    # Cleanup
    rm -f /tmp/gpu0_env.txt /tmp/gpu1_env.txt
}

# Run the main function
main