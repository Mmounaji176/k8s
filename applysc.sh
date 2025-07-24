#!/bin/bash

# This script adds namespace: face-recognition-app to all Kubernetes manifest files
# Create the namespace first
echo "Creating namespace manifest..."
mkdir -p k8s/namespace
cat << EOF > k8s/namespace/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: face-recognition-app
  labels:
    name: face-recognition-app
    environment: production
EOF

# Function to add namespace to a YAML file
add_namespace_to_file() {
    local file="$1"
    
    # Check if the file already has a namespace defined
    if grep -q "namespace:" "$file"; then
        # Replace the existing namespace with face-recognition-app
        sed -i 's/namespace: .*/namespace: face-recognition-app/' "$file"
    else
        # Add namespace to metadata section
        sed -i '/metadata:/a \ \ namespace: face-recognition-app' "$file"
    fi
    
    echo "Updated: $file"
}

# Update all YAML files in the k8s directory and subdirectories
find k8s -name "*.yaml" -not -path "*/namespace/*" | while read -r file; do
    add_namespace_to_file "$file"
done

echo "All manifests updated to use namespace: face-recognition-app"

# Update kustomization.yaml to include the namespace
if [ -f k8s/kustomization.yaml ]; then
    echo "Updating kustomization.yaml to include namespace resource..."
    
    # Check if namespace is already in resources
    if grep -q "namespace/namespace.yaml" k8s/kustomization.yaml; then
        echo "Namespace already included in kustomization.yaml"
    else
        # Add namespace to resources
        sed -i '/resources:/a - namespace/namespace.yaml' k8s/kustomization.yaml
    fi
    
    # Add namespace setting to kustomization.yaml
    if grep -q "namespace:" k8s/kustomization.yaml; then
        sed -i 's/namespace: .*/namespace: face-recognition-app/' k8s/kustomization.yaml
    else
        echo -e "\nnamespace: face-recognition-app" >> k8s/kustomization.yaml
    fi
fi

echo "Namespace setup complete. You can now deploy with: kubectl apply -k k8s/"