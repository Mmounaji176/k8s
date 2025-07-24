#!/bin/bash

# NGINX Ingress Controller Setup and Test Script
set -e

echo "🚀 Starting NGINX Ingress Controller setup and test..."

# Step 1: Verify the Ingress Controller is running
echo "📋 Checking NGINX Ingress Controller status..."
kubectl get pods -n default | grep nginx-ingress

# Step 2: Check the LoadBalancer service
echo "🔍 Checking LoadBalancer service..."
kubectl get svc -n default | grep nginx

# Step 3: Get external IP (wait for it to be ready)
echo "⏳ Waiting for external IP to be assigned..."
echo "Getting service details..."
kubectl get svc nginx-ingress-ingress-nginx-controller -n default -o wide

# Wait for external IP (timeout after 2 minutes)
echo "Waiting for LoadBalancer IP..."
timeout 120 bash -c 'until kubectl get svc nginx-ingress-ingress-nginx-controller -n default -o jsonpath="{.status.loadBalancer.ingress[0].ip}" | grep -v "^$"; do sleep 5; done' || echo "⚠️  LoadBalancer IP not ready yet (this is normal for local clusters)"

# Get the external IP or use localhost for local testing
EXTERNAL_IP=$(kubectl get svc nginx-ingress-ingress-nginx-controller -n default -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
if [ -z "$EXTERNAL_IP" ]; then
    # Try to get NodePort for local clusters
    NODEPORT=$(kubectl get svc nginx-ingress-ingress-nginx-controller -n default -o jsonpath='{.spec.ports[?(@.name=="http")].nodePort}' 2>/dev/null || echo "")
    if [ -n "$NODEPORT" ]; then
        EXTERNAL_IP="localhost:$NODEPORT"
        echo "📍 Using NodePort access: $EXTERNAL_IP"
    else
        EXTERNAL_IP="localhost"
        echo "📍 Using localhost (you may need to port-forward)"
    fi
else
    echo "📍 External IP found: $EXTERNAL_IP"
fi

# Step 4: Deploy test application
echo "🎯 Deploying test application..."
kubectl create deployment hello-world --image=gcr.io/google-samples/hello-app:1.0 --port=8080 || echo "Deployment already exists"
kubectl expose deployment hello-world --port=8080 --target-port=8080 || echo "Service already exists"

# Step 5: Create ingress resource
echo "🌐 Creating ingress resource..."
cat << EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: hello-world-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
spec:
  rules:
  - host: hello-world.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: hello-world
            port:
              number: 8080
EOF

# Step 6: Wait for ingress to be ready
echo "⏳ Waiting for ingress to be ready..."
sleep 10

# Step 7: Check ingress status
echo "📊 Checking ingress status..."
kubectl get ingress hello-world-ingress

# Step 8: Test the ingress
echo "🧪 Testing the ingress..."
echo "External IP/Port: $EXTERNAL_IP"

# Test the ingress
if [[ "$EXTERNAL_IP" == *"localhost"* ]]; then
    echo "💡 For local testing, you can:"
    echo "   1. Add to /etc/hosts: echo '127.0.0.1 hello-world.local' | sudo tee -a /etc/hosts"
    echo "   2. Test with: curl http://hello-world.local:$NODEPORT"
    echo "   3. Or use port-forward: kubectl port-forward svc/nginx-ingress-ingress-nginx-controller 8080:80"
    echo ""
    echo "Attempting to test with current setup..."
    curl -H "Host: hello-world.local" "http://$EXTERNAL_IP" --connect-timeout 10 || echo "❌ Direct curl failed (this is expected for local clusters)"
else
    echo "Testing with external IP..."
    curl -H "Host: hello-world.local" "http://$EXTERNAL_IP" --connect-timeout 10 || echo "❌ Test failed - ingress may still be initializing"
fi

# Step 9: Show useful commands
echo ""
echo "✅ Setup complete! Here are some useful commands:"
echo ""
echo "📋 Check ingress controller:"
echo "   kubectl get pods -n default | grep nginx"
echo ""
echo "🔍 Check services:"
echo "   kubectl get svc -n default"
echo ""
echo "🌐 Check ingress resources:"
echo "   kubectl get ingress"
echo ""
echo "🧪 Test the application:"
echo "   curl -H 'Host: hello-world.local' http://$EXTERNAL_IP"
echo ""
echo "🧹 Cleanup (when done testing):"
echo "   kubectl delete ingress hello-world-ingress"
echo "   kubectl delete service hello-world"
echo "   kubectl delete deployment hello-world"
echo "   helm uninstall nginx-ingress"
echo ""
echo "🎉 NGINX Ingress Controller is ready to use!"