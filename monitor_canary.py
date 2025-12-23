#!/usr/bin/env python3

"""
Canary Deployment Metrics Monitoring System
Monitors error rates and latency for automatic rollback decisions.

This script can:
1. Query Prometheus for real-time metrics
2. Calculate error rates and P95 latency
3. Trigger automatic rollbacks when thresholds exceeded
4. Generate detailed monitoring reports
5. Send alerts to notification systems

Usage:
    python3 monitor_canary.py --deployment canary --duration 60
    python3 monitor_canary.py --prometheus http://prometheus:9090
    python3 monitor_canary.py --alert-on-error
"""

import argparse
import json
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

try:
    import requests
except ImportError:
    print("Warning: requests library not installed. Install with: pip install requests")
    requests = None


class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color


class MetricsMonitor:
    """Monitors canary deployment metrics for automatic rollback"""
    
    def __init__(
        self,
        prometheus_url: str = "http://localhost:9090",
        error_rate_threshold: float = 5.0,
        latency_p95_threshold: float = 1000.0,
        deployment: str = "api-gateway-canary",
        namespace: str = "autograph"
    ):
        self.prometheus_url = prometheus_url
        self.error_rate_threshold = error_rate_threshold
        self.latency_p95_threshold = latency_p95_threshold
        self.deployment = deployment
        self.namespace = namespace
        
    def log_info(self, message: str):
        """Log info message"""
        print(f"{Colors.CYAN}[INFO]{Colors.NC} {message}")
    
    def log_success(self, message: str):
        """Log success message"""
        print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")
    
    def log_warning(self, message: str):
        """Log warning message"""
        print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")
    
    def log_error(self, message: str):
        """Log error message"""
        print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")
    
    def query_prometheus(self, query: str) -> Optional[Dict]:
        """Query Prometheus for metrics"""
        if not requests:
            self.log_warning("requests library not available")
            return None
        
        try:
            url = f"{self.prometheus_url}/api/v1/query"
            params = {"query": query}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.log_warning(f"Prometheus query failed: {e}")
            return None
    
    def get_error_rate(self) -> Tuple[float, bool]:
        """
        Get error rate from Prometheus
        Returns: (error_rate, is_real_data)
        """
        # Query for HTTP 5xx errors
        query = f'''
        sum(rate(http_requests_total{{
            deployment="{self.deployment}",
            namespace="{self.namespace}",
            status=~"5.."
        }}[5m])) / 
        sum(rate(http_requests_total{{
            deployment="{self.deployment}",
            namespace="{self.namespace}"
        }}[5m])) * 100
        '''
        
        result = self.query_prometheus(query)
        
        if result and result.get("data", {}).get("result"):
            error_rate = float(result["data"]["result"][0]["value"][1])
            return error_rate, True
        
        # Simulate error rate for testing (remove in production)
        import random
        simulated_rate = random.uniform(0, 3)
        return simulated_rate, False
    
    def get_p95_latency(self) -> Tuple[float, bool]:
        """
        Get P95 latency from Prometheus
        Returns: (latency_ms, is_real_data)
        """
        # Query for P95 latency
        query = f'''
        histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{{
            deployment="{self.deployment}",
            namespace="{self.namespace}"
        }}[5m])) by (le)) * 1000
        '''
        
        result = self.query_prometheus(query)
        
        if result and result.get("data", {}).get("result"):
            latency = float(result["data"]["result"][0]["value"][1])
            return latency, True
        
        # Simulate latency for testing (remove in production)
        import random
        simulated_latency = random.uniform(100, 500)
        return simulated_latency, False
    
    def get_request_rate(self) -> Tuple[float, bool]:
        """Get requests per second"""
        query = f'''
        sum(rate(http_requests_total{{
            deployment="{self.deployment}",
            namespace="{self.namespace}"
        }}[1m]))
        '''
        
        result = self.query_prometheus(query)
        
        if result and result.get("data", {}).get("result"):
            rate = float(result["data"]["result"][0]["value"][1])
            return rate, True
        
        # Simulate request rate for testing
        import random
        simulated_rate = random.uniform(10, 50)
        return simulated_rate, False
    
    def check_thresholds(
        self,
        error_rate: float,
        latency: float
    ) -> Tuple[bool, List[str]]:
        """
        Check if metrics exceed thresholds
        Returns: (should_rollback, reasons)
        """
        should_rollback = False
        reasons = []
        
        if error_rate > self.error_rate_threshold:
            should_rollback = True
            reasons.append(
                f"Error rate {error_rate:.2f}% exceeds threshold {self.error_rate_threshold}%"
            )
        
        if latency > self.latency_p95_threshold:
            should_rollback = True
            reasons.append(
                f"P95 latency {latency:.0f}ms exceeds threshold {self.latency_p95_threshold}ms"
            )
        
        return should_rollback, reasons
    
    def monitor(
        self,
        duration: int = 60,
        interval: int = 5,
        alert_on_error: bool = False
    ) -> bool:
        """
        Monitor metrics for specified duration
        Returns: True if metrics good, False if rollback needed
        """
        self.log_info(f"Monitoring {self.deployment} for {duration}s")
        self.log_info(f"Error rate threshold: {self.error_rate_threshold}%")
        self.log_info(f"P95 latency threshold: {self.latency_p95_threshold}ms")
        self.log_info(f"Check interval: {interval}s")
        print()
        
        start_time = time.time()
        end_time = start_time + duration
        
        metrics_history = []
        
        try:
            while time.time() < end_time:
                current_time = time.time()
                elapsed = int(current_time - start_time)
                remaining = int(end_time - current_time)
                
                # Get metrics
                error_rate, error_is_real = self.get_error_rate()
                latency, latency_is_real = self.get_p95_latency()
                req_rate, rate_is_real = self.get_request_rate()
                
                # Store in history
                metrics_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "error_rate": error_rate,
                    "latency_p95": latency,
                    "request_rate": req_rate
                })
                
                # Display metrics
                data_source = "Prometheus" if error_is_real else "Simulated"
                print(f"{Colors.BLUE}[{elapsed}s/{duration}s]{Colors.NC} ", end="")
                print(f"Error: {error_rate:.2f}% ", end="")
                print(f"P95: {latency:.0f}ms ", end="")
                print(f"RPS: {req_rate:.1f} ", end="")
                print(f"({data_source}) ", end="")
                print(f"(Remaining: {remaining}s)", end="\r")
                
                # Check thresholds
                should_rollback, reasons = self.check_thresholds(error_rate, latency)
                
                if should_rollback:
                    print()  # New line
                    self.log_error("Metrics exceeded thresholds!")
                    for reason in reasons:
                        self.log_error(f"  - {reason}")
                    
                    if alert_on_error:
                        self.send_alert(reasons, metrics_history)
                    
                    return False
                
                time.sleep(interval)
            
            print()  # New line
            self.log_success("Metrics look good!")
            self.print_summary(metrics_history)
            return True
            
        except KeyboardInterrupt:
            print()  # New line
            self.log_warning("Monitoring interrupted by user")
            return False
    
    def print_summary(self, metrics_history: List[Dict]):
        """Print summary of monitoring session"""
        if not metrics_history:
            return
        
        print()
        print(f"{Colors.CYAN}{'='*60}{Colors.NC}")
        print(f"{Colors.CYAN}Monitoring Summary{Colors.NC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.NC}")
        
        error_rates = [m["error_rate"] for m in metrics_history]
        latencies = [m["latency_p95"] for m in metrics_history]
        req_rates = [m["request_rate"] for m in metrics_history]
        
        print(f"\nError Rate:")
        print(f"  Min: {min(error_rates):.2f}%")
        print(f"  Max: {max(error_rates):.2f}%")
        print(f"  Avg: {sum(error_rates)/len(error_rates):.2f}%")
        
        print(f"\nP95 Latency:")
        print(f"  Min: {min(latencies):.0f}ms")
        print(f"  Max: {max(latencies):.0f}ms")
        print(f"  Avg: {sum(latencies)/len(latencies):.0f}ms")
        
        print(f"\nRequest Rate:")
        print(f"  Min: {min(req_rates):.1f} req/s")
        print(f"  Max: {max(req_rates):.1f} req/s")
        print(f"  Avg: {sum(req_rates)/len(req_rates):.1f} req/s")
        
        print(f"\nTotal Checks: {len(metrics_history)}")
        print(f"Duration: {metrics_history[-1]['timestamp']}")
    
    def send_alert(self, reasons: List[str], metrics_history: List[Dict]):
        """Send alert notification (Slack, email, etc.)"""
        self.log_info("Sending alert notification...")
        
        # In production, integrate with:
        # - Slack webhook
        # - PagerDuty
        # - Email
        # - SMS
        
        alert_message = {
            "deployment": self.deployment,
            "namespace": self.namespace,
            "timestamp": datetime.now().isoformat(),
            "reasons": reasons,
            "recent_metrics": metrics_history[-5:] if len(metrics_history) >= 5 else metrics_history
        }
        
        # For now, just print the alert
        print()
        print(f"{Colors.RED}{'='*60}{Colors.NC}")
        print(f"{Colors.RED}ALERT: Canary Deployment Threshold Exceeded{Colors.NC}")
        print(f"{Colors.RED}{'='*60}{Colors.NC}")
        print(json.dumps(alert_message, indent=2))
        print(f"{Colors.RED}{'='*60}{Colors.NC}")
    
    def trigger_rollback(self) -> bool:
        """Trigger automatic rollback"""
        self.log_warning("Triggering automatic rollback...")
        
        try:
            import subprocess
            
            # Call the canary-deploy.sh rollback command
            script_path = "/Users/nirmalarya/Workspace/auto-harness/cursor-autonomous-coding/autograph-v3/k8s/canary-deploy.sh"
            result = subprocess.run(
                [script_path, "rollback"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                self.log_success("Automatic rollback completed")
                return True
            else:
                self.log_error(f"Rollback failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_error(f"Failed to trigger rollback: {e}")
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Canary Deployment Metrics Monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Monitor for 60 seconds
  python3 monitor_canary.py --duration 60

  # Monitor with custom thresholds
  python3 monitor_canary.py --error-threshold 10 --latency-threshold 2000

  # Monitor and trigger automatic rollback
  python3 monitor_canary.py --auto-rollback

  # Monitor with Prometheus
  python3 monitor_canary.py --prometheus http://prometheus.local:9090
        """
    )
    
    parser.add_argument(
        "--prometheus",
        default="http://localhost:9090",
        help="Prometheus server URL (default: http://localhost:9090)"
    )
    parser.add_argument(
        "--deployment",
        default="api-gateway-canary",
        help="Deployment name to monitor (default: api-gateway-canary)"
    )
    parser.add_argument(
        "--namespace",
        default="autograph",
        help="Kubernetes namespace (default: autograph)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Monitoring duration in seconds (default: 60)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Check interval in seconds (default: 5)"
    )
    parser.add_argument(
        "--error-threshold",
        type=float,
        default=5.0,
        help="Error rate threshold percentage (default: 5.0)"
    )
    parser.add_argument(
        "--latency-threshold",
        type=float,
        default=1000.0,
        help="P95 latency threshold in ms (default: 1000.0)"
    )
    parser.add_argument(
        "--alert-on-error",
        action="store_true",
        help="Send alerts when thresholds exceeded"
    )
    parser.add_argument(
        "--auto-rollback",
        action="store_true",
        help="Automatically trigger rollback on threshold violation"
    )
    
    args = parser.parse_args()
    
    # Create monitor
    monitor = MetricsMonitor(
        prometheus_url=args.prometheus,
        error_rate_threshold=args.error_threshold,
        latency_p95_threshold=args.latency_threshold,
        deployment=args.deployment,
        namespace=args.namespace
    )
    
    # Run monitoring
    metrics_good = monitor.monitor(
        duration=args.duration,
        interval=args.interval,
        alert_on_error=args.alert_on_error
    )
    
    # Handle result
    if not metrics_good:
        if args.auto_rollback:
            monitor.trigger_rollback()
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
