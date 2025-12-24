#!/usr/bin/env python3
"""
AutoGraph v3 - Disaster Recovery Test Script

This script tests the disaster recovery plan by simulating various failure
scenarios and measuring recovery time (RTO) and data loss (RPO).

Usage:
    python test_disaster_recovery.py                    # Get DR status
    python test_disaster_recovery.py --simulate         # Run DR simulation
    python test_disaster_recovery.py --scenario=db_corruption  # Specific scenario
"""

import requests
import time
import sys
from datetime import datetime
from typing import Dict, Any, List

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# API Gateway base URL
API_BASE_URL = "http://localhost:8080"

def print_header(message: str):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")

def print_success(message: str):
    """Print a success message."""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")

def print_error(message: str):
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

def print_warning(message: str):
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")

def print_info(message: str):
    """Print an info message."""
    print(f"{Colors.OKBLUE}ℹ {message}{Colors.ENDC}")

def test_api_connectivity() -> bool:
    """Test API Gateway connectivity."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success("API Gateway is reachable")
            return True
        else:
            print_error(f"API Gateway returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"Cannot reach API Gateway: {e}")
        return False

def get_dr_status() -> Dict[str, Any]:
    """Get disaster recovery status."""
    print_header("Disaster Recovery Status")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/admin/dr/status", timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("success"):
            print_success("DR status retrieved successfully")
            
            # Display RTO/RPO targets
            print(f"\n{Colors.BOLD}Recovery Objectives:{Colors.ENDC}")
            print(f"  RTO (Recovery Time Objective): {data['rto_target_minutes']} minutes")
            print(f"  RPO (Recovery Point Objective): {data['rpo_target_minutes']} minutes")
            
            # Display database backup status
            print(f"\n{Colors.BOLD}Database Backups:{Colors.ENDC}")
            db_backups = data["database_backups"]
            print(f"  Count: {db_backups['count']}")
            print(f"  Latest: {db_backups['latest'] or 'None'}")
            status_color = Colors.OKGREEN if db_backups['status'] == 'healthy' else Colors.FAIL
            print(f"  Status: {status_color}{db_backups['status']}{Colors.ENDC}")
            
            # Display MinIO backup status
            print(f"\n{Colors.BOLD}MinIO Backups:{Colors.ENDC}")
            minio_backups = data["minio_backups"]
            print(f"  Count: {minio_backups['count']}")
            print(f"  Latest: {minio_backups['latest'] or 'None'}")
            status_color = Colors.OKGREEN if minio_backups['status'] == 'healthy' else Colors.FAIL
            print(f"  Status: {status_color}{minio_backups['status']}{Colors.ENDC}")
            
            # Display last DR test
            print(f"\n{Colors.BOLD}DR Testing:{Colors.ENDC}")
            print(f"  Last Test: {data['last_dr_test'] or 'Never'}")
            print(f"  Next Test: {data['next_dr_test'] or 'Not scheduled'}")
            
            return data
        else:
            print_error("Failed to retrieve DR status")
            return {}
            
    except requests.exceptions.RequestException as e:
        print_error(f"API request failed: {e}")
        return {}
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return {}

def simulate_disaster_recovery(scenario: str = "complete_failure") -> Dict[str, Any]:
    """Simulate a disaster recovery scenario."""
    print_header(f"Disaster Recovery Simulation: {scenario}")
    
    print_warning("Starting DR simulation...")
    print_warning("This will simulate service failures (but not actually stop services)")
    print()
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/admin/dr/simulate",
            params={"scenario": scenario},
            timeout=60
        )
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("success"):
            simulation = data["simulation"]
            
            print_success("DR simulation completed successfully")
            print()
            
            # Display simulation details
            print(f"{Colors.BOLD}Simulation Details:{Colors.ENDC}")
            print(f"  Scenario: {simulation['scenario']}")
            print(f"  Start Time: {simulation['start_time']}")
            print(f"  End Time: {simulation['end_time']}")
            print(f"  Total Duration: {simulation['total_duration_minutes']:.2f} minutes ({simulation['total_duration_seconds']:.1f} seconds)")
            print()
            
            # Display recovery steps
            print(f"{Colors.BOLD}Recovery Steps:{Colors.ENDC}")
            for step in simulation["steps"]:
                status_icon = "✓" if step["status"] == "completed" else "⚠" if step["status"] == "skipped" else "✗"
                status_color = Colors.OKGREEN if step["status"] == "completed" else Colors.WARNING if step["status"] == "skipped" else Colors.FAIL
                
                print(f"  {status_color}[{status_icon}] Step {step['step']}: {step['name']}{Colors.ENDC}")
                print(f"      Duration: {step['duration_seconds']:.1f}s")
                print(f"      Details: {step['details']}")
            print()
            
            # Display metrics
            metrics = simulation["metrics"]
            print(f"{Colors.BOLD}Recovery Metrics:{Colors.ENDC}")
            
            # RTO
            rto_met = metrics["rto_met"]
            rto_color = Colors.OKGREEN if rto_met else Colors.FAIL
            rto_icon = "✓" if rto_met else "✗"
            print(f"  {rto_color}[{rto_icon}] RTO: {metrics['actual_recovery_minutes']:.2f} / {metrics['rto_target_minutes']} minutes{Colors.ENDC}")
            
            # RPO
            rpo_met = metrics["rpo_met"]
            rpo_color = Colors.OKGREEN if rpo_met else Colors.FAIL
            rpo_icon = "✓" if rpo_met else "✗"
            print(f"  {rpo_color}[{rpo_icon}] RPO: {metrics['estimated_data_loss_minutes']} / {metrics['rpo_target_minutes']} minutes{Colors.ENDC}")
            
            # Steps
            print(f"  Total Steps: {metrics['total_steps']}")
            print(f"  Successful: {Colors.OKGREEN}{metrics['successful_steps']}{Colors.ENDC}")
            print(f"  Failed: {Colors.FAIL}{metrics['failed_steps']}{Colors.ENDC}")
            print()
            
            # Overall result
            if rto_met and rpo_met and metrics["failed_steps"] == 0:
                print_success("✓ DR simulation PASSED - All objectives met!")
            elif rto_met and rpo_met:
                print_warning("⚠ DR simulation PASSED with warnings - Some steps had issues")
            else:
                print_error("✗ DR simulation FAILED - Did not meet RTO/RPO objectives")
            
            return data
        else:
            print_error("DR simulation failed")
            return {}
            
    except requests.exceptions.RequestException as e:
        print_error(f"API request failed: {e}")
        return {}
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return {}
    finally:
        end_time = time.time()
        print()
        print_info(f"Test completed in {end_time - start_time:.2f} seconds")

def check_prerequisites() -> bool:
    """Check if all prerequisites are met for DR testing."""
    print_header("Prerequisites Check")
    
    all_ok = True
    
    # Check API Gateway
    if not test_api_connectivity():
        all_ok = False
    
    # Check database backups exist
    try:
        response = requests.get(f"{API_BASE_URL}/api/admin/backup/list", timeout=10)
        if response.status_code == 200:
            data = response.json()
            backup_count = data.get("count", 0)
            if backup_count > 0:
                print_success(f"Found {backup_count} database backup(s)")
            else:
                print_warning("No database backups found - DR testing may be limited")
        else:
            print_error("Could not check database backups")
            all_ok = False
    except Exception as e:
        print_error(f"Failed to check database backups: {e}")
        all_ok = False
    
    # Check MinIO backups exist
    try:
        response = requests.get(f"{API_BASE_URL}/api/admin/minio/backup/list", timeout=10)
        if response.status_code == 200:
            data = response.json()
            backup_count = data.get("count", 0)
            if backup_count > 0:
                print_success(f"Found {backup_count} MinIO backup(s)")
            else:
                print_warning("No MinIO backups found - DR testing may be limited")
        else:
            print_error("Could not check MinIO backups")
            all_ok = False
    except Exception as e:
        print_error(f"Failed to check MinIO backups: {e}")
        all_ok = False
    
    print()
    if all_ok:
        print_success("All prerequisites met")
    else:
        print_warning("Some prerequisites not met - tests may fail")
    
    return all_ok

def print_usage():
    """Print usage information."""
    print(f"""
{Colors.BOLD}AutoGraph v3 - Disaster Recovery Test Script{Colors.ENDC}

{Colors.BOLD}Usage:{Colors.ENDC}
    python test_disaster_recovery.py                          # Get DR status
    python test_disaster_recovery.py --simulate               # Run DR simulation
    python test_disaster_recovery.py --scenario=db_corruption # Specific scenario
    python test_disaster_recovery.py --help                   # Show this help

{Colors.BOLD}Available Scenarios:{Colors.ENDC}
    complete_failure   - Complete infrastructure failure (default)
    database_corruption - Database corruption requiring restore
    storage_loss       - MinIO storage loss requiring restore

{Colors.BOLD}Examples:{Colors.ENDC}
    # Check DR status and backup availability
    python test_disaster_recovery.py

    # Run complete DR simulation
    python test_disaster_recovery.py --simulate

    # Simulate database corruption scenario
    python test_disaster_recovery.py --simulate --scenario=database_corruption

{Colors.BOLD}Environment:{Colors.ENDC}
    API Gateway: {API_BASE_URL}
    """)

def main():
    """Main test function."""
    print_header("AutoGraph v3 - Disaster Recovery Test")
    
    # Parse command line arguments
    args = sys.argv[1:]
    
    if "--help" in args or "-h" in args:
        print_usage()
        return 0
    
    # Check prerequisites
    if not check_prerequisites():
        print_warning("Prerequisites not fully met, but continuing...")
        print()
    
    # Determine what to do
    simulate = "--simulate" in args
    scenario = "complete_failure"
    
    # Parse scenario
    for arg in args:
        if arg.startswith("--scenario="):
            scenario = arg.split("=")[1]
    
    if simulate:
        # Run simulation
        result = simulate_disaster_recovery(scenario)
        
        # Return exit code based on success
        if result and result.get("success"):
            simulation = result.get("simulation", {})
            metrics = simulation.get("metrics", {})
            if metrics.get("rto_met") and metrics.get("rpo_met") and metrics.get("failed_steps", 0) == 0:
                return 0  # Success
            else:
                return 1  # Failed metrics
        else:
            return 1  # Simulation failed
    else:
        # Just get status
        result = get_dr_status()
        return 0 if result else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        
        print()
        print_header("Test Summary")
        
        if exit_code == 0:
            print_success("✓ All tests passed")
        else:
            print_error("✗ Some tests failed")
        
        print()
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print()
        print_warning("Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print()
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
