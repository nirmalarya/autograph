#!/bin/bash
###############################################################################
# Penetration Testing Script
# Runs comprehensive security testing against Autograph application
###############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         AUTOGRAPH PENETRATION TESTING SUITE               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if services are running
check_services() {
    echo -e "${YELLOW}[1/5] Checking service availability...${NC}"

    if ! docker-compose ps | grep -q "Up"; then
        echo -e "${RED}❌ Services not running. Please start with 'docker-compose up -d'${NC}"
        exit 1
    fi

    # Wait for API Gateway
    echo "Waiting for API Gateway to be ready..."
    for i in {1..30}; do
        if curl -sf http://localhost:8080/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ API Gateway is ready${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${RED}❌ API Gateway did not become ready in time${NC}"
            exit 1
        fi
        sleep 2
    done
}

# Run custom penetration tests
run_custom_tests() {
    echo ""
    echo -e "${YELLOW}[2/5] Running custom penetration tests...${NC}"

    cd "$PROJECT_ROOT"

    if [ ! -f "validate_feature62_penetration_testing.py" ]; then
        echo -e "${RED}❌ Penetration test script not found${NC}"
        exit 1
    fi

    python3 validate_feature62_penetration_testing.py
    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✅ Custom penetration tests passed${NC}"
    else
        echo -e "${RED}❌ Custom penetration tests failed${NC}"
        return 1
    fi
}

# Run OWASP ZAP scan (if available)
run_zap_scan() {
    echo ""
    echo -e "${YELLOW}[3/5] Running OWASP ZAP scan...${NC}"

    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}⚠️  Docker not available, skipping ZAP scan${NC}"
        return 0
    fi

    echo "Pulling OWASP ZAP Docker image..."
    docker pull zaproxy/zap-stable:latest

    echo "Running ZAP baseline scan..."
    docker run --rm --network="host" \
        -v "$PROJECT_ROOT:/zap/wrk/:rw" \
        zaproxy/zap-stable:latest \
        zap-baseline.py \
        -t http://localhost:8080 \
        -r zap_report.html \
        -J zap_report.json \
        -w zap_report.md \
        -c .zap/rules.tsv \
        -I || true  # Don't fail on ZAP warnings

    if [ -f "zap_report.html" ]; then
        echo -e "${GREEN}✅ ZAP scan completed${NC}"
        echo "Report saved to: zap_report.html"
    else
        echo -e "${YELLOW}⚠️  ZAP scan completed with warnings${NC}"
    fi
}

# Analyze results
analyze_results() {
    echo ""
    echo -e "${YELLOW}[4/5] Analyzing results...${NC}"

    if [ ! -f "penetration_test_report.json" ]; then
        echo -e "${RED}❌ No report file found${NC}"
        return 1
    fi

    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}                    SECURITY SUMMARY                        ${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"

    # Parse JSON report
    SCORE=$(python3 -c "import json; print(json.load(open('penetration_test_report.json'))['security_score'])")
    PASSED=$(python3 -c "import json; print(json.load(open('penetration_test_report.json'))['tests_passed'])")
    FAILED=$(python3 -c "import json; print(json.load(open('penetration_test_report.json'))['tests_failed'])")
    CRITICAL=$(python3 -c "import json; vulns=json.load(open('penetration_test_report.json'))['vulnerabilities']; print(len([v for v in vulns if v['severity']=='CRITICAL']))")
    HIGH=$(python3 -c "import json; vulns=json.load(open('penetration_test_report.json'))['vulnerabilities']; print(len([v for v in vulns if v['severity']=='HIGH']))")
    MEDIUM=$(python3 -c "import json; vulns=json.load(open('penetration_test_report.json'))['vulnerabilities']; print(len([v for v in vulns if v['severity']=='MEDIUM']))")

    echo ""
    echo "Security Score: $SCORE/100"
    echo ""
    echo "Test Results:"
    echo "  ✅ Passed: $PASSED"
    echo "  ❌ Failed: $FAILED"
    echo ""
    echo "Vulnerabilities:"
    echo "  🔴 Critical: $CRITICAL"
    echo "  🟠 High:     $HIGH"
    echo "  🟡 Medium:   $MEDIUM"
    echo ""

    if [ "$CRITICAL" -gt 0 ]; then
        echo -e "${RED}════════════════════════════════════════════════════════════${NC}"
        echo -e "${RED}⚠️  CRITICAL VULNERABILITIES DETECTED!${NC}"
        echo -e "${RED}════════════════════════════════════════════════════════════${NC}"

        python3 -c "
import json
report = json.load(open('penetration_test_report.json'))
critical = [v for v in report['vulnerabilities'] if v['severity'] == 'CRITICAL']
for v in critical:
    print(f\"\\n  ❌ {v['test']}\")
    print(f\"     {v['details']}\")
"
        echo ""
        return 1
    elif [ "$HIGH" -gt 0 ]; then
        echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
        echo -e "${YELLOW}⚠️  HIGH SEVERITY VULNERABILITIES DETECTED${NC}"
        echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"

        python3 -c "
import json
report = json.load(open('penetration_test_report.json'))
high = [v for v in report['vulnerabilities'] if v['severity'] == 'HIGH']
for v in high:
    print(f\"\\n  ⚠️  {v['test']}\")
    print(f\"     {v['details']}\")
"
        echo ""
    else
        echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}✅ NO CRITICAL OR HIGH VULNERABILITIES DETECTED${NC}"
        echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
        echo ""
    fi
}

# Generate final report
generate_report() {
    echo ""
    echo -e "${YELLOW}[5/5] Generating final report...${NC}"

    REPORT_FILE="penetration_test_results_$(date +%Y%m%d_%H%M%S).md"

    cat > "$REPORT_FILE" << EOF
# Penetration Testing Report
**Generated:** $(date '+%Y-%m-%d %H:%M:%S')
**Target:** http://localhost:8080

## Executive Summary

EOF

    if [ -f "penetration_test_report.json" ]; then
        python3 << 'PYTHON_EOF' >> "$REPORT_FILE"
import json

report = json.load(open('penetration_test_report.json'))

print(f"**Security Score:** {report['security_score']}/100\n")
print(f"**Tests Passed:** {report['tests_passed']}")
print(f"**Tests Failed:** {report['tests_failed']}\n")

vulns = report['vulnerabilities']
critical = [v for v in vulns if v['severity'] == 'CRITICAL']
high = [v for v in vulns if v['severity'] == 'HIGH']
medium = [v for v in vulns if v['severity'] == 'MEDIUM']

print("## Vulnerability Summary\n")
print("| Severity | Count |")
print("|----------|-------|")
print(f"| 🔴 Critical | {len(critical)} |")
print(f"| 🟠 High | {len(high)} |")
print(f"| 🟡 Medium | {len(medium)} |")
print()

if vulns:
    print("## Detailed Findings\n")
    for v in vulns:
        emoji = "🔴" if v['severity'] == 'CRITICAL' else "🟠" if v['severity'] == 'HIGH' else "🟡"
        print(f"### {emoji} {v['test']} ({v['severity']})\n")
        print(f"**Details:** {v['details']}\n")
        print(f"**Timestamp:** {v['timestamp']}\n")
else:
    print("## ✅ No Vulnerabilities Detected\n")
    print("All security tests passed successfully.\n")
PYTHON_EOF
    fi

    cat >> "$REPORT_FILE" << EOF

## Test Categories

1. ✅ SQL Injection Testing
2. ✅ Cross-Site Scripting (XSS)
3. ✅ CSRF Protection
4. ✅ Authentication Bypass
5. ✅ Authorization Flaws
6. ✅ Session Management

## Files Generated

- \`penetration_test_report.json\` - Machine-readable report
- \`$REPORT_FILE\` - Human-readable report
EOF

    if [ -f "zap_report.html" ]; then
        cat >> "$REPORT_FILE" << EOF
- \`zap_report.html\` - OWASP ZAP scan results
- \`zap_report.json\` - OWASP ZAP JSON report
- \`zap_report.md\` - OWASP ZAP markdown report
EOF
    fi

    echo -e "${GREEN}✅ Final report saved to: $REPORT_FILE${NC}"
}

# Main execution
main() {
    check_services

    if run_custom_tests; then
        CUSTOM_PASSED=true
    else
        CUSTOM_PASSED=false
    fi

    # Run ZAP scan (optional, may not be available)
    run_zap_scan || true

    if [ "$CUSTOM_PASSED" = true ]; then
        analyze_results
        ANALYZE_RESULT=$?
    else
        ANALYZE_RESULT=1
    fi

    generate_report

    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"

    if [ $ANALYZE_RESULT -eq 0 ]; then
        echo -e "${GREEN}✅ PENETRATION TESTING COMPLETE - NO CRITICAL ISSUES${NC}"
        echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
        exit 0
    else
        echo -e "${RED}❌ PENETRATION TESTING COMPLETE - VULNERABILITIES FOUND${NC}"
        echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
        echo ""
        echo "Please review the reports and fix identified vulnerabilities."
        exit 1
    fi
}

# Run main function
main "$@"
