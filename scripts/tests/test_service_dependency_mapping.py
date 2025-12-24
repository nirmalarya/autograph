#!/usr/bin/env python3
"""
Test Service Dependency Mapping (Feature #46)

Tests:
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
from typing import Dict, Any

# Configuration
API_GATEWAY_URL = "http://localhost:8080"
DEPENDENCIES_ENDPOINT = f"{API_GATEWAY_URL}/dependencies"


def print_test_header(test_num: int, description: str):
    """Print formatted test header."""
    print(f"\n{'='*80}")
    print(f"TEST #{test_num}: {description}")
    print(f"{'='*80}")


def print_success(message: str):
    """Print success message."""
    print(f"✓ {message}")


def print_failure(message: str):
    """Print failure message."""
    print(f"✗ {message}")


def print_info(message: str):
    """Print info message."""
    print(f"ℹ {message}")


def test_1_analyze_service_calls() -> bool:
    """Test 1: Analyze service-to-service calls."""
    print_test_header(1, "Analyze service-to-service calls")
    
    try:
        response = requests.get(DEPENDENCIES_ENDPOINT)
        
        if response.status_code != 200:
            print_failure(f"HTTP {response.status_code}: {response.text}")
            return False
        
        data = response.json()
        
        # Check that we have a graph structure
        if "graph" not in data:
            print_failure("Response missing 'graph' field")
            return False
        
        graph = data["graph"]
        
        # Check for nodes and edges
        if "nodes" not in graph or "edges" not in graph:
            print_failure("Graph missing 'nodes' or 'edges'")
            return False
        
        print_success(f"Found {len(graph['nodes'])} services in dependency graph")
        print_success(f"Found {len(graph['edges'])} service dependencies")
        
        # List all nodes
        print_info("Services in the system:")
        for node in graph["nodes"]:
            print(f"  - {node['name']} ({node['type']}) on port {node['port']}")
        
        print_success("Service-to-service call analysis complete")
        return True
        
    except Exception as e:
        print_failure(f"Exception: {str(e)}")
        return False


def test_2_generate_dependency_graph() -> bool:
    """Test 2: Generate dependency graph."""
    print_test_header(2, "Generate dependency graph")
    
    try:
        response = requests.get(DEPENDENCIES_ENDPOINT)
        
        if response.status_code != 200:
            print_failure(f"HTTP {response.status_code}: {response.text}")
            return False
        
        data = response.json()
        graph = data["graph"]
        
        # Verify graph structure
        required_fields = ["nodes", "edges", "total_services", "total_dependencies"]
        for field in required_fields:
            if field not in graph:
                print_failure(f"Graph missing required field: {field}")
                return False
        
        print_success(f"Total services: {graph['total_services']}")
        print_success(f"Total dependencies: {graph['total_dependencies']}")
        
        # Verify graph is non-empty
        if graph["total_services"] == 0:
            print_failure("Graph has no services")
            return False
        
        if graph["total_dependencies"] == 0:
            print_info("Warning: Graph has no dependencies (unexpected for microservices)")
        
        # Verify each edge connects valid nodes
        node_ids = {node["id"] for node in graph["nodes"]}
        for edge in graph["edges"]:
            if edge["from"] not in node_ids:
                print_failure(f"Edge references unknown 'from' node: {edge['from']}")
                return False
            if edge["to"] not in node_ids:
                print_failure(f"Edge references unknown 'to' node: {edge['to']}")
                return False
        
        print_success("All edges reference valid nodes")
        print_success("Dependency graph generated successfully")
        return True
        
    except Exception as e:
        print_failure(f"Exception: {str(e)}")
        return False


def test_3_verify_frontend_to_gateway_edge() -> bool:
    """Test 3: Verify frontend → api-gateway edge."""
    print_test_header(3, "Verify frontend → api-gateway edge")
    
    try:
        response = requests.get(DEPENDENCIES_ENDPOINT)
        data = response.json()
        edges = data["graph"]["edges"]
        
        # Look for frontend → api-gateway edge
        found = False
        for edge in edges:
            if edge["from"] == "frontend" and edge["to"] == "api-gateway":
                found = True
                print_success(f"Found edge: {edge['from']} → {edge['to']} (type: {edge['type']})")
                break
        
        if not found:
            print_failure("frontend → api-gateway edge not found")
            return False
        
        print_success("Frontend correctly depends on API Gateway")
        return True
        
    except Exception as e:
        print_failure(f"Exception: {str(e)}")
        return False


def test_4_verify_gateway_to_auth_edge() -> bool:
    """Test 4: Verify api-gateway → auth-service edge."""
    print_test_header(4, "Verify api-gateway → auth-service edge")
    
    try:
        response = requests.get(DEPENDENCIES_ENDPOINT)
        data = response.json()
        edges = data["graph"]["edges"]
        
        # Look for api-gateway → auth-service edge
        found = False
        for edge in edges:
            if edge["from"] == "api-gateway" and edge["to"] == "auth-service":
                found = True
                print_success(f"Found edge: {edge['from']} → {edge['to']} (type: {edge['type']})")
                break
        
        if not found:
            print_failure("api-gateway → auth-service edge not found")
            return False
        
        print_success("API Gateway correctly depends on Auth Service")
        return True
        
    except Exception as e:
        print_failure(f"Exception: {str(e)}")
        return False


def test_5_verify_gateway_to_diagram_edge() -> bool:
    """Test 5: Verify api-gateway → diagram-service edge."""
    print_test_header(5, "Verify api-gateway → diagram-service edge")
    
    try:
        response = requests.get(DEPENDENCIES_ENDPOINT)
        data = response.json()
        edges = data["graph"]["edges"]
        
        # Look for api-gateway → diagram-service edge
        found = False
        for edge in edges:
            if edge["from"] == "api-gateway" and edge["to"] == "diagram-service":
                found = True
                print_success(f"Found edge: {edge['from']} → {edge['to']} (type: {edge['type']})")
                break
        
        if not found:
            print_failure("api-gateway → diagram-service edge not found")
            return False
        
        print_success("API Gateway correctly depends on Diagram Service")
        return True
        
    except Exception as e:
        print_failure(f"Exception: {str(e)}")
        return False


def test_6_identify_circular_dependencies() -> bool:
    """Test 6: Identify circular dependencies."""
    print_test_header(6, "Identify circular dependencies")
    
    try:
        response = requests.get(DEPENDENCIES_ENDPOINT)
        data = response.json()
        
        if "circular_dependencies" not in data:
            print_failure("Response missing 'circular_dependencies' field")
            return False
        
        circular = data["circular_dependencies"]
        
        # Check structure
        required_fields = ["found", "count", "cycles"]
        for field in required_fields:
            if field not in circular:
                print_failure(f"circular_dependencies missing field: {field}")
                return False
        
        if circular["found"]:
            print_info(f"Found {circular['count']} circular dependency cycles:")
            for i, cycle in enumerate(circular["cycles"], 1):
                cycle_str = " → ".join(cycle)
                print(f"  Cycle {i}: {cycle_str}")
            print_info("Note: Circular dependencies should be avoided in production")
        else:
            print_success("No circular dependencies found (expected for well-designed architecture)")
        
        print_success("Circular dependency detection working")
        return True
        
    except Exception as e:
        print_failure(f"Exception: {str(e)}")
        return False


def test_7_visualize_critical_path() -> bool:
    """Test 7: Visualize critical path."""
    print_test_header(7, "Visualize critical path")
    
    try:
        response = requests.get(DEPENDENCIES_ENDPOINT)
        data = response.json()
        
        if "critical_path" not in data:
            print_failure("Response missing 'critical_path' field")
            return False
        
        critical = data["critical_path"]
        
        # Check structure
        required_fields = ["path", "length", "description"]
        for field in required_fields:
            if field not in critical:
                print_failure(f"critical_path missing field: {field}")
                return False
        
        if critical["length"] == 0:
            print_failure("Critical path has length 0")
            return False
        
        print_success(f"Critical path length: {critical['length']} services")
        print_success(f"Critical path: {critical['description']}")
        
        # Verify path starts with frontend
        if critical["path"] and critical["path"][0] != "frontend":
            print_info(f"Note: Critical path starts with '{critical['path'][0]}' (expected 'frontend')")
        
        # Critical path should end with infrastructure service
        if critical["path"]:
            last_service = critical["path"][-1]
            print_info(f"Critical path ends at: {last_service}")
        
        print_success("Critical path visualization complete")
        return True
        
    except Exception as e:
        print_failure(f"Exception: {str(e)}")
        return False


def test_8_dependency_health_checks() -> bool:
    """Test 8: Test dependency health checks."""
    print_test_header(8, "Test dependency health checks")
    
    try:
        # Request with health checks enabled
        response = requests.get(f"{DEPENDENCIES_ENDPOINT}?include_health=true")
        
        if response.status_code != 200:
            print_failure(f"HTTP {response.status_code}: {response.text}")
            return False
        
        data = response.json()
        
        if "health" not in data:
            print_failure("Response missing 'health' field when include_health=true")
            return False
        
        health = data["health"]
        
        # Check structure
        if "summary" not in health or "services" not in health:
            print_failure("Health data missing 'summary' or 'services'")
            return False
        
        summary = health["summary"]
        print_success(f"Health summary:")
        print(f"  - Total services: {summary['total']}")
        print(f"  - Healthy: {summary['healthy']}")
        print(f"  - Unhealthy: {summary['unhealthy']}")
        print(f"  - Unknown: {summary['unknown']}")
        print(f"  - Health percentage: {summary['health_percentage']}%")
        
        # List health status of each service
        print_info("Individual service health:")
        for service in health["services"]:
            status_emoji = "✓" if service["status"] == "healthy" else "✗" if service["status"] == "unhealthy" else "?"
            response_time = f" ({service['response_time_ms']}ms)" if service.get("response_time_ms") else ""
            error = f" - {service.get('error')}" if service.get("error") else ""
            print(f"  {status_emoji} {service['name']}: {service['status']}{response_time}{error}")
        
        # Test without health checks
        response_no_health = requests.get(f"{DEPENDENCIES_ENDPOINT}?include_health=false")
        data_no_health = response_no_health.json()
        
        if "health" in data_no_health:
            print_failure("Health data present when include_health=false")
            return False
        
        print_success("Health data correctly excluded when include_health=false")
        print_success("Dependency health checks working")
        return True
        
    except Exception as e:
        print_failure(f"Exception: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("SERVICE DEPENDENCY MAPPING TEST SUITE (Feature #46)")
    print("="*80)
    
    tests = [
        ("Analyze service-to-service calls", test_1_analyze_service_calls),
        ("Generate dependency graph", test_2_generate_dependency_graph),
        ("Verify frontend → api-gateway edge", test_3_verify_frontend_to_gateway_edge),
        ("Verify api-gateway → auth-service edge", test_4_verify_gateway_to_auth_edge),
        ("Verify api-gateway → diagram-service edge", test_5_verify_gateway_to_diagram_edge),
        ("Identify circular dependencies", test_6_identify_circular_dependencies),
        ("Visualize critical path", test_7_visualize_critical_path),
        ("Test dependency health checks", test_8_dependency_health_checks),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print_failure(f"Test crashed: {str(e)}")
            results.append((name, False))
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! Feature #46 is working correctly.")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed. Please fix the issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
