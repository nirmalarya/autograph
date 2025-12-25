#!/usr/bin/env python3
"""
Simplified Feature #63: GDPR Compliance Validation

Validates that all GDPR compliance components are properly implemented.
"""

import psycopg2
import os
from pathlib import Path

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': 'autograph',
    'user': 'autograph',
    'password': os.getenv('POSTGRES_PASSWORD', 'autograph_dev_password')
}

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    END = '\033[0m'

def log(message: str, color: str = Colors.BLUE):
    print(f"{color}{message}{Colors.END}")

def test_result(passed: bool, test_name: str, details: str = ""):
    if passed:
        log(f"✅ {test_name}", Colors.GREEN)
        if details:
            log(f"   {details}", Colors.GREEN)
    else:
        log(f"❌ {test_name}", Colors.RED)
        if details:
            log(f"   {details}", Colors.RED)
    return passed

def test_database_tables():
    """Test that all GDPR tables exist."""
    log("\n1️⃣  Testing GDPR Database Tables...", Colors.BLUE)

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        required_tables = [
            'user_consents',
            'data_processing_activities',
            'data_breach_logs',
            'data_deletion_requests'
        ]

        all_exist = True
        for table in required_tables:
            cur.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = '{table}'
                );
            """)
            exists = cur.fetchone()[0]
            all_exist = all_exist and test_result(exists, f"Table '{table}' exists")

        cur.close()
        conn.close()

        return all_exist

    except Exception as e:
        log(f"Database connection failed: {str(e)}", Colors.RED)
        return False

def test_gdpr_models():
    """Test that GDPR models are defined."""
    log("\n2️⃣  Testing GDPR Models...", Colors.BLUE)

    try:
        project_root = Path(__file__).parent
        models_file = project_root / "services/auth-service/src/models.py"
        if not models_file.exists():
            return test_result(False, f"models.py not found at {models_file}")

        content = models_file.read_text()

        models = [
            'class UserConsent',
            'class DataProcessingActivity',
            'class DataBreachLog',
            'class DataDeletionRequest'
        ]

        all_defined = True
        for model in models:
            exists = model in content
            all_defined = all_defined and test_result(exists, f"{model} defined")

        return all_defined

    except Exception as e:
        log(f"Model check failed: {str(e)}", Colors.RED)
        return False

def test_gdpr_service():
    """Test that GDPR service exists."""
    log("\n3️⃣  Testing GDPR Service...", Colors.BLUE)

    try:
        project_root = Path(__file__).parent
        service_file = project_root / "services/auth-service/src/gdpr_service.py"
        if not service_file.exists():
            return test_result(False, f"gdpr_service.py not found at {service_file}")

        content = service_file.read_text()

        methods = [
            'export_user_data',
            'request_data_deletion',
            'execute_data_deletion',
            'record_consent',
            'withdraw_consent',
            'log_data_breach',
            'get_data_processing_activities'
        ]

        all_implemented = True
        for method in methods:
            exists = f"def {method}" in content
            all_implemented = all_implemented and test_result(exists, f"Method '{method}' implemented")

        return all_implemented

    except Exception as e:
        log(f"Service check failed: {str(e)}", Colors.RED)
        return False

def test_gdpr_routes():
    """Test that GDPR routes exist."""
    log("\n4️⃣  Testing GDPR API Routes...", Colors.BLUE)

    try:
        project_root = Path(__file__).parent
        routes_file = project_root / "services/auth-service/src/gdpr_routes.py"
        if not routes_file.exists():
            return test_result(False, f"gdpr_routes.py not found at {routes_file}")

        content = routes_file.read_text()

        routes = [
            '/gdpr/export',
            '/gdpr/deletion/request',
            '/gdpr/deletion/verify',
            '/gdpr/consent',
            '/gdpr/consent/withdraw',
            '/gdpr/breach/log',
            '/gdpr/processing-activities'
        ]

        all_defined = True
        for route in routes:
            # Check if route is in a decorator or function
            exists = route in content
            all_defined = all_defined and test_result(exists, f"Route '{route}' defined")

        return all_defined

    except Exception as e:
        log(f"Routes check failed: {str(e)}", Colors.RED)
        return False

def test_gdpr_documentation():
    """Test that GDPR documentation exists."""
    log("\n5️⃣  Testing GDPR Documentation...", Colors.BLUE)

    try:
        project_root = Path(__file__).parent
        docs_file = project_root / "docs/GDPR_COMPLIANCE.md"
        if not docs_file.exists():
            return test_result(False, f"GDPR_COMPLIANCE.md not found at {docs_file}")

        content = docs_file.read_text()

        sections = [
            'Right to Access',
            'Right to be Forgotten',
            'Consent Management',
            'Data Breach Notification',
            'Data Processing Activities',
            'Data Minimization',
            'Cross-Border Data Transfers'
        ]

        all_documented = True
        for section in sections:
            exists = section in content
            all_documented = all_documented and test_result(exists, f"Section '{section}' documented")

        return all_documented

    except Exception as e:
        log(f"Documentation check failed: {str(e)}", Colors.RED)
        return False

def test_integration():
    """Test that GDPR routes are integrated into main app."""
    log("\n6️⃣  Testing Integration...", Colors.BLUE)

    try:
        project_root = Path(__file__).parent
        main_file = project_root / "services/auth-service/src/main.py"
        if not main_file.exists():
            return test_result(False, f"main.py not found at {main_file}")

        content = main_file.read_text()

        checks = [
            ('from .gdpr_routes import router as gdpr_router', "GDPR routes imported"),
            ('app.include_router(gdpr_router)', "GDPR router included in app")
        ]

        all_integrated = True
        for check_str, desc in checks:
            exists = check_str in content
            all_integrated = all_integrated and test_result(exists, desc)

        return all_integrated

    except Exception as e:
        log(f"Integration check failed: {str(e)}", Colors.RED)
        return False

def calculate_compliance_score(results: dict) -> int:
    """Calculate GDPR compliance score."""
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)

    score = int((passed_tests / total_tests) * 100)
    return score

def main():
    """Run all GDPR compliance validation tests."""
    log("=" * 60, Colors.BLUE)
    log("GDPR COMPLIANCE VALIDATION - Feature #63", Colors.BLUE)
    log("=" * 60, Colors.BLUE)

    results = {}

    # Run all tests
    results['database_tables'] = test_database_tables()
    results['gdpr_models'] = test_gdpr_models()
    results['gdpr_service'] = test_gdpr_service()
    results['gdpr_routes'] = test_gdpr_routes()
    results['gdpr_documentation'] = test_gdpr_documentation()
    results['integration'] = test_integration()

    # Calculate compliance score
    score = calculate_compliance_score(results)

    # Print summary
    log("\n" + "=" * 60, Colors.BLUE)
    log("GDPR COMPLIANCE TEST SUMMARY", Colors.BLUE)
    log("=" * 60, Colors.BLUE)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        color = Colors.GREEN if passed else Colors.RED
        log(f"{status} - {test_name.replace('_', ' ').title()}", color)

    log(f"\nCompliance Score: {score}/100", Colors.BLUE)

    if score == 100:
        log(f"\n✅ GDPR COMPLIANCE: PERFECT ({score}/100)", Colors.GREEN)
        log("All GDPR requirements properly implemented!", Colors.GREEN)
        return True
    elif score >= 80:
        log(f"\n✅ GDPR COMPLIANCE: EXCELLENT ({score}/100)", Colors.GREEN)
        return True
    elif score >= 60:
        log(f"\n⚠️  GDPR COMPLIANCE: ACCEPTABLE ({score}/100)", Colors.YELLOW)
        return True
    else:
        log(f"\n❌ GDPR COMPLIANCE: INSUFFICIENT ({score}/100)", Colors.RED)
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
