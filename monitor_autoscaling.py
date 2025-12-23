#!/usr/bin/env python3
"""
AutoGraph v3 - Auto-Scaling Monitoring Script

Monitors CPU and memory usage of all microservices and simulates 
auto-scaling decisions based on thresholds.

For Kubernetes: Uses kubectl to get pod metrics
For Docker Compose: Uses docker stats to get container metrics

Thresholds:
- Scale up: CPU > 70% or Memory > 70%
- Scale down: CPU < 30% and Memory < 30%
- Min replicas: 2
- Max replicas: 10 (diagram, api-gateway), 8 (ai, export), 6 (others)

Usage:
  python3 monitor_autoscaling.py [--mode k8s|docker] [--duration 300] [--interval 10]
"""

import argparse
import json
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple


# ANSI color codes for pretty terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'


# Service scaling configuration
SERVICE_CONFIG = {
    'diagram-service': {'min': 2, 'max': 10, 'priority': 'high'},
    'api-gateway': {'min': 2, 'max': 10, 'priority': 'high'},
    'ai-service': {'min': 2, 'max': 8, 'priority': 'high'},
    'export-service': {'min': 2, 'max': 8, 'priority': 'medium'},
    'collaboration-service': {'min': 2, 'max': 6, 'priority': 'medium'},
    'auth-service': {'min': 2, 'max': 6, 'priority': 'medium'},
    'git-service': {'min': 2, 'max': 6, 'priority': 'low'},
    'integration-hub': {'min': 2, 'max': 6, 'priority': 'low'},
}

# Scaling thresholds
SCALE_UP_CPU_THRESHOLD = 70.0  # Scale up if CPU > 70%
SCALE_DOWN_CPU_THRESHOLD = 30.0  # Scale down if CPU < 30%
SCALE_UP_MEMORY_THRESHOLD = 70.0  # Scale up if Memory > 70%
SCALE_DOWN_MEMORY_THRESHOLD = 30.0  # Scale down if Memory < 30%

# Stabilization windows (seconds)
SCALE_UP_WINDOW = 60  # Wait 60s before scaling up
SCALE_DOWN_WINDOW = 300  # Wait 5 minutes before scaling down


class MetricsCollector:
    """Collects metrics from either Kubernetes or Docker Compose"""
    
    def __init__(self, mode: str = 'docker'):
        self.mode = mode
        self.history: Dict[str, List[Tuple[datetime, float, float, int]]] = defaultdict(list)
        # (timestamp, cpu_percent, memory_percent, replica_count)
        
    def get_docker_metrics(self) -> Dict[str, Dict]:
        """Get metrics from Docker Compose containers"""
        try:
            # Get container stats
            result = subprocess.run(
                ['docker', 'stats', '--no-stream', '--format', 
                 'json={{json .}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                print(f"{Colors.RED}Error getting Docker stats: {result.stderr}{Colors.RESET}")
                return {}
            
            metrics = {}
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                    
                try:
                    data = json.loads(line)
                    name = data.get('Name', '')
                    
                    # Filter AutoGraph services
                    if not name.startswith('autograph-'):
                        continue
                    
                    # Extract service name
                    service_name = name.replace('autograph-', '')
                    
                    # Parse CPU percentage (e.g., "0.50%" -> 0.5)
                    cpu_str = data.get('CPUPerc', '0%').replace('%', '')
                    cpu_percent = float(cpu_str)
                    
                    # Parse memory percentage (e.g., "1.23%" -> 1.23)
                    mem_str = data.get('MemPerc', '0%').replace('%', '')
                    mem_percent = float(mem_str)
                    
                    # Parse memory usage (e.g., "256MiB / 1GiB")
                    mem_usage = data.get('MemUsage', '0B / 0B')
                    
                    # Count instances (for load-balanced services)
                    if service_name not in metrics:
                        metrics[service_name] = {
                            'instances': [],
                            'total_cpu': 0.0,
                            'total_memory': 0.0,
                            'count': 0
                        }
                    
                    metrics[service_name]['instances'].append({
                        'name': name,
                        'cpu_percent': cpu_percent,
                        'memory_percent': mem_percent,
                        'memory_usage': mem_usage
                    })
                    metrics[service_name]['total_cpu'] += cpu_percent
                    metrics[service_name]['total_memory'] += mem_percent
                    metrics[service_name]['count'] += 1
                    
                except json.JSONDecodeError:
                    continue
                except (ValueError, KeyError) as e:
                    print(f"{Colors.YELLOW}Warning: Could not parse metrics for {name}: {e}{Colors.RESET}")
                    continue
            
            # Calculate averages
            for service in metrics.values():
                if service['count'] > 0:
                    service['avg_cpu'] = service['total_cpu'] / service['count']
                    service['avg_memory'] = service['total_memory'] / service['count']
                else:
                    service['avg_cpu'] = 0.0
                    service['avg_memory'] = 0.0
            
            return metrics
            
        except subprocess.TimeoutExpired:
            print(f"{Colors.RED}Timeout getting Docker stats{Colors.RESET}")
            return {}
        except Exception as e:
            print(f"{Colors.RED}Error collecting Docker metrics: {e}{Colors.RESET}")
            return {}
    
    def get_k8s_metrics(self) -> Dict[str, Dict]:
        """Get metrics from Kubernetes pods"""
        try:
            # Get pod metrics using kubectl top
            result = subprocess.run(
                ['kubectl', 'top', 'pods', '-n', 'autograph', '--no-headers'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                print(f"{Colors.RED}Error getting Kubernetes metrics: {result.stderr}{Colors.RESET}")
                return {}
            
            metrics = {}
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split()
                if len(parts) < 3:
                    continue
                
                pod_name = parts[0]
                cpu_raw = parts[1]  # e.g., "25m" or "1000m"
                memory_raw = parts[2]  # e.g., "256Mi" or "1Gi"
                
                # Extract service name from pod name (e.g., diagram-service-abc123)
                service_name = None
                for svc in SERVICE_CONFIG.keys():
                    if pod_name.startswith(svc):
                        service_name = svc
                        break
                
                if not service_name:
                    continue
                
                # Parse CPU (millicores to percent, assuming 1000m = 100% of 1 core)
                # For HPA, we compare against resource requests (250m = 25% of 1 core)
                cpu_m = float(cpu_raw.replace('m', ''))
                cpu_percent = (cpu_m / 250.0) * 100  # 250m is typical request
                
                # Parse memory (Mi to percent, assuming 256Mi = 100% of request)
                if memory_raw.endswith('Mi'):
                    mem_mi = float(memory_raw.replace('Mi', ''))
                    mem_percent = (mem_mi / 256.0) * 100  # 256Mi is typical request
                elif memory_raw.endswith('Gi'):
                    mem_gi = float(memory_raw.replace('Gi', ''))
                    mem_percent = (mem_gi * 1024 / 256.0) * 100
                else:
                    mem_percent = 0.0
                
                # Aggregate by service
                if service_name not in metrics:
                    metrics[service_name] = {
                        'instances': [],
                        'total_cpu': 0.0,
                        'total_memory': 0.0,
                        'count': 0
                    }
                
                metrics[service_name]['instances'].append({
                    'name': pod_name,
                    'cpu_percent': cpu_percent,
                    'memory_percent': mem_percent,
                    'cpu_raw': cpu_raw,
                    'memory_raw': memory_raw
                })
                metrics[service_name]['total_cpu'] += cpu_percent
                metrics[service_name]['total_memory'] += mem_percent
                metrics[service_name]['count'] += 1
            
            # Calculate averages
            for service in metrics.values():
                if service['count'] > 0:
                    service['avg_cpu'] = service['total_cpu'] / service['count']
                    service['avg_memory'] = service['total_memory'] / service['count']
                else:
                    service['avg_cpu'] = 0.0
                    service['avg_memory'] = 0.0
            
            return metrics
            
        except subprocess.TimeoutExpired:
            print(f"{Colors.RED}Timeout getting Kubernetes metrics{Colors.RESET}")
            return {}
        except Exception as e:
            print(f"{Colors.RED}Error collecting Kubernetes metrics: {e}{Colors.RESET}")
            return {}
    
    def collect(self) -> Dict[str, Dict]:
        """Collect metrics based on mode"""
        if self.mode == 'k8s':
            return self.get_k8s_metrics()
        else:
            return self.get_docker_metrics()
    
    def add_to_history(self, service: str, cpu: float, memory: float, replicas: int):
        """Add metrics to history"""
        self.history[service].append((datetime.now(), cpu, memory, replicas))
        
        # Keep only last 100 entries
        if len(self.history[service]) > 100:
            self.history[service] = self.history[service][-100:]


class AutoScaler:
    """Makes auto-scaling decisions based on metrics"""
    
    def __init__(self):
        self.scale_up_timestamps: Dict[str, datetime] = {}
        self.scale_down_timestamps: Dict[str, datetime] = {}
    
    def should_scale_up(self, service: str, cpu: float, memory: float, current_replicas: int) -> Tuple[bool, str]:
        """Determine if service should scale up"""
        config = SERVICE_CONFIG.get(service, {'min': 2, 'max': 6})
        
        # Check max replicas
        if current_replicas >= config['max']:
            return False, f"Already at max replicas ({config['max']})"
        
        # Check thresholds
        if cpu > SCALE_UP_CPU_THRESHOLD or memory > SCALE_UP_MEMORY_THRESHOLD:
            # Check stabilization window
            now = datetime.now()
            last_scale_up = self.scale_up_timestamps.get(service)
            
            if last_scale_up:
                elapsed = (now - last_scale_up).total_seconds()
                if elapsed < SCALE_UP_WINDOW:
                    return False, f"Waiting for stabilization ({int(SCALE_UP_WINDOW - elapsed)}s remaining)"
            
            # Scale up!
            self.scale_up_timestamps[service] = now
            reason = []
            if cpu > SCALE_UP_CPU_THRESHOLD:
                reason.append(f"CPU {cpu:.1f}% > {SCALE_UP_CPU_THRESHOLD}%")
            if memory > SCALE_UP_MEMORY_THRESHOLD:
                reason.append(f"Memory {memory:.1f}% > {SCALE_UP_MEMORY_THRESHOLD}%")
            return True, ", ".join(reason)
        
        return False, "Metrics within normal range"
    
    def should_scale_down(self, service: str, cpu: float, memory: float, current_replicas: int) -> Tuple[bool, str]:
        """Determine if service should scale down"""
        config = SERVICE_CONFIG.get(service, {'min': 2, 'max': 6})
        
        # Check min replicas
        if current_replicas <= config['min']:
            return False, f"Already at min replicas ({config['min']})"
        
        # Check thresholds (both must be low)
        if cpu < SCALE_DOWN_CPU_THRESHOLD and memory < SCALE_DOWN_MEMORY_THRESHOLD:
            # Check stabilization window
            now = datetime.now()
            last_scale_down = self.scale_down_timestamps.get(service)
            
            if last_scale_down:
                elapsed = (now - last_scale_down).total_seconds()
                if elapsed < SCALE_DOWN_WINDOW:
                    return False, f"Waiting for stabilization ({int(SCALE_DOWN_WINDOW - elapsed)}s remaining)"
            
            # Scale down!
            self.scale_down_timestamps[service] = now
            reason = f"CPU {cpu:.1f}% < {SCALE_DOWN_CPU_THRESHOLD}% and Memory {memory:.1f}% < {SCALE_DOWN_MEMORY_THRESHOLD}%"
            return True, reason
        
        return False, "Metrics too high for scale down"


def display_metrics(metrics: Dict[str, Dict], autoscaler: AutoScaler):
    """Display metrics and scaling decisions in a nice table"""
    print("\n" + "=" * 120)
    print(f"{Colors.BOLD}{Colors.CYAN}AutoGraph v3 - Auto-Scaling Monitor{Colors.RESET}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 120)
    
    # Table header
    print(f"\n{Colors.BOLD}{'Service':<25} {'Replicas':>10} {'Avg CPU':>10} {'Avg Memory':>12} {'Action':>15} {'Reason':<35}{Colors.RESET}")
    print("-" * 120)
    
    for service_name in sorted(metrics.keys()):
        service_metrics = metrics[service_name]
        replicas = service_metrics['count']
        avg_cpu = service_metrics['avg_cpu']
        avg_memory = service_metrics['avg_memory']
        
        # Determine scaling action
        should_up, up_reason = autoscaler.should_scale_up(service_name, avg_cpu, avg_memory, replicas)
        should_down, down_reason = autoscaler.should_scale_down(service_name, avg_cpu, avg_memory, replicas)
        
        # Color code based on status
        if should_up:
            action = f"{Colors.RED}SCALE UP{Colors.RESET}"
            reason = f"{Colors.RED}{up_reason}{Colors.RESET}"
            cpu_color = Colors.RED
            mem_color = Colors.RED if avg_memory > SCALE_UP_MEMORY_THRESHOLD else Colors.YELLOW
        elif should_down:
            action = f"{Colors.BLUE}SCALE DOWN{Colors.RESET}"
            reason = f"{Colors.BLUE}{down_reason}{Colors.RESET}"
            cpu_color = Colors.GREEN
            mem_color = Colors.GREEN
        else:
            action = f"{Colors.GREEN}STABLE{Colors.RESET}"
            reason = "Metrics within normal range"
            
            # Color code metrics
            if avg_cpu > SCALE_UP_CPU_THRESHOLD:
                cpu_color = Colors.RED
            elif avg_cpu > SCALE_DOWN_CPU_THRESHOLD:
                cpu_color = Colors.YELLOW
            else:
                cpu_color = Colors.GREEN
            
            if avg_memory > SCALE_UP_MEMORY_THRESHOLD:
                mem_color = Colors.RED
            elif avg_memory > SCALE_DOWN_MEMORY_THRESHOLD:
                mem_color = Colors.YELLOW
            else:
                mem_color = Colors.GREEN
        
        print(f"{service_name:<25} {replicas:>10} {cpu_color}{avg_cpu:>9.1f}%{Colors.RESET} {mem_color}{avg_memory:>11.1f}%{Colors.RESET} {action:>29} {reason:<35}")
    
    print("-" * 120)
    print(f"\n{Colors.BOLD}Thresholds:{Colors.RESET} Scale up: CPU > {SCALE_UP_CPU_THRESHOLD}% or Memory > {SCALE_UP_MEMORY_THRESHOLD}% | Scale down: CPU < {SCALE_DOWN_CPU_THRESHOLD}% and Memory < {SCALE_DOWN_MEMORY_THRESHOLD}%")
    print(f"{Colors.BOLD}Stabilization:{Colors.RESET} Scale up: {SCALE_UP_WINDOW}s | Scale down: {SCALE_DOWN_WINDOW}s")


def main():
    parser = argparse.ArgumentParser(description='AutoGraph v3 Auto-Scaling Monitor')
    parser.add_argument('--mode', choices=['k8s', 'docker'], default='docker',
                        help='Monitoring mode: k8s (Kubernetes) or docker (Docker Compose)')
    parser.add_argument('--duration', type=int, default=300,
                        help='Monitoring duration in seconds (default: 300, 0 for infinite)')
    parser.add_argument('--interval', type=int, default=10,
                        help='Polling interval in seconds (default: 10)')
    
    args = parser.parse_args()
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}Starting AutoGraph v3 Auto-Scaling Monitor{Colors.RESET}")
    print(f"Mode: {args.mode.upper()}")
    print(f"Duration: {'Infinite' if args.duration == 0 else f'{args.duration}s'}")
    print(f"Interval: {args.interval}s")
    print(f"\nPress Ctrl+C to stop monitoring\n")
    
    collector = MetricsCollector(mode=args.mode)
    autoscaler = AutoScaler()
    
    start_time = time.time()
    
    try:
        while True:
            # Collect metrics
            metrics = collector.collect()
            
            if not metrics:
                print(f"{Colors.YELLOW}No metrics collected. Are services running?{Colors.RESET}")
            else:
                # Display metrics and scaling decisions
                display_metrics(metrics, autoscaler)
                
                # Add to history
                for service_name, service_metrics in metrics.items():
                    collector.add_to_history(
                        service_name,
                        service_metrics['avg_cpu'],
                        service_metrics['avg_memory'],
                        service_metrics['count']
                    )
            
            # Check duration
            if args.duration > 0:
                elapsed = time.time() - start_time
                if elapsed >= args.duration:
                    print(f"\n{Colors.GREEN}Monitoring duration reached. Exiting.{Colors.RESET}")
                    break
            
            # Wait for next interval
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Monitoring stopped by user.{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Error during monitoring: {e}{Colors.RESET}")
        sys.exit(1)
    
    print(f"\n{Colors.GREEN}Monitoring session complete!{Colors.RESET}\n")


if __name__ == '__main__':
    main()
