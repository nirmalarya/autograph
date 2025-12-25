#!/usr/bin/env python3
"""
Feature #20 Validator: Kubernetes Manifests for Production Deployment
Tests all K8s manifests for production readiness
"""

import subprocess
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Any

class Color:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_header(text: str):
    print(f"\n{Color.BLUE}{'=' * 80}{Color.END}")
    print(f"{Color.BLUE}{text.center(80)}{Color.END}")
    print(f"{Color.BLUE}{'=' * 80}{Color.END}\n")

def print_success(text: str):
    print(f"{Color.GREEN}✓ {text}{Color.END}")

def print_error(text: str):
    print(f"{Color.RED}✗ {text}{Color.END}")

def print_warning(text: str):
    print(f"{Color.YELLOW}⚠ {text}{Color.END}")

def load_yaml_file(filepath: Path) -> List[Dict[str, Any]]:
    """Load YAML file and return list of documents"""
    try:
        with open(filepath, 'r') as f:
            docs = list(yaml.safe_load_all(f))
            # Filter out None documents
            return [doc for doc in docs if doc is not None]
    except Exception as e:
        print_error(f"Failed to load {filepath}: {e}")
        return []

def validate_deployment_resources(deployment: Dict[str, Any]) -> bool:
    """Validate that deployment has resource requests and limits"""
    try:
        containers = deployment['spec']['template']['spec']['containers']
        for container in containers:
            resources = container.get('resources', {})

            # Check requests
            if 'requests' not in resources:
                print_error(f"  Missing resource requests in {deployment['metadata']['name']}")
                return False

            requests = resources['requests']
            if 'cpu' not in requests or 'memory' not in requests:
                print_error(f"  Incomplete resource requests in {deployment['metadata']['name']}")
                return False

            # Check limits
            if 'limits' not in resources:
                print_error(f"  Missing resource limits in {deployment['metadata']['name']}")
                return False

            limits = resources['limits']
            if 'cpu' not in limits or 'memory' not in limits:
                print_error(f"  Incomplete resource limits in {deployment['metadata']['name']}")
                return False

        return True
    except KeyError as e:
        print_error(f"  Invalid deployment structure: missing {e}")
        return False

def validate_deployment_probes(deployment: Dict[str, Any]) -> bool:
    """Validate that deployment has liveness and readiness probes"""
    try:
        containers = deployment['spec']['template']['spec']['containers']
        for container in containers:
            if 'livenessProbe' not in container:
                print_error(f"  Missing livenessProbe in {deployment['metadata']['name']}")
                return False

            if 'readinessProbe' not in container:
                print_error(f"  Missing readinessProbe in {deployment['metadata']['name']}")
                return False

            # Validate probe configuration
            liveness = container['livenessProbe']
            readiness = container['readinessProbe']

            for probe_name, probe in [('liveness', liveness), ('readiness', readiness)]:
                if 'httpGet' in probe:
                    if 'path' not in probe['httpGet'] or 'port' not in probe['httpGet']:
                        print_error(f"  Invalid {probe_name}Probe in {deployment['metadata']['name']}")
                        return False

        return True
    except KeyError as e:
        print_error(f"  Invalid deployment structure: missing {e}")
        return False

def validate_deployment_strategy(deployment: Dict[str, Any]) -> bool:
    """Validate that deployment has rolling update strategy"""
    try:
        strategy = deployment['spec'].get('strategy', {})
        if strategy.get('type') != 'RollingUpdate':
            print_warning(f"  {deployment['metadata']['name']} uses {strategy.get('type', 'default')} strategy (not RollingUpdate)")
            return True  # Warning, not error

        rolling_update = strategy.get('rollingUpdate', {})
        if 'maxSurge' not in rolling_update or 'maxUnavailable' not in rolling_update:
            print_warning(f"  {deployment['metadata']['name']} missing rolling update parameters")
            return True  # Warning, not error

        return True
    except KeyError as e:
        print_error(f"  Invalid deployment structure: missing {e}")
        return False

def validate_hpa(hpa: Dict[str, Any]) -> bool:
    """Validate HPA configuration"""
    try:
        name = hpa['metadata']['name']
        spec = hpa['spec']

        # Check min/max replicas
        if 'minReplicas' not in spec or 'maxReplicas' not in spec:
            print_error(f"  {name} missing min/max replicas")
            return False

        min_replicas = spec['minReplicas']
        max_replicas = spec['maxReplicas']

        if min_replicas >= max_replicas:
            print_error(f"  {name} invalid replica range: min={min_replicas}, max={max_replicas}")
            return False

        # Check metrics
        if 'metrics' not in spec or len(spec['metrics']) == 0:
            print_error(f"  {name} missing metrics")
            return False

        # Validate metrics
        for metric in spec['metrics']:
            if metric['type'] == 'Resource':
                resource_name = metric['resource']['name']
                if resource_name not in ['cpu', 'memory']:
                    print_warning(f"  {name} uses non-standard resource: {resource_name}")

        return True
    except KeyError as e:
        print_error(f"  Invalid HPA structure: missing {e}")
        return False

def test_kubectl_available() -> bool:
    """Test if kubectl is available"""
    print_header("Step 1: Check kubectl availability")
    try:
        result = subprocess.run(['kubectl', 'version', '--client', '--short'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print_success("kubectl is available")
            print(f"  {result.stdout.strip()}")
            return True
        else:
            print_warning("kubectl not available - skipping dry-run validation")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print_warning("kubectl not available - skipping dry-run validation")
        return False

def test_manifest_syntax() -> bool:
    """Test all manifests for valid YAML syntax"""
    print_header("Step 2: Validate YAML Syntax")

    k8s_dir = Path(__file__).parent / 'k8s'
    if not k8s_dir.exists():
        print_error(f"K8s directory not found: {k8s_dir}")
        return False

    yaml_files = list(k8s_dir.glob('*.yaml')) + list(k8s_dir.glob('*.yml'))
    if not yaml_files:
        print_error("No YAML files found in k8s directory")
        return False

    all_valid = True
    for yaml_file in yaml_files:
        docs = load_yaml_file(yaml_file)
        if docs:
            print_success(f"{yaml_file.name}: {len(docs)} document(s)")
        else:
            print_error(f"{yaml_file.name}: failed to parse")
            all_valid = False

    return all_valid

def test_deployment_resources() -> bool:
    """Test all deployments have resource limits"""
    print_header("Step 3: Validate Deployment Resource Limits")

    k8s_dir = Path(__file__).parent / 'k8s'
    deployment_files = [
        'api-gateway-deployment.yaml',
        'auth-service-deployment.yaml',
        'diagram-service-deployment.yaml',
        'ai-collaboration-git-deployments.yaml',
        'export-integration-svg-deployments.yaml',
        'postgres-deployment.yaml',
        'redis-deployment.yaml',
        'minio-deployment.yaml'
    ]

    all_valid = True
    deployment_count = 0

    for file_name in deployment_files:
        file_path = k8s_dir / file_name
        if not file_path.exists():
            print_warning(f"{file_name} not found")
            continue

        docs = load_yaml_file(file_path)
        for doc in docs:
            if doc.get('kind') == 'Deployment':
                deployment_count += 1
                name = doc['metadata']['name']
                if validate_deployment_resources(doc):
                    print_success(f"{name}: resource limits configured")
                else:
                    all_valid = False

    print(f"\nValidated {deployment_count} deployments")
    return all_valid

def test_deployment_probes() -> bool:
    """Test all deployments have health probes"""
    print_header("Step 4: Validate Liveness and Readiness Probes")

    k8s_dir = Path(__file__).parent / 'k8s'
    deployment_files = [
        'api-gateway-deployment.yaml',
        'auth-service-deployment.yaml',
        'diagram-service-deployment.yaml',
        'ai-collaboration-git-deployments.yaml',
        'export-integration-svg-deployments.yaml'
    ]

    all_valid = True
    probe_count = 0

    for file_name in deployment_files:
        file_path = k8s_dir / file_name
        if not file_path.exists():
            continue

        docs = load_yaml_file(file_path)
        for doc in docs:
            if doc.get('kind') == 'Deployment':
                probe_count += 1
                name = doc['metadata']['name']
                if validate_deployment_probes(doc):
                    print_success(f"{name}: health probes configured")
                else:
                    all_valid = False

    print(f"\nValidated {probe_count} deployments")
    return all_valid

def test_rolling_update_strategy() -> bool:
    """Test deployments use rolling update strategy"""
    print_header("Step 5: Validate Rolling Update Strategy")

    k8s_dir = Path(__file__).parent / 'k8s'
    deployment_files = [
        'api-gateway-deployment.yaml',
        'auth-service-deployment.yaml',
        'diagram-service-deployment.yaml',
        'ai-collaboration-git-deployments.yaml',
        'export-integration-svg-deployments.yaml'
    ]

    all_valid = True
    strategy_count = 0

    for file_name in deployment_files:
        file_path = k8s_dir / file_name
        if not file_path.exists():
            continue

        docs = load_yaml_file(file_path)
        for doc in docs:
            if doc.get('kind') == 'Deployment':
                strategy_count += 1
                name = doc['metadata']['name']
                if validate_deployment_strategy(doc):
                    print_success(f"{name}: rolling update configured")
                else:
                    all_valid = False

    print(f"\nValidated {strategy_count} deployments")
    return all_valid

def test_hpa_configuration() -> bool:
    """Test HPA configuration"""
    print_header("Step 6: Validate Horizontal Pod Autoscaler")

    k8s_dir = Path(__file__).parent / 'k8s'
    hpa_file = k8s_dir / 'hpa-autoscaling.yaml'

    if not hpa_file.exists():
        print_error("HPA file not found")
        return False

    docs = load_yaml_file(hpa_file)
    hpa_count = 0
    all_valid = True

    for doc in docs:
        if doc.get('kind') == 'HorizontalPodAutoscaler':
            hpa_count += 1
            name = doc['metadata']['name']
            if validate_hpa(doc):
                min_replicas = doc['spec']['minReplicas']
                max_replicas = doc['spec']['maxReplicas']
                print_success(f"{name}: configured (min={min_replicas}, max={max_replicas})")
            else:
                all_valid = False

    print(f"\nValidated {hpa_count} HPAs")
    return all_valid and hpa_count > 0

def test_service_configuration() -> bool:
    """Test service configuration"""
    print_header("Step 7: Validate Service Definitions")

    k8s_dir = Path(__file__).parent / 'k8s'
    service_files = [
        'microservices-services.yaml',
        'infrastructure-services.yaml'
    ]

    service_count = 0

    for file_name in service_files:
        file_path = k8s_dir / file_name
        if not file_path.exists():
            print_warning(f"{file_name} not found")
            continue

        docs = load_yaml_file(file_path)
        for doc in docs:
            if doc.get('kind') == 'Service':
                service_count += 1
                name = doc['metadata']['name']
                service_type = doc['spec'].get('type', 'ClusterIP')
                print_success(f"{name}: type={service_type}")

    print(f"\nValidated {service_count} services")
    return service_count > 0

def test_configmap_and_secrets() -> bool:
    """Test ConfigMap and Secrets"""
    print_header("Step 8: Validate ConfigMap and Secrets")

    k8s_dir = Path(__file__).parent / 'k8s'

    # Check ConfigMap
    configmap_file = k8s_dir / 'configmap.yaml'
    if configmap_file.exists():
        docs = load_yaml_file(configmap_file)
        for doc in docs:
            if doc.get('kind') == 'ConfigMap':
                print_success(f"ConfigMap: {doc['metadata']['name']}")
    else:
        print_warning("configmap.yaml not found")

    # Check Secrets template
    secrets_file = k8s_dir / 'secrets.yaml.example'
    if secrets_file.exists():
        print_success("secrets.yaml.example template exists")
    else:
        print_warning("secrets.yaml.example not found")

    return True

def test_namespace_configuration() -> bool:
    """Test namespace configuration"""
    print_header("Step 9: Validate Namespace")

    k8s_dir = Path(__file__).parent / 'k8s'
    namespace_file = k8s_dir / 'namespace.yaml'

    if not namespace_file.exists():
        print_warning("namespace.yaml not found")
        return True

    docs = load_yaml_file(namespace_file)
    for doc in docs:
        if doc.get('kind') == 'Namespace':
            name = doc['metadata']['name']
            print_success(f"Namespace: {name}")
            return True

    return True

def test_kubectl_dry_run() -> bool:
    """Test manifests with kubectl dry-run"""
    print_header("Step 10: Kubectl Dry-Run Validation")

    k8s_dir = Path(__file__).parent / 'k8s'
    yaml_files = [
        'namespace.yaml',
        'configmap.yaml',
        'api-gateway-deployment.yaml',
        'auth-service-deployment.yaml',
        'microservices-services.yaml'
    ]

    all_valid = True
    for file_name in yaml_files:
        file_path = k8s_dir / file_name
        if not file_path.exists():
            continue

        try:
            result = subprocess.run(
                ['kubectl', 'apply', '--dry-run=client', '-f', str(file_path)],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                print_success(f"{file_name}: valid")
            else:
                print_error(f"{file_name}: {result.stderr}")
                all_valid = False
        except Exception as e:
            print_error(f"{file_name}: {e}")
            all_valid = False

    return all_valid

def main():
    print_header("Feature #20: Kubernetes Manifests Validation")
    print("Testing Kubernetes production deployment configuration")

    results = {
        "kubectl_available": test_kubectl_available(),
        "manifest_syntax": test_manifest_syntax(),
        "deployment_resources": test_deployment_resources(),
        "deployment_probes": test_deployment_probes(),
        "rolling_update": test_rolling_update_strategy(),
        "hpa_configuration": test_hpa_configuration(),
        "service_configuration": test_service_configuration(),
        "configmap_secrets": test_configmap_and_secrets(),
        "namespace": test_namespace_configuration()
    }

    # Only run kubectl dry-run if kubectl is available
    if results["kubectl_available"]:
        results["kubectl_dry_run"] = test_kubectl_dry_run()

    # Print summary
    print_header("Validation Summary")

    # Count required tests (kubectl is optional)
    required_tests = {k: v for k, v in results.items() if k != 'kubectl_available' and k != 'kubectl_dry_run'}
    optional_tests = {k: v for k, v in results.items() if k in ['kubectl_available', 'kubectl_dry_run']}

    for test_name, result in results.items():
        status = f"{Color.GREEN}PASS{Color.END}" if result else f"{Color.RED}FAIL{Color.END}"
        optional = " (optional)" if test_name in optional_tests else ""
        print(f"{test_name.replace('_', ' ').title()}{optional}: {status}")

    required_passed = sum(1 for v in required_tests.values() if v)
    required_total = len(required_tests)
    optional_passed = sum(1 for v in optional_tests.values() if v)
    optional_total = len(optional_tests)

    print(f"\n{Color.BLUE}Required: {required_passed}/{required_total} tests passed{Color.END}")
    print(f"{Color.BLUE}Optional: {optional_passed}/{optional_total} tests passed{Color.END}")

    if required_passed == required_total:
        print(f"\n{Color.GREEN}✓ Feature #20: Kubernetes Manifests - VALIDATED{Color.END}")
        print(f"{Color.GREEN}  All production-ready K8s manifests validated successfully{Color.END}")
        return 0
    else:
        print(f"\n{Color.RED}✗ Feature #20: Kubernetes Manifests - FAILED{Color.END}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
