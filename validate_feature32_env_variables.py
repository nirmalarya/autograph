#!/usr/bin/env python3
"""
Feature 32: Environment variables loaded from .env file
Validates that services correctly load and use environment variables from .env file
"""

import subprocess
import time
import os
import sys
import requests
import psycopg2

def run_command(cmd, description):
    """Run a shell command and return output"""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"❌ Failed: {result.stderr}")
            return False, result.stderr
        print(f"✅ Success")
        return True, result.stdout
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout")
        return False, "Command timed out"
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, str(e)

def check_env_file_exists():
    """Verify .env file exists"""
    print("\n" + "="*80)
    print("TEST 1: .env File Exists")
    print("="*80)

    if os.path.exists(".env"):
        print("✅ .env file exists")
        return True
    else:
        print("❌ .env file not found")
        return False

def check_env_not_in_git():
    """Verify .env is in .gitignore"""
    print("\n" + "="*80)
    print("TEST 2: .env Not Committed to Git")
    print("="*80)

    try:
        # Check if .env is in .gitignore
        with open(".gitignore", "r") as f:
            content = f.read()
            if ".env" in content:
                print("✅ .env is in .gitignore")

                # Verify .env is not tracked by git
                result = subprocess.run(
                    "git ls-files .env",
                    shell=True,
                    capture_output=True,
                    text=True
                )

                if result.stdout.strip() == "":
                    print("✅ .env is not tracked by git")
                    return True
                else:
                    print("❌ .env is tracked by git (should be ignored)")
                    return False
            else:
                print("❌ .env not found in .gitignore")
                return False
    except Exception as e:
        print(f"❌ Error checking git ignore: {e}")
        return False

def test_database_env_vars():
    """Test database connection using environment variables"""
    print("\n" + "="*80)
    print("TEST 3: Database Environment Variables")
    print("="*80)

    required_vars = [
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD"
    ]

    # Read .env file
    env_vars = {}
    try:
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key] = value
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False

    # Check required variables exist
    print("\n📋 Checking required environment variables...")
    all_present = True
    for var in required_vars:
        if var in env_vars:
            # Don't print passwords
            if "PASSWORD" in var:
                print(f"✅ {var}=***")
            else:
                print(f"✅ {var}={env_vars[var]}")
        else:
            print(f"❌ {var} not found in .env")
            all_present = False

    if not all_present:
        return False

    # Test connection using these variables
    print("\n🔌 Testing database connection with .env variables...")
    try:
        # Use localhost since we're testing from host machine
        conn = psycopg2.connect(
            host="localhost",
            port=env_vars.get("POSTGRES_PORT", "5432"),
            database=env_vars.get("POSTGRES_DB"),
            user=env_vars.get("POSTGRES_USER"),
            password=env_vars.get("POSTGRES_PASSWORD")
        )
        conn.close()
        print("✅ Database connection successful using .env variables")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_service_env_vars():
    """Test that services are using environment variables"""
    print("\n" + "="*80)
    print("TEST 4: Service Environment Variables")
    print("="*80)

    services = [
        ("auth-service", 8085),
        ("api-gateway", 8080),
        ("diagram-service", 8082)
    ]

    # Read .env file for JWT secret
    env_vars = {}
    try:
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key] = value
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False

    # Check JWT secret is defined
    if "JWT_SECRET" in env_vars:
        print(f"✅ JWT_SECRET defined in .env")
    else:
        print("⚠️  JWT_SECRET not found in .env (may be optional)")

    # Test that services are running with environment variables
    print("\n🏥 Checking services are healthy (they must load env vars to start)...")
    all_healthy = True

    for service_name, port in services:
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name} healthy on port {port}")
            else:
                print(f"❌ {service_name} returned status {response.status_code}")
                all_healthy = False
        except Exception as e:
            print(f"❌ {service_name} health check failed: {e}")
            all_healthy = False

    return all_healthy

def test_docker_compose_env_interpolation():
    """Test that docker-compose correctly interpolates .env variables"""
    print("\n" + "="*80)
    print("TEST 5: Docker Compose Environment Interpolation")
    print("="*80)

    # Check that docker-compose can see environment variables
    print("\n🐳 Checking docker-compose environment variable usage...")

    try:
        # Get postgres container environment
        result = subprocess.run(
            "docker exec autograph-postgres env | grep POSTGRES",
            shell=True,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            env_lines = result.stdout.strip().split("\n")
            print("\n📋 PostgreSQL container environment variables:")
            for line in env_lines:
                if "PASSWORD" in line:
                    key = line.split("=")[0]
                    print(f"  {key}=***")
                else:
                    print(f"  {line}")

            # Check required variables are present
            required = ["POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"]
            for req in required:
                if any(req in line for line in env_lines):
                    print(f"✅ {req} loaded in container")
                else:
                    print(f"❌ {req} not found in container")
                    return False

            return True
        else:
            print(f"❌ Failed to get container environment")
            return False

    except Exception as e:
        print(f"❌ Error checking docker environment: {e}")
        return False

def test_sensitive_values():
    """Test that sensitive values are properly managed"""
    print("\n" + "="*80)
    print("TEST 6: Sensitive Value Management")
    print("="*80)

    sensitive_keys = ["PASSWORD", "SECRET", "KEY", "TOKEN"]

    # Read .env file
    env_vars = {}
    try:
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key] = value
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False

    # Find sensitive variables
    print("\n🔐 Checking sensitive variables are defined...")
    sensitive_found = []
    for key in env_vars:
        if any(sensitive in key.upper() for sensitive in sensitive_keys):
            sensitive_found.append(key)

    if sensitive_found:
        print(f"✅ Found {len(sensitive_found)} sensitive variables:")
        for key in sensitive_found:
            print(f"  • {key}=***")

        # Verify critical ones are not empty (API keys can be empty for dev)
        critical_vars = ["POSTGRES_PASSWORD", "JWT_SECRET"]
        all_set = True
        empty_vars = []

        for key in sensitive_found:
            if not env_vars[key] or env_vars[key].strip() == "":
                empty_vars.append(key)
                if key in critical_vars:
                    print(f"❌ CRITICAL: {key} is empty")
                    all_set = False
                else:
                    print(f"⚠️  {key} is empty (OK for development)")

        if all_set:
            if empty_vars:
                print(f"✅ Critical variables set ({len(empty_vars)} optional vars empty)")
            else:
                print("✅ All sensitive variables have values")
            return True
        else:
            print("❌ Some critical sensitive variables are empty")
            return False
    else:
        print("⚠️  No sensitive variables found in .env")
        return True  # Not necessarily a failure

def test_env_example_exists():
    """Test that .env.docker.example exists as template"""
    print("\n" + "="*80)
    print("TEST 7: Environment Template File")
    print("="*80)

    if os.path.exists(".env.docker.example"):
        print("✅ .env.docker.example exists")

        # Compare keys between .env and .env.example
        try:
            with open(".env", "r") as f:
                env_keys = set()
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key = line.split("=", 1)[0]
                        env_keys.add(key)

            with open(".env.docker.example", "r") as f:
                example_keys = set()
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key = line.split("=", 1)[0]
                        example_keys.add(key)

            # Check if .env has keys not in example
            extra_keys = env_keys - example_keys
            if extra_keys:
                print(f"⚠️  .env has {len(extra_keys)} keys not in example file")
                for key in list(extra_keys)[:5]:
                    print(f"  • {key}")

            # Check if example has keys not in .env
            missing_keys = example_keys - env_keys
            if missing_keys:
                print(f"⚠️  .env.docker.example has {len(missing_keys)} keys not in .env")
                for key in list(missing_keys)[:5]:
                    print(f"  • {key}")

            print(f"✅ Template comparison complete ({len(env_keys)} in .env, {len(example_keys)} in example)")
            return True

        except Exception as e:
            print(f"❌ Error comparing files: {e}")
            return False
    else:
        print("❌ .env.docker.example not found")
        return False

def main():
    """Run all environment variable tests"""
    print("\n" + "="*80)
    print("FEATURE 32: Environment Variables Loaded from .env File")
    print("="*80)

    # Run all tests
    results = {
        ".env file exists": check_env_file_exists(),
        ".env not in git": check_env_not_in_git(),
        "Database env vars": test_database_env_vars(),
        "Service env vars": test_service_env_vars(),
        "Docker Compose interpolation": test_docker_compose_env_interpolation(),
        "Sensitive value management": test_sensitive_values(),
        "Environment template": test_env_example_exists()
    }

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "="*80)
    if all_passed:
        print("✅ FEATURE 32: PASSED - Environment variables working correctly")
        print("="*80)
        return 0
    else:
        print("❌ FEATURE 32: FAILED - Some tests failed")
        print("="*80)
        return 1

if __name__ == "__main__":
    sys.exit(main())
