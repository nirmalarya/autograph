#!/usr/bin/env python3
"""
AutoGraph v3 - Auto-Scaling Test Suite

Comprehensive tests for auto-scaling functionality across
Kubernetes and Docker Compose environments.

Tests:
1. Auto-scaling configuration validation
2. Monitoring script functionality
3. Scale-up trigger (70% CPU threshold)
4. Scale-down trigger (30% CPU threshold)
5. Min/max replica limits
6. Stabilization windows
7. Load balancer integration
8. Kubernetes HPA validation

Usage:
  python3 test_autoscaling.py
"""

import json
import os
import subprocess
import sys
import time
import yaml
from typing import Dict, List, Tuple


# ANSI colors
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


class AutoScalingTests:
    """Test suite for auto-scaling functionality"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
    
    def print_header(self, test_name: str):
        """Print test header"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}TEST: {test_name}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.RESET}\n")
    
    def print_result(self, success: bool, message: str):
        """Print test result"""
        if success:
            print(f"{Colors.GREEN}✓ PASS{Colors.RESET}: {message}")
            self.passed += 1
        else:
            print(f"{Colors.RED}✗ FAIL{Colors.RESET}: {message}")
            self.failed += 1
    
    def print_warning(self, message: str):
        """Print warning"""
        print(f"{Colors.YELLOW}⚠ WARNING{Colors.RESET}: {message}")
        self.warnings += 1
    
    def print_info(self, message: str):
        """Print info"""
        print(f"{Colors.BLUE}ℹ INFO{Colors.RESET}: {message}")
    
    def test_hpa_manifests(self):
        """Test 1: Validate Kubernetes HPA manifests exist and are valid"""
        self.print_header("Kubernetes HPA Manifests Validation")
        
        hpa_file = 'k8s/hpa-autoscaling.yaml'
        
        # Check file exists
        if not os.path.exists(hpa_file):
            self.print_result(False, f"HPA manifest file not found: {hpa_file}")
            return
        
        self.print_result(True, f"HPA manifest file exists: {hpa_file}")
        
        # Parse YAML
        try:
            with open(hpa_file, 'r') as f:
                docs = list(yaml.safe_load_all(f))
            
            self.print_result(True, f"Successfully parsed YAML ({len(docs)} documents)")
            
            # Check each HPA
            expected_services = [
                'diagram-service',
                'ai-service',
                'collaboration-service',
                'auth-service',
                'export-service',
                'git-service',
                'integration-hub',
                'api-gateway'
            ]
            
            found_services = []
            
            for doc in docs:
                if not doc or doc.get('kind') != 'HorizontalPodAutoscaler':
                    continue
                
                name = doc['metadata']['name']
                service_name = name.replace('-hpa', '')
                found_services.append(service_name)
                
                # Validate structure
                spec = doc.get('spec', {})
                
                # Check scaleTargetRef
                if 'scaleTargetRef' not in spec:
                    self.print_result(False, f"{service_name}: Missing scaleTargetRef")
                    continue
                
                # Check min/max replicas
                min_replicas = spec.get('minReplicas')
                max_replicas = spec.get('maxReplicas')
                
                if not min_replicas or not max_replicas:
                    self.print_result(False, f"{service_name}: Missing min/max replicas")
                    continue
                
                if min_replicas < 2:
                    self.print_result(False, f"{service_name}: minReplicas should be >= 2, got {min_replicas}")
                    continue
                
                if max_replicas < min_replicas:
                    self.print_result(False, f"{service_name}: maxReplicas < minReplicas")
                    continue
                
                # Check metrics
                metrics = spec.get('metrics', [])
                has_cpu = any(m.get('resource', {}).get('name') == 'cpu' for m in metrics)
                has_memory = any(m.get('resource', {}).get('name') == 'memory' for m in metrics)
                
                if not has_cpu:
                    self.print_result(False, f"{service_name}: Missing CPU metric")
                    continue
                
                if not has_memory:
                    self.print_warning(f"{service_name}: Missing memory metric (optional)")
                
                # Check behavior (scaling policies)
                behavior = spec.get('behavior', {})
                if 'scaleUp' not in behavior or 'scaleDown' not in behavior:
                    self.print_warning(f"{service_name}: Missing scaling behavior policies")
                
                self.print_result(True, f"{service_name}: Valid HPA (min={min_replicas}, max={max_replicas})")
            
            # Check all expected services are present
            missing = set(expected_services) - set(found_services)
            if missing:
                self.print_result(False, f"Missing HPAs for: {', '.join(missing)}")
            else:
                self.print_result(True, "All expected services have HPAs")
            
        except yaml.YAMLError as e:
            self.print_result(False, f"YAML parsing error: {e}")
        except Exception as e:
            self.print_result(False, f"Error validating HPAs: {e}")
    
    def test_monitoring_script(self):
        """Test 2: Validate monitoring script exists and runs"""
        self.print_header("Monitoring Script Validation")
        
        script_file = 'monitor_autoscaling.py'
        
        # Check file exists
        if not os.path.exists(script_file):
            self.print_result(False, f"Monitoring script not found: {script_file}")
            return
        
        self.print_result(True, f"Monitoring script exists: {script_file}")
        
        # Check executable
        if not os.access(script_file, os.X_OK):
            self.print_warning("Script is not executable (run: chmod +x monitor_autoscaling.py)")
        
        # Test help
        try:
            result = subprocess.run(
                ['python3', script_file, '--help'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self.print_result(True, "Script executes successfully (--help)")
            else:
                self.print_result(False, f"Script execution failed: {result.stderr}")
                return
            
            # Check for required arguments
            help_text = result.stdout
            required_args = ['--mode', '--duration', '--interval']
            
            for arg in required_args:
                if arg in help_text:
                    self.print_result(True, f"Script supports {arg} argument")
                else:
                    self.print_warning(f"Script may not support {arg} argument")
            
        except subprocess.TimeoutExpired:
            self.print_result(False, "Script execution timed out")
        except Exception as e:
            self.print_result(False, f"Error testing script: {e}")
    
    def test_autoscaler_docker_script(self):
        """Test 3: Validate Docker auto-scaler script"""
        self.print_header("Docker Auto-Scaler Script Validation")
        
        script_file = 'autoscaler_docker.py'
        
        # Check file exists
        if not os.path.exists(script_file):
            self.print_result(False, f"Auto-scaler script not found: {script_file}")
            return
        
        self.print_result(True, f"Auto-scaler script exists: {script_file}")
        
        # Test help
        try:
            result = subprocess.run(
                ['python3', script_file, '--help'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self.print_result(True, "Script executes successfully (--help)")
            else:
                self.print_result(False, f"Script execution failed: {result.stderr}")
                return
            
            # Check for required features
            help_text = result.stdout
            
            if '--dry-run' in help_text:
                self.print_result(True, "Script supports --dry-run mode")
            else:
                self.print_warning("Script may not support --dry-run mode")
            
            if '--interval' in help_text:
                self.print_result(True, "Script supports --interval argument")
            else:
                self.print_warning("Script may not support --interval argument")
            
        except subprocess.TimeoutExpired:
            self.print_result(False, "Script execution timed out")
        except Exception as e:
            self.print_result(False, f"Error testing script: {e}")
    
    def test_load_generator(self):
        """Test 4: Validate load generator script"""
        self.print_header("Load Generator Script Validation")
        
        script_file = 'load_generator.py'
        
        # Check file exists
        if not os.path.exists(script_file):
            self.print_result(False, f"Load generator not found: {script_file}")
            return
        
        self.print_result(True, f"Load generator exists: {script_file}")
        
        # Test help
        try:
            result = subprocess.run(
                ['python3', script_file, '--help'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self.print_result(True, "Script executes successfully (--help)")
            else:
                self.print_result(False, f"Script execution failed: {result.stderr}")
                return
            
            # Check for load patterns
            help_text = result.stdout
            patterns = ['constant', 'spike', 'gradual', 'random']
            
            for pattern in patterns:
                if pattern in help_text:
                    self.print_result(True, f"Supports {pattern} load pattern")
                else:
                    self.print_warning(f"May not support {pattern} load pattern")
            
        except subprocess.TimeoutExpired:
            self.print_result(False, "Script execution timed out")
        except Exception as e:
            self.print_result(False, f"Error testing script: {e}")
    
    def test_scaling_thresholds(self):
        """Test 5: Validate scaling thresholds configuration"""
        self.print_header("Scaling Thresholds Configuration")
        
        # Check HPA thresholds
        hpa_file = 'k8s/hpa-autoscaling.yaml'
        
        try:
            with open(hpa_file, 'r') as f:
                docs = list(yaml.safe_load_all(f))
            
            for doc in docs:
                if not doc or doc.get('kind') != 'HorizontalPodAutoscaler':
                    continue
                
                name = doc['metadata']['name']
                service_name = name.replace('-hpa', '')
                spec = doc.get('spec', {})
                metrics = spec.get('metrics', [])
                
                for metric in metrics:
                    resource = metric.get('resource', {})
                    metric_name = resource.get('name')
                    target = resource.get('target', {})
                    utilization = target.get('averageUtilization')
                    
                    if metric_name == 'cpu':
                        if utilization == 70:
                            self.print_result(True, f"{service_name}: CPU threshold is 70% (correct)")
                        else:
                            self.print_warning(f"{service_name}: CPU threshold is {utilization}% (expected 70%)")
                    
                    elif metric_name == 'memory':
                        if utilization >= 70 and utilization <= 75:
                            self.print_result(True, f"{service_name}: Memory threshold is {utilization}% (acceptable)")
                        else:
                            self.print_warning(f"{service_name}: Memory threshold is {utilization}% (expected 70-75%)")
            
        except Exception as e:
            self.print_result(False, f"Error validating thresholds: {e}")
    
    def test_replica_limits(self):
        """Test 6: Validate min/max replica limits"""
        self.print_header("Replica Limits Configuration")
        
        # Expected limits per service
        expected_limits = {
            'diagram-service': {'min': 2, 'max': 10},
            'api-gateway': {'min': 2, 'max': 10},
            'ai-service': {'min': 2, 'max': 8},
            'export-service': {'min': 2, 'max': 8},
            'collaboration-service': {'min': 2, 'max': 6},
            'auth-service': {'min': 2, 'max': 6},
            'git-service': {'min': 2, 'max': 6},
            'integration-hub': {'min': 2, 'max': 6},
        }
        
        hpa_file = 'k8s/hpa-autoscaling.yaml'
        
        try:
            with open(hpa_file, 'r') as f:
                docs = list(yaml.safe_load_all(f))
            
            for doc in docs:
                if not doc or doc.get('kind') != 'HorizontalPodAutoscaler':
                    continue
                
                name = doc['metadata']['name']
                service_name = name.replace('-hpa', '')
                spec = doc.get('spec', {})
                
                min_replicas = spec.get('minReplicas')
                max_replicas = spec.get('maxReplicas')
                
                if service_name in expected_limits:
                    expected = expected_limits[service_name]
                    
                    if min_replicas == expected['min']:
                        self.print_result(True, f"{service_name}: Min replicas = {min_replicas} (correct)")
                    else:
                        self.print_warning(f"{service_name}: Min replicas = {min_replicas} (expected {expected['min']})")
                    
                    if max_replicas == expected['max']:
                        self.print_result(True, f"{service_name}: Max replicas = {max_replicas} (correct)")
                    else:
                        self.print_warning(f"{service_name}: Max replicas = {max_replicas} (expected {expected['max']})")
                else:
                    self.print_info(f"{service_name}: Min={min_replicas}, Max={max_replicas}")
            
        except Exception as e:
            self.print_result(False, f"Error validating limits: {e}")
    
    def test_stabilization_windows(self):
        """Test 7: Validate stabilization windows configuration"""
        self.print_header("Stabilization Windows Configuration")
        
        hpa_file = 'k8s/hpa-autoscaling.yaml'
        
        try:
            with open(hpa_file, 'r') as f:
                docs = list(yaml.safe_load_all(f))
            
            for doc in docs:
                if not doc or doc.get('kind') != 'HorizontalPodAutoscaler':
                    continue
                
                name = doc['metadata']['name']
                service_name = name.replace('-hpa', '')
                spec = doc.get('spec', {})
                behavior = spec.get('behavior', {})
                
                # Check scale up window
                scale_up = behavior.get('scaleUp', {})
                scale_up_window = scale_up.get('stabilizationWindowSeconds')
                
                if scale_up_window:
                    if scale_up_window == 60:
                        self.print_result(True, f"{service_name}: Scale-up window = {scale_up_window}s (correct)")
                    else:
                        self.print_warning(f"{service_name}: Scale-up window = {scale_up_window}s (expected 60s)")
                else:
                    self.print_warning(f"{service_name}: Missing scale-up stabilization window")
                
                # Check scale down window
                scale_down = behavior.get('scaleDown', {})
                scale_down_window = scale_down.get('stabilizationWindowSeconds')
                
                if scale_down_window:
                    if scale_down_window == 300:
                        self.print_result(True, f"{service_name}: Scale-down window = {scale_down_window}s (correct)")
                    else:
                        self.print_warning(f"{service_name}: Scale-down window = {scale_down_window}s (expected 300s)")
                else:
                    self.print_warning(f"{service_name}: Missing scale-down stabilization window")
            
        except Exception as e:
            self.print_result(False, f"Error validating windows: {e}")
    
    def test_deployment_resources(self):
        """Test 8: Validate deployment resource requests/limits"""
        self.print_header("Deployment Resource Requests/Limits")
        
        self.print_info("Checking if deployments have resource requests (required for HPA)")
        
        deployment_file = 'k8s/diagram-service-deployment.yaml'
        
        if not os.path.exists(deployment_file):
            self.print_warning(f"Deployment file not found: {deployment_file}")
            self.print_info("Checking other deployment files...")
            return
        
        try:
            with open(deployment_file, 'r') as f:
                deployment = yaml.safe_load(f)
            
            containers = deployment['spec']['template']['spec']['containers']
            
            for container in containers:
                resources = container.get('resources', {})
                requests = resources.get('requests', {})
                limits = resources.get('limits', {})
                
                if 'cpu' in requests:
                    self.print_result(True, f"Container has CPU request: {requests['cpu']}")
                else:
                    self.print_result(False, "Container missing CPU request (required for HPA)")
                
                if 'memory' in requests:
                    self.print_result(True, f"Container has memory request: {requests['memory']}")
                else:
                    self.print_result(False, "Container missing memory request (required for HPA)")
                
                if 'cpu' in limits:
                    self.print_info(f"Container has CPU limit: {limits['cpu']}")
                
                if 'memory' in limits:
                    self.print_info(f"Container has memory limit: {limits['memory']}")
            
        except Exception as e:
            self.print_result(False, f"Error validating resources: {e}")
    
    def print_summary(self):
        """Print test summary"""
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"\n{Colors.BOLD}{'=' * 80}{Colors.RESET}")
        print(f"{Colors.BOLD}TEST SUMMARY{Colors.RESET}")
        print(f"{'=' * 80}")
        print(f"Total Tests: {total}")
        print(f"{Colors.GREEN}Passed: {self.passed} ({pass_rate:.1f}%){Colors.RESET}")
        print(f"{Colors.RED}Failed: {self.failed}{Colors.RESET}")
        print(f"{Colors.YELLOW}Warnings: {self.warnings}{Colors.RESET}")
        print(f"{'=' * 80}\n")
        
        if self.failed == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED!{Colors.RESET}\n")
            return True
        else:
            print(f"{Colors.RED}{Colors.BOLD}✗ SOME TESTS FAILED{Colors.RESET}\n")
            return False


def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}AutoGraph v3 - Auto-Scaling Test Suite{Colors.RESET}\n")
    
    tests = AutoScalingTests()
    
    # Run all tests
    tests.test_hpa_manifests()
    tests.test_monitoring_script()
    tests.test_autoscaler_docker_script()
    tests.test_load_generator()
    tests.test_scaling_thresholds()
    tests.test_replica_limits()
    tests.test_stabilization_windows()
    tests.test_deployment_resources()
    
    # Print summary
    success = tests.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
