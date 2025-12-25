#!/usr/bin/env python3
"""
Feature #46 Validation: Service dependency mapping for architecture visualization

Tests all 8 steps:
1. Analyze service-to-service calls
2. Generate dependency graph
3. Verify frontend → api-gateway edge
4. Verify api-gateway → auth-service edge
5. Verify api-gateway → diagram-service edge
6. Identify circular dependencies
7. Visualize critical path
8. Test dependency health checks
"""

import requests
import json
import sys
from datetime import datetime

# API endpoint
BASE_URL = "http://localhost:8080"
DEPENDENCIES_URL = f"{BASE_URL}/dependencies"

def print_step(step_num, description):
    """Print step header."""
    print(f"\n{'='*80}")
    print(f"Step {step_num}: {description}")
    print(f"{'='*80}")

def test_step_1_analyze_service_calls():
    """Step 1: Analyze service-to-service calls"""
    print_step(1, "Analyze service-to-service calls")

    try:
        response = requests.get(DEPENDENCIES_URL, timeout=10)

        if response.status_code != 200:
            print(f"❌ FAILED: API returned status {response.status_code}")
            return False

        data = response.json()

        # Verify response structure
        if "graph" not in data:
            print("❌ FAILED: Response missing 'graph' field")
            return False

        nodes = data["graph"].get("nodes", [])
        edges = data["graph"].get("edges", [])

        print(f"✅ SUCCESS: Found {len(nodes)} services and {len(edges)} dependencies")
        print(f"   Total services: {data['graph']['total_services']}")
        print(f"   Total dependencies: {data['graph']['total_dependencies']}")

        return True

    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

def test_step_2_generate_dependency_graph():
    """Step 2: Generate dependency graph"""
    print_step(2, "Generate dependency graph")

    try:
        response = requests.get(DEPENDENCIES_URL, timeout=10)
        data = response.json()

        graph = data.get("graph", {})
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        # Verify graph structure
        if not nodes or not edges:
            print("❌ FAILED: Graph is empty")
            return False

        # Verify node structure
        required_node_fields = ["id", "name", "type", "port"]
        for node in nodes[:3]:  # Check first 3 nodes
            for field in required_node_fields:
                if field not in node:
                    print(f"❌ FAILED: Node missing '{field}' field")
                    return False

        # Verify edge structure
        required_edge_fields = ["from", "to", "type"]
        for edge in edges[:3]:  # Check first 3 edges
            for field in required_edge_fields:
                if field not in edge:
                    print(f"❌ FAILED: Edge missing '{field}' field")
                    return False

        print(f"✅ SUCCESS: Dependency graph generated correctly")
        print(f"   Nodes: {len(nodes)}")
        print(f"   Edges: {len(edges)}")
        print(f"   Sample node: {nodes[0]}")
        print(f"   Sample edge: {edges[0]}")

        return True

    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

def test_step_3_verify_frontend_to_gateway():
    """Step 3: Verify frontend → api-gateway edge"""
    print_step(3, "Verify frontend → api-gateway edge")

    try:
        response = requests.get(DEPENDENCIES_URL, timeout=10)
        data = response.json()

        edges = data["graph"]["edges"]

        # Find edge from frontend to api-gateway
        frontend_to_gateway = None
        for edge in edges:
            if edge["from"] == "frontend" and edge["to"] == "api-gateway":
                frontend_to_gateway = edge
                break

        if not frontend_to_gateway:
            print("❌ FAILED: No edge found from frontend to api-gateway")
            return False

        print(f"✅ SUCCESS: Found edge: frontend → api-gateway")
        print(f"   Edge details: {frontend_to_gateway}")

        return True

    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

def test_step_4_verify_gateway_to_auth():
    """Step 4: Verify api-gateway → auth-service edge"""
    print_step(4, "Verify api-gateway → auth-service edge")

    try:
        response = requests.get(DEPENDENCIES_URL, timeout=10)
        data = response.json()

        edges = data["graph"]["edges"]

        # Find edge from api-gateway to auth-service
        gateway_to_auth = None
        for edge in edges:
            if edge["from"] == "api-gateway" and edge["to"] == "auth-service":
                gateway_to_auth = edge
                break

        if not gateway_to_auth:
            print("❌ FAILED: No edge found from api-gateway to auth-service")
            return False

        print(f"✅ SUCCESS: Found edge: api-gateway → auth-service")
        print(f"   Edge details: {gateway_to_auth}")

        return True

    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

def test_step_5_verify_gateway_to_diagram():
    """Step 5: Verify api-gateway → diagram-service edge"""
    print_step(5, "Verify api-gateway → diagram-service edge")

    try:
        response = requests.get(DEPENDENCIES_URL, timeout=10)
        data = response.json()

        edges = data["graph"]["edges"]

        # Find edge from api-gateway to diagram-service
        gateway_to_diagram = None
        for edge in edges:
            if edge["from"] == "api-gateway" and edge["to"] == "diagram-service":
                gateway_to_diagram = edge
                break

        if not gateway_to_diagram:
            print("❌ FAILED: No edge found from api-gateway to diagram-service")
            return False

        print(f"✅ SUCCESS: Found edge: api-gateway → diagram-service")
        print(f"   Edge details: {gateway_to_diagram}")

        return True

    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

def test_step_6_identify_circular_dependencies():
    """Step 6: Identify circular dependencies"""
    print_step(6, "Identify circular dependencies")

    try:
        response = requests.get(DEPENDENCIES_URL, timeout=10)
        data = response.json()

        circular = data.get("circular_dependencies", {})

        if "found" not in circular or "count" not in circular or "cycles" not in circular:
            print("❌ FAILED: Missing circular dependency fields")
            return False

        print(f"✅ SUCCESS: Circular dependency detection works")
        print(f"   Circular dependencies found: {circular['found']}")
        print(f"   Count: {circular['count']}")

        if circular['found']:
            print(f"   ⚠️  WARNING: Circular dependencies detected!")
            for i, cycle in enumerate(circular['cycles'], 1):
                print(f"      Cycle {i}: {' → '.join(cycle)}")
        else:
            print(f"   ✓ No circular dependencies (good!)")

        return True

    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

def test_step_7_visualize_critical_path():
    """Step 7: Visualize critical path"""
    print_step(7, "Visualize critical path")

    try:
        response = requests.get(DEPENDENCIES_URL, timeout=10)
        data = response.json()

        critical_path = data.get("critical_path", {})

        if "path" not in critical_path or "length" not in critical_path:
            print("❌ FAILED: Missing critical path fields")
            return False

        path = critical_path["path"]
        length = critical_path["length"]
        description = critical_path.get("description", "")

        if not path or length == 0:
            print("❌ FAILED: Critical path is empty")
            return False

        print(f"✅ SUCCESS: Critical path identified")
        print(f"   Length: {length} services")
        print(f"   Path: {description}")
        print(f"   Services in critical path:")
        for i, service in enumerate(path, 1):
            print(f"      {i}. {service}")

        return True

    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

def test_step_8_dependency_health_checks():
    """Step 8: Test dependency health checks"""
    print_step(8, "Test dependency health checks")

    try:
        # Request with health checks enabled
        response = requests.get(f"{DEPENDENCIES_URL}?include_health=true", timeout=30)
        data = response.json()

        if "health" not in data:
            print("❌ FAILED: Health data missing from response")
            return False

        health = data["health"]

        if "summary" not in health or "services" not in health:
            print("❌ FAILED: Missing health fields")
            return False

        summary = health["summary"]
        services = health["services"]

        print(f"✅ SUCCESS: Health checks performed")
        print(f"   Total services checked: {summary['total']}")
        print(f"   Healthy: {summary['healthy']}")
        print(f"   Unhealthy: {summary['unhealthy']}")
        print(f"   Unknown: {summary['unknown']}")
        print(f"   Health percentage: {summary['health_percentage']}%")

        # Show status of each service
        print(f"\n   Service health details:")
        for svc in services[:10]:  # Show first 10
            service_id = svc.get("service_id", "unknown")
            status = svc.get("status", "unknown")
            name = svc.get("name", "unknown")
            symbol = "✓" if status == "healthy" else ("✗" if status == "unhealthy" else "?")
            print(f"      {symbol} {name} ({service_id}): {status}")

        return True

    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False


def main():
    """Run all validation steps."""
    print("\n" + "="*80)
    print("Feature #46 Validation: Service Dependency Mapping")
    print("="*80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Testing endpoint: {DEPENDENCIES_URL}")

    # Run all tests
    results = []

    results.append(("Step 1: Analyze service calls", test_step_1_analyze_service_calls()))
    results.append(("Step 2: Generate dependency graph", test_step_2_generate_dependency_graph()))
    results.append(("Step 3: Verify frontend → api-gateway", test_step_3_verify_frontend_to_gateway()))
    results.append(("Step 4: Verify api-gateway → auth-service", test_step_4_verify_gateway_to_auth()))
    results.append(("Step 5: Verify api-gateway → diagram-service", test_step_5_verify_gateway_to_diagram()))
    results.append(("Step 6: Identify circular dependencies", test_step_6_identify_circular_dependencies()))
    results.append(("Step 7: Visualize critical path", test_step_7_visualize_critical_path()))
    results.append(("Step 8: Test dependency health checks", test_step_8_dependency_health_checks()))

    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} steps passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 Feature #46: ALL TESTS PASSED!")
        print("Service dependency mapping is fully functional.")
        return 0
    else:
        print(f"\n❌ Feature #46: {total - passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
