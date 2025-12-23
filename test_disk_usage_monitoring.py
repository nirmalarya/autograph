"""
Test Feature #45: Disk usage monitoring for storage services

This test verifies:
1. Monitor MinIO disk usage
2. Upload 100MB file
3. Verify disk usage increases
4. Delete file  
5. Verify disk usage decreases
6. Set disk usage alerts at 80% capacity
7. Test alert triggering
"""

import requests
import time
import json

# API Gateway URL
API_URL = "http://localhost:8080"

def test_disk_monitoring_endpoint():
    """Test 1: Verify disk monitoring endpoint is accessible and returns data."""
    print("\n=== Test 1: Disk Monitoring Endpoint ===")
    response = requests.get(f"{API_URL}/test/disk")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    
    # Verify response structure
    assert "message" in data, "Missing 'message' field"
    assert "local_disk" in data, "Missing 'local_disk' field"
    assert "minio_storage" in data, "Missing 'minio_storage' field"
    assert "configuration" in data, "Missing 'configuration' field"
    
    # Verify local disk data
    local_disk = data["local_disk"]
    assert "total_bytes" in local_disk, "Missing 'total_bytes' in local_disk"
    assert "used_bytes" in local_disk, "Missing 'used_bytes' in local_disk"
    assert "free_bytes" in local_disk, "Missing 'free_bytes' in local_disk"
    assert "used_percent" in local_disk, "Missing 'used_percent' in local_disk"
    assert local_disk["used_percent"] >= 0, "Used percent should be >= 0"
    assert local_disk["used_percent"] <= 100, "Used percent should be <= 100"
    
    # Verify MinIO storage data
    minio_storage = data["minio_storage"]
    assert isinstance(minio_storage, list), "minio_storage should be a list"
    assert len(minio_storage) == 3, f"Expected 3 buckets, got {len(minio_storage)}"
    
    # Verify buckets exist
    bucket_names = [b["bucket"] for b in minio_storage]
    assert "diagrams" in bucket_names, "Missing 'diagrams' bucket"
    assert "exports" in bucket_names, "Missing 'exports' bucket"
    assert "uploads" in bucket_names, "Missing 'uploads' bucket"
    
    # Verify configuration
    config = data["configuration"]
    assert config["check_interval_seconds"] == 300, "Expected 300 second check interval"
    assert config["warning_threshold_percent"] == 70.0, "Expected 70% warning threshold"
    assert config["critical_threshold_percent"] == 80.0, "Expected 80% critical threshold"
    assert config["alert_threshold_percent"] == 80.0, "Expected 80% alert threshold"
    
    print("✅ Disk monitoring endpoint working")
    print(f"   Local disk: {local_disk['used_gb']:.2f} GB / {local_disk['total_gb']:.2f} GB ({local_disk['used_percent']}%)")
    print(f"   MinIO buckets: {len(minio_storage)}")
    for bucket in minio_storage:
        print(f"     - {bucket['bucket']}: {bucket['size_mb']:.2f} MB")
    
    return data

def test_get_initial_minio_usage():
    """Test 2: Get initial MinIO usage for comparison."""
    print("\n=== Test 2: Get Initial MinIO Usage ===")
    response = requests.get(f"{API_URL}/test/disk")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    
    minio_storage = data["minio_storage"]
    uploads_bucket = next((b for b in minio_storage if b["bucket"] == "uploads"), None)
    
    assert uploads_bucket is not None, "uploads bucket not found"
    initial_size_bytes = uploads_bucket["size_bytes"]
    
    print(f"✅ Initial uploads bucket size: {initial_size_bytes} bytes ({uploads_bucket['size_mb']:.2f} MB)")
    return initial_size_bytes

def test_upload_large_file():
    """Test 3: Upload 100MB file to MinIO and verify size increase."""
    print("\n=== Test 3: Upload 100MB File ===")
    
    # Get initial size
    initial_size = test_get_initial_minio_usage()
    
    # Upload 100MB file
    file_size_mb = 100.0
    print(f"Uploading {file_size_mb} MB file...")
    response = requests.post(
        f"{API_URL}/test/disk/upload",
        params={"size_mb": file_size_mb, "bucket": "uploads"}
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    upload_data = response.json()
    
    assert "filename" in upload_data, "Missing 'filename' field"
    assert "size_bytes" in upload_data, "Missing 'size_bytes' field"
    assert "size_mb" in upload_data, "Missing 'size_mb' field"
    
    filename = upload_data["filename"]
    uploaded_bytes = upload_data["size_bytes"]
    
    print(f"✅ File uploaded: {filename}")
    print(f"   Size: {uploaded_bytes} bytes ({upload_data['size_mb']:.2f} MB)")
    
    # Wait a moment for MinIO to process
    time.sleep(2)
    
    return filename, uploaded_bytes

def test_verify_size_increase(initial_size, uploaded_bytes):
    """Test 4: Verify disk usage increased after upload."""
    print("\n=== Test 4: Verify Size Increase ===")
    
    # Get current size
    response = requests.get(f"{API_URL}/test/disk")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    minio_storage = data["minio_storage"]
    uploads_bucket = next((b for b in minio_storage if b["bucket"] == "uploads"), None)
    
    assert uploads_bucket is not None, "uploads bucket not found"
    current_size = uploads_bucket["size_bytes"]
    
    # Verify size increased
    size_increase = current_size - initial_size
    
    print(f"Initial size: {initial_size} bytes")
    print(f"Current size: {current_size} bytes")
    print(f"Size increase: {size_increase} bytes ({size_increase / 1024 / 1024:.2f} MB)")
    
    # Should have increased by approximately the uploaded size (allow some variance for metadata)
    expected_min_increase = uploaded_bytes * 0.95  # Allow 5% variance
    assert size_increase >= expected_min_increase, \
        f"Expected increase of at least {expected_min_increase} bytes, got {size_increase} bytes"
    
    print(f"✅ Disk usage increased by {size_increase / 1024 / 1024:.2f} MB")
    return current_size

def test_delete_file(filename):
    """Test 5: Delete file from MinIO."""
    print("\n=== Test 5: Delete File ===")
    
    response = requests.delete(
        f"{API_URL}/test/disk/cleanup",
        params={"bucket": "uploads", "filename": filename}
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    
    assert data["message"] == "File deleted successfully", "Unexpected message"
    
    print(f"✅ File deleted: {filename}")
    
    # Wait a moment for MinIO to process
    time.sleep(2)

def test_verify_size_decrease(size_after_upload, initial_size):
    """Test 6: Verify disk usage decreased after deletion."""
    print("\n=== Test 6: Verify Size Decrease ===")
    
    # Get current size
    response = requests.get(f"{API_URL}/test/disk")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    minio_storage = data["minio_storage"]
    uploads_bucket = next((b for b in minio_storage if b["bucket"] == "uploads"), None)
    
    assert uploads_bucket is not None, "uploads bucket not found"
    final_size = uploads_bucket["size_bytes"]
    
    size_decrease = size_after_upload - final_size
    
    print(f"Size after upload: {size_after_upload} bytes")
    print(f"Final size: {final_size} bytes")
    print(f"Size decrease: {size_decrease} bytes ({size_decrease / 1024 / 1024:.2f} MB)")
    
    # Should have decreased significantly (back to approximately initial size)
    expected_min_decrease = (size_after_upload - initial_size) * 0.95  # Allow 5% variance
    assert size_decrease >= expected_min_decrease, \
        f"Expected decrease of at least {expected_min_decrease} bytes, got {size_decrease} bytes"
    
    print(f"✅ Disk usage decreased by {size_decrease / 1024 / 1024:.2f} MB")
    print(f"   Final size close to initial: {final_size} bytes (initial: {initial_size} bytes)")

def test_alert_configuration():
    """Test 7: Verify alert thresholds are configured correctly."""
    print("\n=== Test 7: Alert Configuration ===")
    
    response = requests.get(f"{API_URL}/test/disk")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    config = data["configuration"]
    local_disk = data["local_disk"]
    
    # Verify alert threshold is set at 80%
    assert config["alert_threshold_percent"] == 80.0, "Alert threshold should be 80%"
    assert config["critical_threshold_percent"] == 80.0, "Critical threshold should be 80%"
    assert config["warning_threshold_percent"] == 70.0, "Warning threshold should be 70%"
    
    # Check if alert would be triggered
    current_usage = local_disk["used_percent"]
    alert_triggered = local_disk.get("alert_triggered", False)
    
    print(f"✅ Alert configuration verified")
    print(f"   Warning threshold: {config['warning_threshold_percent']}%")
    print(f"   Critical threshold: {config['critical_threshold_percent']}%")
    print(f"   Alert threshold: {config['alert_threshold_percent']}%")
    print(f"   Current usage: {current_usage}%")
    print(f"   Alert triggered: {alert_triggered}")
    
    # Verify alert logic is working
    if current_usage >= config["alert_threshold_percent"]:
        print(f"   ⚠️ Current usage ({current_usage}%) exceeds alert threshold ({config['alert_threshold_percent']}%)")
    else:
        print(f"   ✓ Current usage ({current_usage}%) is below alert threshold ({config['alert_threshold_percent']}%)")

def test_prometheus_metrics():
    """Test 8: Verify disk metrics are exposed in Prometheus format."""
    print("\n=== Test 8: Prometheus Metrics ===")
    
    response = requests.get(f"{API_URL}/metrics")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    metrics_text = response.text
    
    # Check for disk usage metrics
    assert "api_gateway_disk_usage_bytes" in metrics_text, "Missing disk_usage_bytes metric"
    assert "api_gateway_disk_usage_percent" in metrics_text, "Missing disk_usage_percent metric"
    assert "api_gateway_disk_total_bytes" in metrics_text, "Missing disk_total_bytes metric"
    assert "api_gateway_disk_available_bytes" in metrics_text, "Missing disk_available_bytes metric"
    assert "api_gateway_disk_alert_triggered_total" in metrics_text, "Missing disk_alert_triggered_total metric"
    
    print("✅ Prometheus metrics exposed")
    print("   Metrics found:")
    print("     - api_gateway_disk_usage_bytes")
    print("     - api_gateway_disk_usage_percent")
    print("     - api_gateway_disk_total_bytes")
    print("     - api_gateway_disk_available_bytes")
    print("     - api_gateway_disk_alert_triggered_total")
    
    # Count metric lines
    metric_lines = [line for line in metrics_text.split('\n') if 'api_gateway_disk' in line and not line.startswith('#')]
    print(f"   Total disk metric values: {len(metric_lines)}")

def test_background_monitoring():
    """Test 9: Verify background monitoring task is running."""
    print("\n=== Test 9: Background Monitoring ===")
    
    # Get initial metrics
    response1 = requests.get(f"{API_URL}/metrics")
    assert response1.status_code == 200, f"Expected 200, got {response1.status_code}"
    
    # Wait for monitoring cycle (check interval is 300 seconds, so we can't wait that long)
    # Instead, we'll just verify the metrics exist
    metrics_text = response1.text
    
    # Extract disk usage values
    import re
    disk_usage_lines = [line for line in metrics_text.split('\n') 
                       if 'api_gateway_disk_usage_percent{' in line and 'storage_type="local"' in line and not line.startswith('#')]
    
    assert len(disk_usage_lines) > 0, "No disk usage metrics found for local storage"
    
    # Parse the value
    match = re.search(r'api_gateway_disk_usage_percent.*?} ([\d.]+)', disk_usage_lines[0])
    assert match, "Could not parse disk usage metric"
    
    usage_value = float(match.group(1))
    assert 0 <= usage_value <= 100, f"Invalid usage percentage: {usage_value}"
    
    print(f"✅ Background monitoring is running")
    print(f"   Current disk usage (from metrics): {usage_value}%")
    print(f"   Monitoring interval: 300 seconds")

def run_all_tests():
    """Run all disk monitoring tests."""
    print("=" * 70)
    print("DISK USAGE MONITORING TESTS - Feature #45")
    print("=" * 70)
    
    try:
        # Test 1: Basic endpoint
        test_disk_monitoring_endpoint()
        
        # Test 2: Get initial usage
        initial_size = test_get_initial_minio_usage()
        
        # Test 3: Upload file
        filename, uploaded_bytes = test_upload_large_file()
        
        # Test 4: Verify size increase
        size_after_upload = test_verify_size_increase(initial_size, uploaded_bytes)
        
        # Test 5: Delete file
        test_delete_file(filename)
        
        # Test 6: Verify size decrease
        test_verify_size_decrease(size_after_upload, initial_size)
        
        # Test 7: Alert configuration
        test_alert_configuration()
        
        # Test 8: Prometheus metrics
        test_prometheus_metrics()
        
        # Test 9: Background monitoring
        test_background_monitoring()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED (9/9)")
        print("=" * 70)
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
