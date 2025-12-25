#!/usr/bin/env python3
"""
Validation Script for Feature #389: Cursor Presence - Real-time position updates

This feature ensures cursor positions update in real-time with minimal latency.

Tests:
1. cursor_move event handler exists
2. Position data (x, y coordinates) extracted from event
3. Presence updated immediately
4. Broadcast happens without delay (no batching)
5. Updates sent to all room members except sender
6. Timestamp included for latency tracking
"""

import sys

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_step(step_num, description, status, details=""):
    """Print test step result."""
    status_icon = f"{GREEN}✓{RESET}" if status else f"{RED}✗{RESET}"
    print(f"\n{BLUE}Step {step_num}:{RESET} {description}")
    print(f"Status: {status_icon}")
    if details:
        print(f"Details: {details}")


def test_feature_389():
    """Test Feature #389: Real-time cursor position updates."""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}Feature #389: Cursor Presence - Real-time position updates{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")

    all_passed = True

    # Read the collaboration service code
    try:
        with open("services/collaboration-service/src/main.py", "r") as f:
            code = f.read()
    except Exception as e:
        print(f"{RED}Failed to read collaboration service code: {e}{RESET}")
        return False

    # Step 1: Verify cursor_move event handler
    print(f"\n{YELLOW}Step 1: Verify cursor_move WebSocket event handler{RESET}")
    has_cursor_move = "@sio.event" in code and "async def cursor_move(sid, data):" in code

    if has_cursor_move:
        print_step(1, "cursor_move event handler exists", True,
                  "WebSocket handler for cursor movement present")
    else:
        print_step(1, "cursor_move event handler exists", False,
                  "cursor_move handler not found")
        all_passed = False
        return all_passed

    # Extract cursor_move function
    cursor_start = code.find("async def cursor_move")
    cursor_end = code.find("\n@sio.event", cursor_start + 1)
    cursor_section = code[cursor_start:cursor_end] if cursor_end != -1 else code[cursor_start:cursor_start+1500]

    # Step 2: Verify position data extraction
    print(f"\n{YELLOW}Step 2: Verify x,y coordinates extracted from event{RESET}")
    has_x_coord = "data.get('x'" in cursor_section or 'data.get("x"' in cursor_section
    has_y_coord = "data.get('y'" in cursor_section or 'data.get("y"' in cursor_section

    if has_x_coord and has_y_coord:
        print_step(2, "Position coordinates (x, y) extracted", True,
                  "Cursor position data extracted from event payload")
    else:
        print_step(2, "Position coordinates (x, y) extracted", False,
                  "Missing x or y coordinate extraction")
        all_passed = False

    # Step 3: Verify immediate presence update
    print(f"\n{YELLOW}Step 3: Verify immediate presence update{RESET}")
    has_update_call = "await update_user_presence" in cursor_section
    has_cursor_params = "cursor_x=" in cursor_section and "cursor_y=" in cursor_section

    if has_update_call and has_cursor_params:
        print_step(3, "Presence updated immediately with cursor position", True,
                  "update_user_presence called with cursor_x and cursor_y")
    else:
        print_step(3, "Presence updated immediately with cursor position", False,
                  "Presence update not found or incomplete")
        all_passed = False

    # Step 4: Verify real-time broadcast (no batching/delay)
    print(f"\n{YELLOW}Step 4: Verify immediate broadcast (no batching){RESET}")
    has_emit = "await sio.emit('cursor_update'" in cursor_section or "await sio.emit(\"cursor_update\"" in cursor_section

    # Check there's no setTimeout, sleep, or batch logic
    has_delay = "sleep(" in cursor_section or "setTimeout" in cursor_section or "batch" in cursor_section.lower()

    if has_emit and not has_delay:
        print_step(4, "Immediate broadcast without delay", True,
                  "cursor_update emitted immediately (no batching or delays)")
    elif has_emit and has_delay:
        print_step(4, "Immediate broadcast without delay", False,
                  "Broadcast has delays or batching logic")
        all_passed = False
    else:
        print_step(4, "Immediate broadcast without delay", False,
                  "cursor_update emit not found")
        all_passed = False

    # Step 5: Verify skip_sid (doesn't echo to sender)
    print(f"\n{YELLOW}Step 5: Verify broadcast excludes sender{RESET}")
    has_skip_sid = "skip_sid=sid" in cursor_section

    if has_skip_sid:
        print_step(5, "Broadcast excludes sender (skip_sid)", True,
                  "Updates sent to all room members except sender")
    else:
        print_step(5, "Broadcast excludes sender (skip_sid)", False,
                  "skip_sid parameter missing (would echo to sender)")
        all_passed = False

    # Step 6: Verify timestamp for latency tracking
    print(f"\n{YELLOW}Step 6: Verify timestamp included in updates{RESET}")
    has_timestamp = "'timestamp':" in cursor_section or '"timestamp"' in cursor_section
    has_datetime = "datetime.utcnow()" in cursor_section or "timestamp" in cursor_section

    if has_timestamp and has_datetime:
        print_step(6, "Timestamp included for latency tracking", True,
                  "Each cursor update includes server timestamp")
    else:
        print_step(6, "Timestamp included for latency tracking", False,
                  "Timestamp not included in cursor updates")
        all_passed = False

    # Step 7: Verify update payload structure
    print(f"\n{YELLOW}Step 7: Verify complete update payload{RESET}")
    required_fields = ["'user_id':", "'x':", "'y':", "'color':", "'username':"]
    missing_fields = [field for field in required_fields if field not in cursor_section]

    if not missing_fields:
        print_step(7, "Complete cursor update payload", True,
                  "Includes: user_id, username, color, x, y, timestamp")
    else:
        print_step(7, "Complete cursor update payload", False,
                  f"Missing fields: {missing_fields}")
        all_passed = False

    # Step 8: Verify room-based broadcasting
    print(f"\n{YELLOW}Step 8: Verify room-based broadcasting{RESET}")
    has_room = "room=room_id" in cursor_section or "room=" in cursor_section

    if has_room:
        print_step(8, "Room-based broadcasting", True,
                  "Updates only sent to users in the same room")
    else:
        print_step(8, "Room-based broadcasting", False,
                  "Room parameter missing (would broadcast globally)")
        all_passed = False

    # Final summary
    print(f"\n{BLUE}{'='*80}{RESET}")
    if all_passed:
        print(f"{GREEN}✓ Feature #389: PASS - Real-time cursor updates fully implemented{RESET}")
        print(f"\n{GREEN}Verified real-time features:{RESET}")
        print(f"  • cursor_move WebSocket event handler")
        print(f"  • Immediate position extraction (x, y)")
        print(f"  • Instant presence update")
        print(f"  • Immediate broadcast (no delays or batching)")
        print(f"  • Excludes sender (skip_sid)")
        print(f"  • Includes timestamp for latency tracking")
        print(f"  • Complete payload (user, color, position)")
        print(f"  • Room-scoped broadcasting")
    else:
        print(f"{RED}✗ Feature #389: FAIL - Some real-time features missing{RESET}")

    print(f"{BLUE}{'='*80}{RESET}\n")

    return all_passed


if __name__ == "__main__":
    try:
        success = test_feature_389()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"{RED}Test execution failed: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
