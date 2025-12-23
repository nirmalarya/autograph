#!/usr/bin/env python3
"""
AutoGraph v3 - Load Generator for Auto-Scaling Testing

Generates varying CPU load to test auto-scaling behavior.
Can target specific services and generate different load patterns.

Usage:
  python3 load_generator.py --service diagram --pattern spike --duration 300
  python3 load_generator.py --service ai --pattern gradual --target-cpu 80
"""

import argparse
import concurrent.futures
import random
import requests
import sys
import time
from datetime import datetime
from typing import List


# ANSI colors
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


# Service endpoints
SERVICES = {
    'diagram': {
        'url': 'http://localhost:8082/health',
        'name': 'Diagram Service'
    },
    'ai': {
        'url': 'http://localhost:8084/health',
        'name': 'AI Service'
    },
    'collaboration': {
        'url': 'http://localhost:8083/health',
        'name': 'Collaboration Service'
    },
    'auth': {
        'url': 'http://localhost:8085/health',
        'name': 'Auth Service'
    },
    'export': {
        'url': 'http://localhost:8097/health',
        'name': 'Export Service'
    },
    'git': {
        'url': 'http://localhost:8087/health',
        'name': 'Git Service'
    },
    'integration': {
        'url': 'http://localhost:8099/health',
        'name': 'Integration Hub'
    },
}


class LoadGenerator:
    """Generates HTTP load to test auto-scaling"""
    
    def __init__(self, service: str, target_rps: int = 10):
        self.service = service
        self.target_rps = target_rps
        self.success_count = 0
        self.error_count = 0
        self.total_latency = 0.0
        
        if service not in SERVICES:
            raise ValueError(f"Unknown service: {service}")
        
        self.service_config = SERVICES[service]
    
    def send_request(self) -> bool:
        """Send a single HTTP request"""
        try:
            start_time = time.time()
            response = requests.get(
                self.service_config['url'],
                timeout=5
            )
            latency = (time.time() - start_time) * 1000  # ms
            
            self.total_latency += latency
            
            if response.status_code == 200:
                self.success_count += 1
                return True
            else:
                self.error_count += 1
                return False
                
        except Exception as e:
            self.error_count += 1
            return False
    
    def generate_constant_load(self, duration: int, rps: int):
        """Generate constant load at specified RPS"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}Constant Load Pattern{Colors.RESET}")
        print(f"Service: {self.service_config['name']}")
        print(f"Target RPS: {rps}")
        print(f"Duration: {duration}s")
        print(f"URL: {self.service_config['url']}")
        print(f"\nPress Ctrl+C to stop early\n")
        
        start_time = time.time()
        request_interval = 1.0 / rps
        
        try:
            while time.time() - start_time < duration:
                # Send burst of requests
                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    futures = [executor.submit(self.send_request) for _ in range(rps)]
                    concurrent.futures.wait(futures)
                
                # Wait for next second
                time.sleep(1.0)
                
                # Print stats every 10 seconds
                elapsed = int(time.time() - start_time)
                if elapsed % 10 == 0:
                    self.print_stats(elapsed)
        
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Load generation stopped by user{Colors.RESET}")
        
        self.print_final_stats(time.time() - start_time)
    
    def generate_spike_load(self, duration: int, base_rps: int, spike_rps: int, spike_duration: int):
        """Generate load with periodic spikes"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}Spike Load Pattern{Colors.RESET}")
        print(f"Service: {self.service_config['name']}")
        print(f"Base RPS: {base_rps}")
        print(f"Spike RPS: {spike_rps}")
        print(f"Spike Duration: {spike_duration}s")
        print(f"Total Duration: {duration}s")
        print(f"URL: {self.service_config['url']}")
        print(f"\nPress Ctrl+C to stop early\n")
        
        start_time = time.time()
        spike_interval = 60  # Spike every 60 seconds
        last_spike = 0
        in_spike = False
        spike_start = 0
        
        try:
            while time.time() - start_time < duration:
                elapsed = time.time() - start_time
                
                # Determine if we should be spiking
                if not in_spike and elapsed - last_spike >= spike_interval:
                    # Start spike
                    in_spike = True
                    spike_start = elapsed
                    current_rps = spike_rps
                    print(f"\n{Colors.RED}🔥 SPIKE STARTED at t={int(elapsed)}s (RPS: {spike_rps}){Colors.RESET}")
                
                elif in_spike and elapsed - spike_start >= spike_duration:
                    # End spike
                    in_spike = False
                    last_spike = elapsed
                    current_rps = base_rps
                    print(f"{Colors.GREEN}✓ Spike ended, returning to base load (RPS: {base_rps}){Colors.RESET}\n")
                
                else:
                    current_rps = spike_rps if in_spike else base_rps
                
                # Send burst
                with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                    futures = [executor.submit(self.send_request) for _ in range(current_rps)]
                    concurrent.futures.wait(futures)
                
                time.sleep(1.0)
                
                # Print stats every 10 seconds
                if int(elapsed) % 10 == 0:
                    self.print_stats(int(elapsed))
        
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Load generation stopped by user{Colors.RESET}")
        
        self.print_final_stats(time.time() - start_time)
    
    def generate_gradual_load(self, duration: int, start_rps: int, end_rps: int):
        """Generate gradually increasing/decreasing load"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}Gradual Load Pattern{Colors.RESET}")
        print(f"Service: {self.service_config['name']}")
        print(f"Start RPS: {start_rps}")
        print(f"End RPS: {end_rps}")
        print(f"Duration: {duration}s")
        print(f"URL: {self.service_config['url']}")
        print(f"\nPress Ctrl+C to stop early\n")
        
        start_time = time.time()
        rps_delta = (end_rps - start_rps) / duration
        
        try:
            while time.time() - start_time < duration:
                elapsed = time.time() - start_time
                current_rps = int(start_rps + (rps_delta * elapsed))
                
                # Send burst
                with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                    futures = [executor.submit(self.send_request) for _ in range(current_rps)]
                    concurrent.futures.wait(futures)
                
                time.sleep(1.0)
                
                # Print stats every 10 seconds
                if int(elapsed) % 10 == 0:
                    self.print_stats(int(elapsed), current_rps)
        
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Load generation stopped by user{Colors.RESET}")
        
        self.print_final_stats(time.time() - start_time)
    
    def generate_random_load(self, duration: int, min_rps: int, max_rps: int):
        """Generate random varying load"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}Random Load Pattern{Colors.RESET}")
        print(f"Service: {self.service_config['name']}")
        print(f"RPS Range: {min_rps}-{max_rps}")
        print(f"Duration: {duration}s")
        print(f"URL: {self.service_config['url']}")
        print(f"\nPress Ctrl+C to stop early\n")
        
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration:
                elapsed = time.time() - start_time
                current_rps = random.randint(min_rps, max_rps)
                
                # Send burst
                with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                    futures = [executor.submit(self.send_request) for _ in range(current_rps)]
                    concurrent.futures.wait(futures)
                
                time.sleep(1.0)
                
                # Print stats every 10 seconds
                if int(elapsed) % 10 == 0:
                    self.print_stats(int(elapsed), current_rps)
        
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Load generation stopped by user{Colors.RESET}")
        
        self.print_final_stats(time.time() - start_time)
    
    def print_stats(self, elapsed: int, current_rps: int = None):
        """Print current statistics"""
        total_requests = self.success_count + self.error_count
        success_rate = (self.success_count / total_requests * 100) if total_requests > 0 else 0
        avg_latency = (self.total_latency / self.success_count) if self.success_count > 0 else 0
        
        stats_line = f"[t={elapsed}s] Requests: {total_requests} | Success: {self.success_count} ({success_rate:.1f}%) | Errors: {self.error_count} | Avg Latency: {avg_latency:.1f}ms"
        
        if current_rps:
            stats_line += f" | Current RPS: {current_rps}"
        
        print(stats_line)
    
    def print_final_stats(self, duration: float):
        """Print final statistics"""
        total_requests = self.success_count + self.error_count
        success_rate = (self.success_count / total_requests * 100) if total_requests > 0 else 0
        avg_latency = (self.total_latency / self.success_count) if self.success_count > 0 else 0
        actual_rps = total_requests / duration if duration > 0 else 0
        
        print(f"\n{Colors.BOLD}{'=' * 80}{Colors.RESET}")
        print(f"{Colors.BOLD}Final Statistics{Colors.RESET}")
        print(f"{'=' * 80}")
        print(f"Duration: {duration:.1f}s")
        print(f"Total Requests: {total_requests}")
        print(f"Successful: {Colors.GREEN}{self.success_count} ({success_rate:.1f}%){Colors.RESET}")
        print(f"Failed: {Colors.RED}{self.error_count} ({100-success_rate:.1f}%){Colors.RESET}")
        print(f"Average Latency: {avg_latency:.1f}ms")
        print(f"Actual RPS: {actual_rps:.1f}")
        print(f"{'=' * 80}\n")


def main():
    parser = argparse.ArgumentParser(description='AutoGraph v3 Load Generator for Auto-Scaling Testing')
    parser.add_argument('--service', required=True, choices=list(SERVICES.keys()),
                        help='Target service to load test')
    parser.add_argument('--pattern', default='constant',
                        choices=['constant', 'spike', 'gradual', 'random'],
                        help='Load pattern (default: constant)')
    parser.add_argument('--duration', type=int, default=300,
                        help='Test duration in seconds (default: 300)')
    parser.add_argument('--rps', type=int, default=50,
                        help='Requests per second for constant pattern (default: 50)')
    parser.add_argument('--base-rps', type=int, default=10,
                        help='Base RPS for spike pattern (default: 10)')
    parser.add_argument('--spike-rps', type=int, default=100,
                        help='Spike RPS for spike pattern (default: 100)')
    parser.add_argument('--spike-duration', type=int, default=30,
                        help='Spike duration in seconds (default: 30)')
    parser.add_argument('--start-rps', type=int, default=10,
                        help='Start RPS for gradual pattern (default: 10)')
    parser.add_argument('--end-rps', type=int, default=100,
                        help='End RPS for gradual pattern (default: 100)')
    parser.add_argument('--min-rps', type=int, default=10,
                        help='Min RPS for random pattern (default: 10)')
    parser.add_argument('--max-rps', type=int, default=100,
                        help='Max RPS for random pattern (default: 100)')
    
    args = parser.parse_args()
    
    # Create load generator
    generator = LoadGenerator(args.service, args.rps)
    
    # Run selected pattern
    if args.pattern == 'constant':
        generator.generate_constant_load(args.duration, args.rps)
    
    elif args.pattern == 'spike':
        generator.generate_spike_load(
            args.duration,
            args.base_rps,
            args.spike_rps,
            args.spike_duration
        )
    
    elif args.pattern == 'gradual':
        generator.generate_gradual_load(
            args.duration,
            args.start_rps,
            args.end_rps
        )
    
    elif args.pattern == 'random':
        generator.generate_random_load(
            args.duration,
            args.min_rps,
            args.max_rps
        )


if __name__ == '__main__':
    main()
