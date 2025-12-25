#!/bin/bash
# Pre-commit hook for Trivy container scanning
# This is a template - can be integrated with git hooks

echo "🔍 Running Trivy security scan on modified services..."

# Detect which services have changed
CHANGED_SERVICES=$(git diff --cached --name-only | grep "^services/" | cut -d'/' -f2 | sort -u)

if [ -z "$CHANGED_SERVICES" ]; then
    echo "✓ No service changes detected, skipping Trivy scan"
    exit 0
fi

echo "Changed services: $CHANGED_SERVICES"
echo ""

# Quick scan flag
QUICK_SCAN=${QUICK_SCAN:-true}

for SERVICE in $CHANGED_SERVICES; do
    IMAGE_NAME="autograph-${SERVICE}:latest"

    # Check if image exists
    if ! docker images | grep -q "autograph-${SERVICE}"; then
        echo "⚠️  Image not found: $IMAGE_NAME (build may be required)"
        continue
    fi

    echo "Scanning $IMAGE_NAME..."

    if [ "$QUICK_SCAN" = "true" ]; then
        # Quick scan - only CRITICAL vulnerabilities
        docker run --rm \
            -v /var/run/docker.sock:/var/run/docker.sock \
            -e TRIVY_INSECURE=true \
            aquasec/trivy:latest image \
            --severity CRITICAL \
            --exit-code 1 \
            "$IMAGE_NAME"

        if [ $? -ne 0 ]; then
            echo "❌ CRITICAL vulnerabilities found in $SERVICE!"
            echo "Fix critical issues before committing or use --no-verify to skip"
            exit 1
        fi
    else
        # Full scan
        docker run --rm \
            -v /var/run/docker.sock:/var/run/docker.sock \
            -e TRIVY_INSECURE=true \
            aquasec/trivy:latest image \
            --severity CRITICAL,HIGH \
            "$IMAGE_NAME"
    fi

    echo ""
done

echo "✅ Trivy scan completed successfully"
exit 0
