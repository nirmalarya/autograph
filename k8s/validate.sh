#!/bin/bash
# AutoGraph v3 - Kubernetes Manifest Validation Script
# This script validates all Kubernetes manifests without deploying them

set -e

echo "=================================================="
echo "AutoGraph v3 - Kubernetes Manifest Validation"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
TOTAL=0
PASSED=0
FAILED=0

# Function to validate a manifest
validate_manifest() {
    local file=$1
    local description=$2
    
    TOTAL=$((TOTAL + 1))
    echo -n "Testing: $description ... "
    
    # First check if file exists and is valid YAML
    if ! [ -f "$file" ]; then
        echo -e "${RED}FAIL${NC}"
        echo "  File not found: $file"
        FAILED=$((FAILED + 1))
        return 1
    fi
    
    # Try to validate with kubectl
    if [ "$CLUSTER_AVAILABLE" = true ]; then
        if kubectl apply --dry-run=client -f "$file" > /dev/null 2>&1; then
            echo -e "${GREEN}PASS${NC}"
            PASSED=$((PASSED + 1))
            return 0
        else
            echo -e "${RED}FAIL${NC}"
            echo "  Error validating $file:"
            kubectl apply --dry-run=client -f "$file" 2>&1 | sed 's/^/    /'
            FAILED=$((FAILED + 1))
            return 1
        fi
    else
        # Basic YAML validation when no cluster available
        if kubectl apply --dry-run=client --validate=false -f "$file" > /dev/null 2>&1; then
            echo -e "${GREEN}PASS${NC} (basic YAML check)"
            PASSED=$((PASSED + 1))
            return 0
        else
            echo -e "${RED}FAIL${NC}"
            echo "  Error parsing $file:"
            kubectl apply --dry-run=client --validate=false -f "$file" 2>&1 | sed 's/^/    /'
            FAILED=$((FAILED + 1))
            return 1
        fi
    fi
}

# Change to k8s directory
cd "$(dirname "$0")"

echo "Step 1: Checking kubectl installation"
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}ERROR: kubectl not found${NC}"
    echo "Please install kubectl: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi
echo -e "${GREEN}✓ kubectl found${NC}"

# Check if cluster is available
if kubectl cluster-info &> /dev/null; then
    echo -e "${GREEN}✓ Kubernetes cluster is accessible${NC}"
    CLUSTER_AVAILABLE=true
    DRY_RUN_MODE="client"
else
    echo -e "${YELLOW}⚠ No Kubernetes cluster accessible${NC}"
    echo "  Will perform basic YAML validation only"
    CLUSTER_AVAILABLE=false
    DRY_RUN_MODE="none"
fi
echo ""

echo "Step 2: Validating manifest syntax"
echo "------------------------------------"

# Validate each manifest
validate_manifest "namespace.yaml" "Namespace manifest"
validate_manifest "configmap.yaml" "ConfigMap manifest"
validate_manifest "secrets.yaml" "Secrets manifest"
validate_manifest "persistentvolumeclaims.yaml" "PersistentVolumeClaims manifest"
validate_manifest "postgres-deployment.yaml" "PostgreSQL Deployment"
validate_manifest "redis-deployment.yaml" "Redis Deployment"
validate_manifest "minio-deployment.yaml" "MinIO Deployment"
validate_manifest "infrastructure-services.yaml" "Infrastructure Services"
validate_manifest "api-gateway-deployment.yaml" "API Gateway Deployment"
validate_manifest "auth-service-deployment.yaml" "Auth Service Deployment"
validate_manifest "diagram-service-deployment.yaml" "Diagram Service Deployment"
validate_manifest "ai-collaboration-git-deployments.yaml" "AI/Collaboration/Git Deployments"
validate_manifest "export-integration-svg-deployments.yaml" "Export/Integration/SVG Deployments"
validate_manifest "frontend-deployment.yaml" "Frontend Deployment"
validate_manifest "microservices-services.yaml" "Microservices Services"
validate_manifest "ingress.yaml" "Ingress manifest"
validate_manifest "servicemonitor.yaml" "ServiceMonitor manifest"

echo ""
echo "Step 3: Checking resource limits"
echo "---------------------------------"

# Check if resource limits are defined
check_resources() {
    local file=$1
    local component=$2
    
    if grep -q "resources:" "$file" && \
       grep -q "limits:" "$file" && \
       grep -q "requests:" "$file"; then
        echo -e "  $component: ${GREEN}✓ Resource limits defined${NC}"
        return 0
    else
        echo -e "  $component: ${YELLOW}⚠ No resource limits${NC}"
        return 1
    fi
}

check_resources "postgres-deployment.yaml" "PostgreSQL"
check_resources "redis-deployment.yaml" "Redis"
check_resources "minio-deployment.yaml" "MinIO"
check_resources "api-gateway-deployment.yaml" "API Gateway"
check_resources "auth-service-deployment.yaml" "Auth Service"
check_resources "diagram-service-deployment.yaml" "Diagram Service"

echo ""
echo "Step 4: Checking probes"
echo "-----------------------"

# Check if health probes are defined
check_probes() {
    local file=$1
    local component=$2
    
    if grep -q "livenessProbe:" "$file" && \
       grep -q "readinessProbe:" "$file"; then
        echo -e "  $component: ${GREEN}✓ Liveness and readiness probes defined${NC}"
        return 0
    else
        echo -e "  $component: ${YELLOW}⚠ Missing probes${NC}"
        return 1
    fi
}

check_probes "postgres-deployment.yaml" "PostgreSQL"
check_probes "redis-deployment.yaml" "Redis"
check_probes "minio-deployment.yaml" "MinIO"
check_probes "api-gateway-deployment.yaml" "API Gateway"
check_probes "auth-service-deployment.yaml" "Auth Service"
check_probes "diagram-service-deployment.yaml" "Diagram Service"

echo ""
echo "Step 5: Checking rolling update strategy"
echo "-----------------------------------------"

# Check rolling update configuration
check_rolling_update() {
    local file=$1
    local component=$2
    
    if grep -q "type: RollingUpdate" "$file"; then
        echo -e "  $component: ${GREEN}✓ Rolling update configured${NC}"
        return 0
    else
        echo -e "  $component: ${YELLOW}⚠ No rolling update strategy${NC}"
        return 1
    fi
}

check_rolling_update "api-gateway-deployment.yaml" "API Gateway"
check_rolling_update "auth-service-deployment.yaml" "Auth Service"
check_rolling_update "diagram-service-deployment.yaml" "Diagram Service"

echo ""
echo "Step 6: Summary"
echo "==============="
echo ""
echo "Manifest Validation Results:"
echo "  Total tests: $TOTAL"
echo -e "  Passed: ${GREEN}$PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "  Failed: ${RED}$FAILED${NC}"
else
    echo -e "  Failed: $FAILED"
fi
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All manifests are valid!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Create a Kubernetes cluster (minikube, kind, or cloud provider)"
    echo "  2. Update secrets.yaml with real credentials"
    echo "  3. Deploy with: kubectl apply -f k8s/"
    echo "  4. Monitor with: kubectl get pods -n autograph -w"
    exit 0
else
    echo -e "${RED}✗ Some manifests have errors${NC}"
    echo "Please fix the errors above before deploying."
    exit 1
fi
