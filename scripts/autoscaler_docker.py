#!/usr/bin/env python3
"""
AutoGraph v3 - Docker Compose Auto-Scaling Controller

Automatically scales Docker Compose services based on CPU and memory metrics.
Simulates Kubernetes HPA behavior for local development.

Features:
- Monitors CPU and memory usage of all services
- Automatically starts new containers when thresholds exceeded
- Automatically stops containers when usage is low
- Respects min/max replica counts
- Implements stabilization windows to prevent flapping

Usage:
  python3 autoscaler_docker.py [--dry-run] [--interval 30]
"""

import argparse
import json
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# ANSI colors
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


# Service configuration
SERVICE_CONFIG = {
    'diagram-service': {
        'min': 2,
        'max': 10,
        'scale_up_threshold_cpu': 70.0,
        'scale_down_threshold_cpu': 30.0,
        'scale_up_threshold_memory': 70.0,
        'scale_down_threshold_memory': 30.0,
        'image': 'autograph/diagram-service:latest',
        'port': 8082,
        'compose_file': 'docker-compose.lb.yml',
        'service_name': 'diagram-service'
    },
    'ai-service': {
        'min': 2,
        'max': 8,
        'scale_up_threshold_cpu': 70.0,
        'scale_down_threshold_cpu': 30.0,
        'scale_up_threshold_memory': 75.0,
        'scale_down_threshold_memory': 30.0,
        'image': 'autograph/ai-service:latest',
        'port': 8084,
        'compose_file': 'docker-compose.lb.yml',
        'service_name': 'ai-service'
    },
    'collaboration-service': {
        'min': 2,
        'max': 6,
        'scale_up_threshold_cpu': 70.0,
        'scale_down_threshold_cpu': 30.0,
        'scale_up_threshold_memory': 70.0,
        'scale_down_threshold_memory': 30.0,
        'image': 'autograph/collaboration-service:latest',
        'port': 8083,
        'compose_file': 'docker-compose.lb.yml',
        'service_name': 'collaboration-service'
    },
}

SCALE_UP_WINDOW = 60  # seconds
SCALE_DOWN_WINDOW = 300  # seconds


class DockerAutoScaler:
    """Auto-scales Docker Compose services based on metrics"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.last_scale_up: Dict[str, datetime] = {}
        self.last_scale_down: Dict[str, datetime] = {}
        self.instance_counter: Dict[str, int] = defaultdict(int)
    
    def get_running_containers(self, service_prefix: str) -> List[str]:
        """Get list of running container names for a service"""
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name={service_prefix}', 
                 '--format', '{{.Names}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return []
            
            containers = [name.strip() for name in result.stdout.strip().split('\n') if name.strip()]
            return containers
            
        except Exception as e:
            print(f"{Colors.RED}Error getting containers: {e}{Colors.RESET}")
            return []
    
    def get_container_metrics(self, container_name: str) -> Optional[Dict]:
        """Get CPU and memory metrics for a container"""
        try:
            result = subprocess.run(
                ['docker', 'stats', '--no-stream', '--format', 
                 'json={{json .}}', container_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return None
            
            data = json.loads(result.stdout.strip())
            
            # Parse metrics
            cpu_str = data.get('CPUPerc', '0%').replace('%', '')
            cpu_percent = float(cpu_str)
            
            mem_str = data.get('MemPerc', '0%').replace('%', '')
            mem_percent = float(mem_str)
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': mem_percent,
                'name': container_name
            }
            
        except Exception as e:
            print(f"{Colors.YELLOW}Warning: Could not get metrics for {container_name}: {e}{Colors.RESET}")
            return None
    
    def get_service_metrics(self, service_name: str) -> Dict:
        """Get aggregated metrics for all instances of a service"""
        container_prefix = f'autograph-{service_name}'
        containers = self.get_running_containers(container_prefix)
        
        if not containers:
            return {
                'count': 0,
                'avg_cpu': 0.0,
                'avg_memory': 0.0,
                'instances': []
            }
        
        instances = []
        total_cpu = 0.0
        total_memory = 0.0
        
        for container in containers:
            metrics = self.get_container_metrics(container)
            if metrics:
                instances.append(metrics)
                total_cpu += metrics['cpu_percent']
                total_memory += metrics['memory_percent']
        
        count = len(instances)
        return {
            'count': count,
            'avg_cpu': total_cpu / count if count > 0 else 0.0,
            'avg_memory': total_memory / count if count > 0 else 0.0,
            'instances': instances
        }
    
    def can_scale_up(self, service_name: str) -> bool:
        """Check if enough time has passed since last scale up"""
        last_time = self.last_scale_up.get(service_name)
        if not last_time:
            return True
        
        elapsed = (datetime.now() - last_time).total_seconds()
        return elapsed >= SCALE_UP_WINDOW
    
    def can_scale_down(self, service_name: str) -> bool:
        """Check if enough time has passed since last scale down"""
        last_time = self.last_scale_down.get(service_name)
        if not last_time:
            return True
        
        elapsed = (datetime.now() - last_time).total_seconds()
        return elapsed >= SCALE_DOWN_WINDOW
    
    def scale_up(self, service_name: str, current_count: int) -> bool:
        """Scale up a service by adding one instance"""
        config = SERVICE_CONFIG.get(service_name)
        if not config:
            return False
        
        # Check max replicas
        if current_count >= config['max']:
            print(f"{Colors.YELLOW}  Cannot scale up {service_name}: already at max ({config['max']}){Colors.RESET}")
            return False
        
        # Check stabilization window
        if not self.can_scale_up(service_name):
            remaining = SCALE_UP_WINDOW - (datetime.now() - self.last_scale_up[service_name]).total_seconds()
            print(f"{Colors.YELLOW}  Waiting for stabilization: {int(remaining)}s remaining{Colors.RESET}")
            return False
        
        # Generate new instance number
        self.instance_counter[service_name] += 1
        instance_num = self.instance_counter[service_name]
        container_name = f"autograph-{service_name}-{instance_num}"
        
        print(f"{Colors.CYAN}  Scaling up {service_name}: {current_count} -> {current_count + 1}{Colors.RESET}")
        print(f"    New container: {container_name}")
        
        if self.dry_run:
            print(f"{Colors.YELLOW}    [DRY RUN] Would start container{Colors.RESET}")
            self.last_scale_up[service_name] = datetime.now()
            return True
        
        # Start new container
        try:
            # Get network and env from existing container
            existing = self.get_running_containers(f'autograph-{service_name}')[0]
            
            cmd = [
                'docker', 'run', '-d',
                '--name', container_name,
                '--network', 'autograph-v3_default',
                '-e', f'INSTANCE_ID={instance_num}',
                '-e', 'POSTGRES_HOST=postgres',
                '-e', 'REDIS_HOST=redis',
                '-e', 'MINIO_HOST=minio',
                f"{config['image']}"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"{Colors.GREEN}    ✓ Container started successfully{Colors.RESET}")
                self.last_scale_up[service_name] = datetime.now()
                return True
            else:
                print(f"{Colors.RED}    ✗ Failed to start container: {result.stderr}{Colors.RESET}")
                return False
                
        except Exception as e:
            print(f"{Colors.RED}    ✗ Error starting container: {e}{Colors.RESET}")
            return False
    
    def scale_down(self, service_name: str, current_count: int) -> bool:
        """Scale down a service by removing one instance"""
        config = SERVICE_CONFIG.get(service_name)
        if not config:
            return False
        
        # Check min replicas
        if current_count <= config['min']:
            print(f"{Colors.YELLOW}  Cannot scale down {service_name}: already at min ({config['min']}){Colors.RESET}")
            return False
        
        # Check stabilization window
        if not self.can_scale_down(service_name):
            remaining = SCALE_DOWN_WINDOW - (datetime.now() - self.last_scale_down[service_name]).total_seconds()
            print(f"{Colors.YELLOW}  Waiting for stabilization: {int(remaining)}s remaining{Colors.RESET}")
            return False
        
        # Get containers and remove the last one
        containers = self.get_running_containers(f'autograph-{service_name}')
        if not containers:
            return False
        
        # Remove the container with highest number
        container_to_remove = sorted(containers)[-1]
        
        print(f"{Colors.BLUE}  Scaling down {service_name}: {current_count} -> {current_count - 1}{Colors.RESET}")
        print(f"    Removing container: {container_to_remove}")
        
        if self.dry_run:
            print(f"{Colors.YELLOW}    [DRY RUN] Would stop and remove container{Colors.RESET}")
            self.last_scale_down[service_name] = datetime.now()
            return True
        
        # Stop and remove container
        try:
            # Stop gracefully
            subprocess.run(['docker', 'stop', container_to_remove], 
                          capture_output=True, timeout=30)
            
            # Remove
            result = subprocess.run(['docker', 'rm', container_to_remove], 
                                   capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"{Colors.GREEN}    ✓ Container removed successfully{Colors.RESET}")
                self.last_scale_down[service_name] = datetime.now()
                return True
            else:
                print(f"{Colors.RED}    ✗ Failed to remove container: {result.stderr}{Colors.RESET}")
                return False
                
        except Exception as e:
            print(f"{Colors.RED}    ✗ Error removing container: {e}{Colors.RESET}")
            return False
    
    def evaluate_and_scale(self, service_name: str):
        """Evaluate metrics and scale if needed"""
        config = SERVICE_CONFIG.get(service_name)
        if not config:
            return
        
        # Get metrics
        metrics = self.get_service_metrics(service_name)
        
        if metrics['count'] == 0:
            print(f"{Colors.YELLOW}No containers running for {service_name}{Colors.RESET}")
            return
        
        print(f"\n{Colors.BOLD}{service_name}{Colors.RESET}")
        print(f"  Instances: {metrics['count']}/{config['max']} (min: {config['min']})")
        print(f"  Avg CPU: {metrics['avg_cpu']:.1f}%")
        print(f"  Avg Memory: {metrics['avg_memory']:.1f}%")
        
        # Check scale up
        if (metrics['avg_cpu'] > config['scale_up_threshold_cpu'] or 
            metrics['avg_memory'] > config['scale_up_threshold_memory']):
            print(f"{Colors.RED}  → High resource usage detected!{Colors.RESET}")
            self.scale_up(service_name, metrics['count'])
        
        # Check scale down
        elif (metrics['avg_cpu'] < config['scale_down_threshold_cpu'] and 
              metrics['avg_memory'] < config['scale_down_threshold_memory']):
            print(f"{Colors.GREEN}  → Low resource usage detected{Colors.RESET}")
            self.scale_down(service_name, metrics['count'])
        
        else:
            print(f"{Colors.GREEN}  → Metrics within normal range{Colors.RESET}")
    
    def run(self, interval: int = 30):
        """Run auto-scaling loop"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}AutoGraph v3 - Docker Auto-Scaling Controller{Colors.RESET}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'ACTIVE'}")
        print(f"Interval: {interval}s")
        print(f"Services: {', '.join(SERVICE_CONFIG.keys())}")
        print(f"\nPress Ctrl+C to stop\n")
        
        try:
            while True:
                print("=" * 80)
                print(f"Evaluation cycle: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("=" * 80)
                
                for service_name in SERVICE_CONFIG.keys():
                    self.evaluate_and_scale(service_name)
                
                print(f"\n{Colors.CYAN}Next evaluation in {interval}s...{Colors.RESET}")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}Auto-scaler stopped by user{Colors.RESET}\n")


def main():
    parser = argparse.ArgumentParser(description='AutoGraph v3 Docker Auto-Scaling Controller')
    parser.add_argument('--dry-run', action='store_true',
                        help='Simulate scaling without actually starting/stopping containers')
    parser.add_argument('--interval', type=int, default=30,
                        help='Evaluation interval in seconds (default: 30)')
    
    args = parser.parse_args()
    
    autoscaler = DockerAutoScaler(dry_run=args.dry_run)
    autoscaler.run(interval=args.interval)


if __name__ == '__main__':
    main()
