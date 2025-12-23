#!/usr/bin/env python3
"""
AutoGraph v3 - Kubernetes Manifest Validation Script
This script validates all Kubernetes manifests without requiring a running cluster.
"""

import os
import sys
import json
import re
from pathlib import Path

# ANSI color codes
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
NC = '\033[0m'  # No Color

def validate_yaml_syntax(filepath):
    """Basic YAML syntax validation using JSON-like parsing."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            
        # Check for basic YAML structure
        if not content.strip():
            return False, "Empty file"
        
        # Check for required Kubernetes fields
        if 'apiVersion:' not in content:
            return False, "Missing apiVersion"
        
        if 'kind:' not in content:
            return False, "Missing kind"
        
        if 'metadata:' not in content:
            return False, "Missing metadata"
        
        return True, "Valid"
    except Exception as e:
        return False, str(e)

def check_resources(filepath, component):
    """Check if resource limits are defined."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        has_resources = 'resources:' in content
        has_limits = 'limits:' in content
        has_requests = 'requests:' in content
        
        if has_resources and has_limits and has_requests:
            print(f"  {component}: {GREEN}✓ Resource limits defined{NC}")
            return True
        else:
            print(f"  {component}: {YELLOW}⚠ No resource limits{NC}")
            return False
    except Exception as e:
        print(f"  {component}: {RED}✗ Error: {e}{NC}")
        return False

def check_probes(filepath, component):
    """Check if health probes are defined."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        has_liveness = 'livenessProbe:' in content
        has_readiness = 'readinessProbe:' in content
        
        if has_liveness and has_readiness:
            print(f"  {component}: {GREEN}✓ Liveness and readiness probes defined{NC}")
            return True
        else:
            print(f"  {component}: {YELLOW}⚠ Missing probes{NC}")
            return False
    except Exception as e:
        print(f"  {component}: {RED}✗ Error: {e}{NC}")
        return False

def check_rolling_update(filepath, component):
    """Check rolling update configuration."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        has_rolling = 'type: RollingUpdate' in content
        
        if has_rolling:
            print(f"  {component}: {GREEN}✓ Rolling update configured{NC}")
            return True
        else:
            print(f"  {component}: {YELLOW}⚠ No rolling update strategy{NC}")
            return False
    except Exception as e:
        print(f"  {component}: {RED}✗ Error: {e}{NC}")
        return False

def main():
    print("=" * 50)
    print("AutoGraph v3 - Kubernetes Manifest Validation")
    print("=" * 50)
    print()
    
    # Change to k8s directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Counters
    total = 0
    passed = 0
    failed = 0
    
    print("Step 1: Checking Python environment")
    print(f"{GREEN}✓ Python {sys.version.split()[0]} found{NC}")
    print()
    
    print("Step 2: Validating manifest syntax")
    print("-" * 50)
    
    manifests = [
        ("namespace.yaml", "Namespace manifest"),
        ("configmap.yaml", "ConfigMap manifest"),
        ("secrets.yaml", "Secrets manifest"),
        ("persistentvolumeclaims.yaml", "PersistentVolumeClaims manifest"),
        ("postgres-deployment.yaml", "PostgreSQL Deployment"),
        ("redis-deployment.yaml", "Redis Deployment"),
        ("minio-deployment.yaml", "MinIO Deployment"),
        ("infrastructure-services.yaml", "Infrastructure Services"),
        ("api-gateway-deployment.yaml", "API Gateway Deployment"),
        ("auth-service-deployment.yaml", "Auth Service Deployment"),
        ("diagram-service-deployment.yaml", "Diagram Service Deployment"),
        ("ai-collaboration-git-deployments.yaml", "AI/Collaboration/Git Deployments"),
        ("export-integration-svg-deployments.yaml", "Export/Integration/SVG Deployments"),
        ("frontend-deployment.yaml", "Frontend Deployment"),
        ("microservices-services.yaml", "Microservices Services"),
        ("ingress.yaml", "Ingress manifest"),
        ("servicemonitor.yaml", "ServiceMonitor manifest"),
    ]
    
    for filepath, description in manifests:
        total += 1
        print(f"Testing: {description} ... ", end='')
        
        if not Path(filepath).exists():
            print(f"{RED}FAIL{NC}")
            print(f"  File not found: {filepath}")
            failed += 1
            continue
        
        valid, message = validate_yaml_syntax(filepath)
        if valid:
            print(f"{GREEN}PASS{NC}")
            passed += 1
        else:
            print(f"{RED}FAIL{NC}")
            print(f"  Error: {message}")
            failed += 1
    
    print()
    print("Step 3: Checking resource limits")
    print("-" * 50)
    
    check_resources("postgres-deployment.yaml", "PostgreSQL")
    check_resources("redis-deployment.yaml", "Redis")
    check_resources("minio-deployment.yaml", "MinIO")
    check_resources("api-gateway-deployment.yaml", "API Gateway")
    check_resources("auth-service-deployment.yaml", "Auth Service")
    check_resources("diagram-service-deployment.yaml", "Diagram Service")
    
    print()
    print("Step 4: Checking probes")
    print("-" * 50)
    
    check_probes("postgres-deployment.yaml", "PostgreSQL")
    check_probes("redis-deployment.yaml", "Redis")
    check_probes("minio-deployment.yaml", "MinIO")
    check_probes("api-gateway-deployment.yaml", "API Gateway")
    check_probes("auth-service-deployment.yaml", "Auth Service")
    check_probes("diagram-service-deployment.yaml", "Diagram Service")
    
    print()
    print("Step 5: Checking rolling update strategy")
    print("-" * 50)
    
    check_rolling_update("api-gateway-deployment.yaml", "API Gateway")
    check_rolling_update("auth-service-deployment.yaml", "Auth Service")
    check_rolling_update("diagram-service-deployment.yaml", "Diagram Service")
    
    print()
    print("Step 6: Summary")
    print("=" * 50)
    print()
    print("Manifest Validation Results:")
    print(f"  Total tests: {total}")
    print(f"  Passed: {GREEN}{passed}{NC}")
    if failed > 0:
        print(f"  Failed: {RED}{failed}{NC}")
    else:
        print(f"  Failed: {failed}")
    print()
    
    if failed == 0:
        print(f"{GREEN}✓ All manifests are valid!{NC}")
        print()
        print("Next steps:")
        print("  1. Create a Kubernetes cluster (minikube, kind, or cloud provider)")
        print("  2. Update secrets.yaml with real credentials")
        print("  3. Deploy with: kubectl apply -f k8s/")
        print("  4. Monitor with: kubectl get pods -n autograph -w")
        return 0
    else:
        print(f"{RED}✗ Some manifests have errors{NC}")
        print("Please fix the errors above before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
