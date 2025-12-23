#!/bin/bash
#
# AutoGraph v3 - Blue-Green Deployment Script
# This script manages blue-green deployments for zero-downtime updates
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="autograph"
COMPONENT="api-gateway"
DEPLOYMENT_BLUE="${COMPONENT}-blue"
DEPLOYMENT_GREEN="${COMPONENT}-green"
SERVICE_ACTIVE="${COMPONENT}-service-active"
SERVICE_BLUE="${COMPONENT}-blue-service"
SERVICE_GREEN="${COMPONENT}-green-service"

# Functions
print_header() {
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

get_active_deployment() {
    # Get the current active deployment by checking service selector
    ACTIVE=$(kubectl get service ${SERVICE_ACTIVE} -n ${NAMESPACE} -o jsonpath='{.spec.selector.deployment}' 2>/dev/null || echo "none")
    echo $ACTIVE
}

get_inactive_deployment() {
    ACTIVE=$(get_active_deployment)
    if [ "$ACTIVE" == "blue" ]; then
        echo "green"
    elif [ "$ACTIVE" == "green" ]; then
        echo "blue"
    else
        echo "blue"  # Default to blue if no active deployment
    fi
}

get_deployment_name() {
    local ENV=$1
    if [ "$ENV" == "blue" ]; then
        echo $DEPLOYMENT_BLUE
    else
        echo $DEPLOYMENT_GREEN
    fi
}

get_service_name() {
    local ENV=$1
    if [ "$ENV" == "blue" ]; then
        echo $SERVICE_BLUE
    else
        echo $SERVICE_GREEN
    fi
}

check_deployment_health() {
    local DEPLOYMENT=$1
    print_info "Checking health of deployment: $DEPLOYMENT"
    
    # Check if deployment exists
    if ! kubectl get deployment ${DEPLOYMENT} -n ${NAMESPACE} &>/dev/null; then
        print_error "Deployment ${DEPLOYMENT} does not exist"
        return 1
    fi
    
    # Check if pods are ready
    REPLICAS=$(kubectl get deployment ${DEPLOYMENT} -n ${NAMESPACE} -o jsonpath='{.spec.replicas}')
    READY=$(kubectl get deployment ${DEPLOYMENT} -n ${NAMESPACE} -o jsonpath='{.status.readyReplicas}')
    
    if [ "$REPLICAS" == "$READY" ] && [ "$READY" != "0" ]; then
        print_success "Deployment ${DEPLOYMENT} is healthy: ${READY}/${REPLICAS} pods ready"
        return 0
    else
        print_warning "Deployment ${DEPLOYMENT} is not fully ready: ${READY}/${REPLICAS} pods ready"
        return 1
    fi
}

run_smoke_tests() {
    local ENV=$1
    local SERVICE=$(get_service_name $ENV)
    
    print_info "Running smoke tests on ${ENV} environment..."
    
    # Port-forward to the service
    kubectl port-forward -n ${NAMESPACE} svc/${SERVICE} 18080:8080 &>/dev/null &
    PF_PID=$!
    sleep 3
    
    # Test health endpoint
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:18080/health || echo "000")
    
    # Kill port-forward
    kill $PF_PID 2>/dev/null || true
    
    if [ "$HTTP_CODE" == "200" ]; then
        print_success "Smoke tests passed: Health check returned 200"
        return 0
    else
        print_error "Smoke tests failed: Health check returned ${HTTP_CODE}"
        return 1
    fi
}

switch_traffic() {
    local TARGET_ENV=$1
    local PERCENTAGE=${2:-100}
    
    print_info "Switching ${PERCENTAGE}% traffic to ${TARGET_ENV} environment..."
    
    if [ "$PERCENTAGE" == "100" ]; then
        # Full switch - update service selector
        kubectl patch service ${SERVICE_ACTIVE} -n ${NAMESPACE} -p "{\"spec\":{\"selector\":{\"deployment\":\"${TARGET_ENV}\"}}}"
        print_success "Traffic switched to ${TARGET_ENV}"
    else
        # Partial switch - requires ingress with traffic splitting
        print_warning "Canary deployment (${PERCENTAGE}%) requires Ingress with traffic splitting"
        print_info "For full implementation, configure NGINX Ingress with canary annotations"
        print_info "For now, deploying to ${TARGET_ENV} without traffic split"
    fi
}

deploy_version() {
    local ENV=$1
    local VERSION=$2
    local IMAGE="autograph/${COMPONENT}:${VERSION}"
    local DEPLOYMENT=$(get_deployment_name $ENV)
    
    print_info "Deploying version ${VERSION} to ${ENV} environment..."
    
    # Update image
    kubectl set image deployment/${DEPLOYMENT} ${COMPONENT}=${IMAGE} -n ${NAMESPACE}
    
    # Scale up if needed
    REPLICAS=$(kubectl get deployment ${DEPLOYMENT} -n ${NAMESPACE} -o jsonpath='{.spec.replicas}')
    if [ "$REPLICAS" == "0" ]; then
        print_info "Scaling ${DEPLOYMENT} to 2 replicas..."
        kubectl scale deployment/${DEPLOYMENT} --replicas=2 -n ${NAMESPACE}
    fi
    
    # Wait for rollout
    print_info "Waiting for rollout to complete..."
    kubectl rollout status deployment/${DEPLOYMENT} -n ${NAMESPACE} --timeout=300s
    
    print_success "Version ${VERSION} deployed to ${ENV}"
}

scale_down() {
    local ENV=$1
    local DEPLOYMENT=$(get_deployment_name $ENV)
    
    print_info "Scaling down ${ENV} environment..."
    kubectl scale deployment/${DEPLOYMENT} --replicas=0 -n ${NAMESPACE}
    print_success "${ENV} environment scaled down to 0 replicas"
}

rollback() {
    local PREVIOUS_ENV=$1
    print_warning "Rolling back to ${PREVIOUS_ENV} environment..."
    switch_traffic $PREVIOUS_ENV 100
    print_success "Rollback complete"
}

show_status() {
    print_header "Blue-Green Deployment Status"
    
    echo ""
    echo -e "${CYAN}Active Deployment:${NC}"
    ACTIVE=$(get_active_deployment)
    echo "  Environment: $ACTIVE"
    echo ""
    
    echo -e "${CYAN}Blue Environment:${NC}"
    kubectl get deployment ${DEPLOYMENT_BLUE} -n ${NAMESPACE} -o wide 2>/dev/null || echo "  Not deployed"
    echo ""
    
    echo -e "${CYAN}Green Environment:${NC}"
    kubectl get deployment ${DEPLOYMENT_GREEN} -n ${NAMESPACE} -o wide 2>/dev/null || echo "  Not deployed"
    echo ""
    
    echo -e "${CYAN}Services:${NC}"
    kubectl get svc -n ${NAMESPACE} -l component=${COMPONENT} -o wide
    echo ""
}

# Main command handling
case "${1}" in
    "status")
        show_status
        ;;
    
    "deploy")
        # Usage: ./blue-green-deploy.sh deploy <version>
        if [ -z "$2" ]; then
            print_error "Usage: $0 deploy <version>"
            exit 1
        fi
        
        VERSION=$2
        
        print_header "Blue-Green Deployment: Version ${VERSION}"
        
        # Step 1: Determine active and inactive environments
        ACTIVE_ENV=$(get_active_deployment)
        INACTIVE_ENV=$(get_inactive_deployment)
        
        print_info "Active environment: ${ACTIVE_ENV}"
        print_info "Deploying to inactive environment: ${INACTIVE_ENV}"
        echo ""
        
        # Step 2: Check active environment health
        ACTIVE_DEPLOYMENT=$(get_deployment_name $ACTIVE_ENV)
        if ! check_deployment_health $ACTIVE_DEPLOYMENT; then
            print_error "Active deployment is unhealthy. Fix before proceeding."
            exit 1
        fi
        echo ""
        
        # Step 3: Deploy to inactive environment
        deploy_version $INACTIVE_ENV $VERSION
        echo ""
        
        # Step 4: Run smoke tests on inactive environment
        sleep 5
        if ! run_smoke_tests $INACTIVE_ENV; then
            print_error "Smoke tests failed. Deployment aborted."
            print_info "To rollback: $0 rollback"
            exit 1
        fi
        echo ""
        
        # Step 5: Switch traffic to new environment
        print_info "Ready to switch traffic to ${INACTIVE_ENV}"
        read -p "Continue with traffic switch? (yes/no): " CONFIRM
        if [ "$CONFIRM" != "yes" ]; then
            print_warning "Traffic switch cancelled by user"
            print_info "New version running on ${INACTIVE_ENV}, but not receiving traffic"
            print_info "To switch manually: $0 switch ${INACTIVE_ENV}"
            exit 0
        fi
        
        switch_traffic $INACTIVE_ENV 100
        echo ""
        
        # Step 6: Verify new deployment
        sleep 5
        if check_deployment_health $(get_deployment_name $INACTIVE_ENV); then
            print_success "Deployment successful!"
            print_info "Active environment: ${INACTIVE_ENV}"
            print_info "Previous environment (${ACTIVE_ENV}) kept as rollback option"
            print_info "To scale down old environment: $0 cleanup ${ACTIVE_ENV}"
        else
            print_error "New deployment appears unhealthy after switch"
            print_warning "Consider rollback: $0 rollback"
        fi
        ;;
    
    "switch")
        # Usage: ./blue-green-deploy.sh switch <blue|green> [percentage]
        if [ -z "$2" ]; then
            print_error "Usage: $0 switch <blue|green> [percentage]"
            exit 1
        fi
        
        TARGET_ENV=$2
        PERCENTAGE=${3:-100}
        
        print_header "Switching Traffic to ${TARGET_ENV}"
        
        # Check target environment health
        TARGET_DEPLOYMENT=$(get_deployment_name $TARGET_ENV)
        if ! check_deployment_health $TARGET_DEPLOYMENT; then
            print_error "Target deployment is unhealthy. Cannot switch traffic."
            exit 1
        fi
        
        switch_traffic $TARGET_ENV $PERCENTAGE
        print_success "Traffic switch complete"
        ;;
    
    "rollback")
        print_header "Rollback to Previous Environment"
        
        ACTIVE_ENV=$(get_active_deployment)
        PREVIOUS_ENV=$(get_inactive_deployment)
        
        print_warning "Current active: ${ACTIVE_ENV}"
        print_info "Rolling back to: ${PREVIOUS_ENV}"
        
        # Check if previous environment is healthy
        PREVIOUS_DEPLOYMENT=$(get_deployment_name $PREVIOUS_ENV)
        if ! check_deployment_health $PREVIOUS_DEPLOYMENT; then
            print_error "Previous deployment is not available or unhealthy"
            exit 1
        fi
        
        rollback $PREVIOUS_ENV
        ;;
    
    "cleanup")
        # Usage: ./blue-green-deploy.sh cleanup <blue|green>
        if [ -z "$2" ]; then
            print_error "Usage: $0 cleanup <blue|green>"
            exit 1
        fi
        
        ENV=$2
        
        # Prevent cleanup of active environment
        ACTIVE_ENV=$(get_active_deployment)
        if [ "$ENV" == "$ACTIVE_ENV" ]; then
            print_error "Cannot cleanup active environment"
            exit 1
        fi
        
        print_header "Cleaning Up ${ENV} Environment"
        scale_down $ENV
        ;;
    
    "init")
        print_header "Initializing Blue-Green Deployment"
        
        # Apply blue-green deployment manifest
        if [ ! -f "blue-green-deployment.yaml" ]; then
            print_error "blue-green-deployment.yaml not found"
            exit 1
        fi
        
        print_info "Applying blue-green deployment manifests..."
        kubectl apply -f blue-green-deployment.yaml
        
        print_success "Blue-green deployment initialized"
        print_info "Blue environment is active by default"
        print_info "Use '$0 status' to check deployment status"
        ;;
    
    *)
        echo "AutoGraph v3 - Blue-Green Deployment Script"
        echo ""
        echo "Usage:"
        echo "  $0 init                           - Initialize blue-green deployment"
        echo "  $0 status                         - Show current deployment status"
        echo "  $0 deploy <version>               - Deploy new version (automated workflow)"
        echo "  $0 switch <blue|green> [percent]  - Switch traffic to environment"
        echo "  $0 rollback                       - Rollback to previous environment"
        echo "  $0 cleanup <blue|green>           - Scale down environment"
        echo ""
        echo "Example workflow:"
        echo "  1. $0 status                      - Check current state"
        echo "  2. $0 deploy v1.1.0               - Deploy new version"
        echo "  3. $0 switch green 10             - Canary test with 10% traffic"
        echo "  4. $0 switch green 100            - Full switch"
        echo "  5. $0 cleanup blue                - Remove old version"
        echo ""
        exit 1
        ;;
esac
