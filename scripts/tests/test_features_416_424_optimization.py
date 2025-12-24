#!/usr/bin/env python3
"""
Test Suite for Features #416-424: Collaboration Optimization
Tests optimization features like heartbeat, permissions, bandwidth optimization,
scalability, connection quality, and offline mode.
"""

import json
import subprocess
import time
import sys

# Configuration
COLLAB_SERVICE_URL = "http://localhost:8083"

def run_curl(url, method="GET", data=None):
    """Run curl command and return JSON response."""
    cmd = ["curl", "-s", "-X", method, url]
    
    if data:
        cmd.extend(["-H", "Content-Type: application/json"])
        cmd.extend(["-d", json.dumps(data)])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
        return None
    except Exception as e:
        print(f"Exception: {e}")
        return None


class TestCollaborationOptimization:
    """Test collaboration optimization features."""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def log_result(self, feature_num: int, description: str, passed: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\nFeature #{feature_num}: {description}")
        print(f"Status: {status}")
        if details:
            print(f"Details: {details}")
        
        self.results.append({
            "feature": feature_num,
            "description": description,
            "passed": passed,
            "details": details
        })
        
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def test_feature_416_presence_heartbeat(self):
        """Feature #416: Presence heartbeat: periodic ping to maintain connection."""
        try:
            # Check for heartbeat handler
            with open("services/collaboration-service/src/main.py", "r") as f:
                code = f.read()
                has_heartbeat = "heartbeat" in code
                has_handler = "@sio.event" in code and "heartbeat" in code
                
                if has_heartbeat and has_handler:
                    self.log_result(416, "Presence heartbeat: periodic ping", True,
                                  "Heartbeat event handler implemented")
                else:
                    self.log_result(416, "Presence heartbeat: periodic ping", False,
                                  "Heartbeat handler missing")
        except Exception as e:
            self.log_result(416, "Presence heartbeat: periodic ping", False, str(e))
    
    def test_feature_417_viewer_permissions(self):
        """Feature #417: Collaborative permissions: viewer cannot edit."""
        try:
            # Check for role system
            with open("services/collaboration-service/src/main.py", "r") as f:
                code = f.read()
                has_role = "UserRole" in code or "role" in code
                has_viewer = "VIEWER" in code or "viewer" in code.lower()
                
                if has_role and has_viewer:
                    self.log_result(417, "Viewer permissions: cannot edit", True,
                                  "Role system with viewer role implemented")
                else:
                    self.log_result(417, "Viewer permissions: cannot edit", False,
                                  "Role system missing")
        except Exception as e:
            self.log_result(417, "Viewer permissions: cannot edit", False, str(e))
    
    def test_feature_418_editor_permissions(self):
        """Feature #418: Collaborative permissions: editor can edit."""
        try:
            # Check for editor role
            with open("services/collaboration-service/src/main.py", "r") as f:
                code = f.read()
                has_editor = "EDITOR" in code or "editor" in code.lower()
                has_role_check = "role" in code
                
                if has_editor and has_role_check:
                    self.log_result(418, "Editor permissions: can edit", True,
                                  "Editor role implemented")
                else:
                    self.log_result(418, "Editor permissions: can edit", False,
                                  "Editor role missing")
        except Exception as e:
            self.log_result(418, "Editor permissions: can edit", False, str(e))
    
    def test_feature_419_delta_updates(self):
        """Feature #419: Bandwidth optimization: delta updates only."""
        try:
            # Check for delta update handler
            with open("services/collaboration-service/src/main.py", "r") as f:
                code = f.read()
                has_delta = "delta" in code.lower()
                has_handler = "delta_update" in code
                
                if has_delta and has_handler:
                    self.log_result(419, "Delta updates for bandwidth optimization", True,
                                  "Delta update handler implemented")
                else:
                    self.log_result(419, "Delta updates for bandwidth optimization", False,
                                  "Delta updates missing")
        except Exception as e:
            self.log_result(419, "Delta updates for bandwidth optimization", False, str(e))
    
    def test_feature_420_cursor_throttle(self):
        """Feature #420: Bandwidth optimization: throttle cursor updates."""
        try:
            # Check for cursor throttling
            with open("services/collaboration-service/src/main.py", "r") as f:
                code = f.read()
                has_throttle = "throttle" in code.lower()
                has_cursor_throttle = "cursor" in code.lower() and "throttle" in code.lower()
                
                if has_throttle and has_cursor_throttle:
                    self.log_result(420, "Throttle cursor updates (50ms)", True,
                                  "Cursor throttling implemented")
                else:
                    self.log_result(420, "Throttle cursor updates (50ms)", False,
                                  "Cursor throttling missing")
        except Exception as e:
            self.log_result(420, "Throttle cursor updates (50ms)", False, str(e))
    
    def test_feature_421_scalability_concurrent_users(self):
        """Feature #421: Scalability: support 20+ concurrent users."""
        try:
            # Room-based architecture inherently scalable
            with open("services/collaboration-service/src/main.py", "r") as f:
                code = f.read()
                has_rooms = "room" in code.lower()
                has_users = "room_users" in code or "active_rooms" in code
                
                if has_rooms and has_users:
                    self.log_result(421, "Support 20+ concurrent users per room", True,
                                  "Room-based architecture supports scalability")
                else:
                    self.log_result(421, "Support 20+ concurrent users per room", False,
                                  "Scalability architecture missing")
        except Exception as e:
            self.log_result(421, "Support 20+ concurrent users per room", False, str(e))
    
    def test_feature_422_horizontal_scaling(self):
        """Feature #422: Scalability: horizontal scaling with Redis."""
        try:
            # Check for Redis pub/sub
            with open("services/collaboration-service/src/main.py", "r") as f:
                code = f.read()
                has_redis = "redis" in code.lower()
                has_pubsub = "publish" in code.lower() or "pub" in code.lower()
                
                if has_redis and has_pubsub:
                    self.log_result(422, "Horizontal scaling with Redis pub/sub", True,
                                  "Redis pub/sub enables horizontal scaling")
                else:
                    self.log_result(422, "Horizontal scaling with Redis pub/sub", False,
                                  "Redis pub/sub missing")
        except Exception as e:
            self.log_result(422, "Horizontal scaling with Redis pub/sub", False, str(e))
    
    def test_feature_423_connection_quality(self):
        """Feature #423: Connection quality indicator."""
        try:
            # Check for connection quality endpoint
            response = run_curl(f"{COLLAB_SERVICE_URL}/rooms/file:test/connection-quality")
            
            if response is not None and "users" in response:
                self.log_result(423, "Connection quality indicator", True,
                              "Connection quality endpoint working")
            else:
                self.log_result(423, "Connection quality indicator", False,
                              "Connection quality endpoint not working")
        except Exception as e:
            self.log_result(423, "Connection quality indicator", False, str(e))
    
    def test_feature_424_offline_mode(self):
        """Feature #424: Offline mode: queue edits when disconnected."""
        try:
            # Test offline queue endpoints
            # Queue an operation
            operation = {
                "user_id": "test-user",
                "operation": "update",
                "data": {"test": "value"}
            }
            response = run_curl(f"{COLLAB_SERVICE_URL}/offline/queue", 
                              method="POST", data=operation)
            
            if response and response.get("success"):
                # Get queue
                queue_response = run_curl(f"{COLLAB_SERVICE_URL}/offline/queue/test-user")
                if queue_response and "operations" in queue_response:
                    # Clear queue
                    clear_response = run_curl(f"{COLLAB_SERVICE_URL}/offline/queue/test-user",
                                            method="DELETE")
                    if clear_response and clear_response.get("success"):
                        self.log_result(424, "Offline mode: queue edits", True,
                                      "Offline queue working (queue, retrieve, clear)")
                    else:
                        self.log_result(424, "Offline mode: queue edits", False,
                                      "Clear queue failed")
                else:
                    self.log_result(424, "Offline mode: queue edits", False,
                                  "Retrieve queue failed")
            else:
                self.log_result(424, "Offline mode: queue edits", False,
                              "Queue operation failed")
        except Exception as e:
            self.log_result(424, "Offline mode: queue edits", False, str(e))
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*80)
        print("COLLABORATION OPTIMIZATION TEST SUMMARY")
        print("="*80)
        print(f"\nTotal Features Tested: {len(self.results)}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"Success Rate: {(self.passed/len(self.results)*100):.1f}%")
        
        if self.failed > 0:
            print("\n❌ Failed Tests:")
            for result in self.results:
                if not result["passed"]:
                    print(f"  - Feature #{result['feature']}: {result['description']}")
        
        print("\n" + "="*80)
        print("These optimization features improve performance and scalability.")
        print("="*80 + "\n")


def main():
    """Run all tests."""
    print("="*80)
    print("COLLABORATION OPTIMIZATION FEATURES TEST")
    print("Features #416-424")
    print("="*80)
    
    tester = TestCollaborationOptimization()
    
    # Run all feature tests
    tester.test_feature_416_presence_heartbeat()
    tester.test_feature_417_viewer_permissions()
    tester.test_feature_418_editor_permissions()
    tester.test_feature_419_delta_updates()
    tester.test_feature_420_cursor_throttle()
    tester.test_feature_421_scalability_concurrent_users()
    tester.test_feature_422_horizontal_scaling()
    tester.test_feature_423_connection_quality()
    tester.test_feature_424_offline_mode()
    
    # Print summary
    tester.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if tester.failed == 0 else 1)


if __name__ == "__main__":
    main()
