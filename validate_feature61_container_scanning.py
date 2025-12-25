#!/usr/bin/env python3
"""
Feature #61 Validation: Container Image Scanning with Trivy

Tests:
1. Trivy Docker image is available
2. All service images exist
3. Trivy can scan images successfully
4. Scan results are generated
5. No critical vulnerabilities exist
6. Scan script works correctly
7. GitHub Actions workflow exists
8. Pre-commit hook exists
"""

import subprocess
import json
import os
import sys
from pathlib import Path


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_test(message, status="info"):
    """Print formatted test message"""
    if status == "pass":
        print(f"{Colors.GREEN}✓{Colors.END} {message}")
        return True
    elif status == "fail":
        print(f"{Colors.RED}✗{Colors.END} {message}")
        return False
    elif status == "warn":
        print(f"{Colors.YELLOW}⚠{Colors.END} {message}")
        return True
    else:
        print(f"{Colors.BLUE}ℹ{Colors.END} {message}")
        return True


def run_command(cmd, check=True, timeout=60):
    """Run shell command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=check
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr
    except Exception as e:
        return False, "", str(e)


def test_trivy_available():
    """Test 1: Trivy Docker image is available"""
    print_test("Test 1: Checking Trivy Docker image availability")

    success, stdout, stderr = run_command(
        "docker images aquasec/trivy:latest --format '{{.Repository}}:{{.Tag}}'",
        check=False
    )

    if success and "aquasec/trivy:latest" in stdout:
        return print_test("Trivy Docker image is available", "pass")
    else:
        return print_test("Trivy Docker image not found", "fail")


def test_service_images_exist():
    """Test 2: All service images exist"""
    print_test("Test 2: Checking service images exist")

    services = [
        "api-gateway",
        "auth-service",
        "diagram-service",
        "collaboration-service",
        "ai-service",
        "git-service",
        "export-service",
        "integration-hub"
    ]

    all_exist = True
    for service in services:
        success, stdout, stderr = run_command(
            f"docker images autograph-{service}:latest --format '{{{{.Repository}}}}:{{{{.Tag}}}}'",
            check=False
        )

        if success and f"autograph-{service}:latest" in stdout:
            print_test(f"  Image exists: autograph-{service}:latest", "pass")
        else:
            print_test(f"  Image missing: autograph-{service}:latest", "fail")
            all_exist = False

    return all_exist


def test_trivy_scan_works():
    """Test 3: Trivy can scan images successfully"""
    print_test("Test 3: Testing Trivy scan functionality")

    # Test scan on api-gateway
    success, stdout, stderr = run_command(
        "docker run --rm -v /var/run/docker.sock:/var/run/docker.sock "
        "-e TRIVY_INSECURE=true aquasec/trivy:latest image "
        "--format json --quiet autograph-api-gateway:latest",
        check=False,
        timeout=120
    )

    if success:
        try:
            # Verify output is valid JSON
            json.loads(stdout)
            return print_test("Trivy scan executed successfully", "pass")
        except json.JSONDecodeError:
            return print_test("Trivy scan produced invalid JSON", "fail")
    else:
        return print_test(f"Trivy scan failed: {stderr[:100]}", "fail")


def test_scan_results_exist():
    """Test 4: Scan results are generated"""
    print_test("Test 4: Checking scan result files exist")

    results_dir = Path("trivy_results")
    if not results_dir.exists():
        return print_test("Results directory doesn't exist", "fail")

    # Check for summary JSON
    summary_file = results_dir / "scan_summary.json"
    if not summary_file.exists():
        return print_test("Summary file doesn't exist", "fail")

    # Check for individual service scans
    services = [
        "api-gateway", "auth-service", "diagram-service",
        "collaboration-service", "ai-service", "git-service",
        "export-service", "integration-hub"
    ]

    all_exist = True
    for service in services:
        scan_file = results_dir / f"{service}_scan.json"
        if scan_file.exists():
            print_test(f"  Scan result exists: {service}", "pass")
        else:
            print_test(f"  Scan result missing: {service}", "fail")
            all_exist = False

    return all_exist


def test_no_critical_vulnerabilities():
    """Test 5: No critical vulnerabilities exist"""
    print_test("Test 5: Checking for critical vulnerabilities")

    summary_file = Path("trivy_results/scan_summary.json")
    if not summary_file.exists():
        return print_test("Summary file not found", "fail")

    try:
        with open(summary_file, 'r') as f:
            data = json.load(f)

        summary = data.get("summary", {})
        critical_count = summary.get("services_with_critical", -1)
        high_count = summary.get("services_with_high", -1)
        clean_count = summary.get("services_clean", 0)

        print_test(f"  Services with CRITICAL: {critical_count}", "info")
        print_test(f"  Services with HIGH: {high_count}", "info")
        print_test(f"  Services clean: {clean_count}", "info")

        if critical_count == 0:
            return print_test("No critical vulnerabilities found", "pass")
        else:
            return print_test(f"Found {critical_count} services with critical vulnerabilities", "fail")

    except Exception as e:
        return print_test(f"Error reading summary: {e}", "fail")


def test_scan_script_exists():
    """Test 6: Scan script exists and is executable"""
    print_test("Test 6: Checking scan script")

    script_path = Path("scripts/trivy_scan_all.sh")

    if not script_path.exists():
        return print_test("Scan script doesn't exist", "fail")

    if not os.access(script_path, os.X_OK):
        return print_test("Scan script is not executable", "fail")

    # Check script has proper content
    with open(script_path, 'r') as f:
        content = f.read()

    if "aquasec/trivy" in content and "docker run" in content:
        return print_test("Scan script exists and looks valid", "pass")
    else:
        return print_test("Scan script missing required content", "fail")


def test_github_workflow_exists():
    """Test 7: GitHub Actions workflow exists"""
    print_test("Test 7: Checking GitHub Actions workflow")

    workflow_path = Path(".github/workflows/container-scan.yml")

    if not workflow_path.exists():
        return print_test("Container scan workflow doesn't exist", "fail")

    with open(workflow_path, 'r') as f:
        content = f.read()

    required_elements = [
        "trivy-action",
        "aquasecurity/trivy-action",
        "matrix:",
        "service:"
    ]

    missing = []
    for element in required_elements:
        if element not in content:
            missing.append(element)

    if missing:
        return print_test(f"Workflow missing elements: {', '.join(missing)}", "fail")

    return print_test("GitHub Actions workflow exists and looks valid", "pass")


def test_precommit_hook_exists():
    """Test 8: Pre-commit hook exists"""
    print_test("Test 8: Checking pre-commit hook")

    hook_path = Path(".pre-commit-trivy.sh")

    if not hook_path.exists():
        return print_test("Pre-commit hook doesn't exist", "fail")

    if not os.access(hook_path, os.X_OK):
        return print_test("Pre-commit hook is not executable", "fail")

    with open(hook_path, 'r') as f:
        content = f.read()

    if "trivy" in content.lower() and "docker run" in content:
        return print_test("Pre-commit hook exists and looks valid", "pass")
    else:
        return print_test("Pre-commit hook missing required content", "fail")


def main():
    """Run all validation tests"""
    print("=" * 60)
    print("Feature #61 Validation: Container Image Scanning")
    print("=" * 60)
    print()

    tests = [
        ("Trivy Available", test_trivy_available),
        ("Service Images Exist", test_service_images_exist),
        ("Trivy Scan Works", test_trivy_scan_works),
        ("Scan Results Exist", test_scan_results_exist),
        ("No Critical Vulnerabilities", test_no_critical_vulnerabilities),
        ("Scan Script Exists", test_scan_script_exists),
        ("GitHub Workflow Exists", test_github_workflow_exists),
        ("Pre-commit Hook Exists", test_precommit_hook_exists),
    ]

    results = []
    for test_name, test_func in tests:
        print()
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_test(f"Test error: {e}", "fail")
            results.append((test_name, False))

    # Print summary
    print()
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"  {test_name}: {status}")

    print()
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print(f"{Colors.GREEN}✓ Feature #61: PASSING{Colors.END}")
        return 0
    else:
        print(f"{Colors.RED}✗ Feature #61: FAILING{Colors.END}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
