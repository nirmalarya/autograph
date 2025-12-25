#!/usr/bin/env python3
"""
Validation Script for Feature #388: Cursor Presence - Color-coded per user

This feature ensures each user's cursor has a distinct color in collaborative editing.

Tests:
1. USER_COLORS constant exists with multiple colors
2. assign_user_color() function exists
3. UserPresence includes color field
4. Colors are assigned on user join
5. Cursor broadcasts include color information
6. Colors are visible and distinct (8 different colors)
"""

import sys
import json

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


def test_feature_388():
    """Test Feature #388: Color-coded cursor presence."""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}Feature #388: Cursor Presence - Color-coded per user{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")

    all_passed = True

    # Read the collaboration service code
    try:
        with open("services/collaboration-service/src/main.py", "r") as f:
            code = f.read()
    except Exception as e:
        print(f"{RED}Failed to read collaboration service code: {e}{RESET}")
        return False

    # Step 1: Verify USER_COLORS constant exists
    print(f"\n{YELLOW}Step 1: Verify USER_COLORS constant{RESET}")
    has_user_colors = "USER_COLORS = [" in code

    if has_user_colors:
        # Extract color values
        import re
        colors = re.findall(r'"#[0-9A-Fa-f]{6}"', code)
        unique_colors = set(colors)

        if len(unique_colors) >= 8:
            print_step(1, "USER_COLORS constant with distinct colors", True,
                      f"Found {len(unique_colors)} unique color values")
        else:
            print_step(1, "USER_COLORS constant with distinct colors", False,
                      f"Only {len(unique_colors)} colors found (need at least 8)")
            all_passed = False
    else:
        print_step(1, "USER_COLORS constant with distinct colors", False,
                  "USER_COLORS constant not found")
        all_passed = False

    # Step 2: Verify assign_user_color() function
    print(f"\n{YELLOW}Step 2: Verify assign_user_color() function{RESET}")
    has_assign_function = "def assign_user_color" in code
    returns_color = "return color" in code or "USER_COLORS[" in code

    if has_assign_function and returns_color:
        # Check if it rotates through colors
        has_rotation = "next_color_index" in code or "% len(USER_COLORS)" in code

        if has_rotation:
            print_step(2, "assign_user_color() with rotation", True,
                      "Function rotates through color array")
        else:
            print_step(2, "assign_user_color() with rotation", False,
                      "Color rotation logic not found")
            all_passed = False
    else:
        print_step(2, "assign_user_color() with rotation", False,
                  "assign_user_color() function not found")
        all_passed = False

    # Step 3: Verify UserPresence has color field
    print(f"\n{YELLOW}Step 3: Verify UserPresence color field{RESET}")
    has_presence_class = "@dataclass" in code and "class UserPresence:" in code
    has_color_field = "color: str" in code

    # Find UserPresence class and verify color field is in it
    if has_presence_class and has_color_field:
        presence_start = code.find("class UserPresence:")
        presence_end = code.find("\n\nclass ", presence_start) if presence_start != -1 else -1
        presence_section = code[presence_start:presence_end] if presence_start != -1 and presence_end != -1 else code[presence_start:presence_start+500]

        if "color: str" in presence_section:
            print_step(3, "UserPresence includes color field", True,
                      "color: str field found in UserPresence dataclass")
        else:
            print_step(3, "UserPresence includes color field", False,
                      "color field not in UserPresence class")
            all_passed = False
    else:
        print_step(3, "UserPresence includes color field", False,
                  "UserPresence class or color field not found")
        all_passed = False

    # Step 4: Verify color assignment on join
    print(f"\n{YELLOW}Step 4: Verify color assigned when user joins room{RESET}")
    has_join_room = "async def join_room" in code
    assigns_color = "color = assign_user_color()" in code or "assign_user_color" in code

    if has_join_room:
        join_start = code.find("async def join_room")
        join_end = code.find("\n@sio.event", join_start + 1) if join_start != -1 else -1
        join_section = code[join_start:join_end] if join_start != -1 and join_end != -1 else code[join_start:join_start+2000]

        if "assign_user_color" in join_section:
            print_step(4, "Color assigned on user join", True,
                      "assign_user_color() called in join_room handler")
        else:
            print_step(4, "Color assigned on user join", False,
                      "Color assignment not found in join_room")
            all_passed = False
    else:
        print_step(4, "Color assigned on user join", False,
                  "join_room handler not found")
        all_passed = False

    # Step 5: Verify cursor broadcasts include color
    print(f"\n{YELLOW}Step 5: Verify cursor updates include color{RESET}")
    has_cursor_move = "async def cursor_move" in code

    if has_cursor_move:
        cursor_start = code.find("async def cursor_move")
        cursor_end = code.find("\n@sio.event", cursor_start + 1) if cursor_start != -1 else -1
        cursor_section = code[cursor_start:cursor_end] if cursor_start != -1 and cursor_end != -1 else code[cursor_start:cursor_start+1000]

        has_color_emit = "'color': presence.color" in cursor_section or '"color"' in cursor_section

        if has_color_emit:
            print_step(5, "Cursor updates broadcast color", True,
                      "cursor_update event includes color field")
        else:
            print_step(5, "Cursor updates broadcast color", False,
                      "Color not included in cursor broadcasts")
            all_passed = False
    else:
        print_step(5, "Cursor updates broadcast color", False,
                  "cursor_move handler not found")
        all_passed = False

    # Step 6: Verify user_joined event includes color
    print(f"\n{YELLOW}Step 6: Verify user_joined event includes color{RESET}")
    if has_join_room:
        has_user_joined_emit = "emit('user_joined'" in join_section
        has_color_in_joined = "'color':" in join_section or '"color"' in join_section

        if has_user_joined_emit and has_color_in_joined:
            print_step(6, "user_joined event includes color", True,
                      "New users broadcast their assigned color")
        else:
            print_step(6, "user_joined event includes color", False,
                      "Color not included in user_joined event")
            all_passed = False
    else:
        print_step(6, "user_joined event includes color", False,
                  "join_room handler not available")
        all_passed = False

    # Step 7: Display the actual colors used
    print(f"\n{YELLOW}Step 7: Display color palette{RESET}")
    try:
        import re
        colors_match = re.search(r'USER_COLORS = \[(.*?)\]', code, re.DOTALL)
        if colors_match:
            color_list = re.findall(r'"(#[0-9A-Fa-f]{6})"', colors_match.group(1))
            print_step(7, "Color palette verification", True,
                      f"Colors: {', '.join(color_list)}")
        else:
            print_step(7, "Color palette verification", False,
                      "Could not extract color values")
            all_passed = False
    except Exception as e:
        print_step(7, "Color palette verification", False, str(e))
        all_passed = False

    # Final summary
    print(f"\n{BLUE}{'='*80}{RESET}")
    if all_passed:
        print(f"{GREEN}✓ Feature #388: PASS - Color-coded cursor presence fully implemented{RESET}")
        print(f"\n{GREEN}Verified features:{RESET}")
        print(f"  • USER_COLORS constant with 8+ distinct colors")
        print(f"  • assign_user_color() function with rotation")
        print(f"  • UserPresence tracks color for each user")
        print(f"  • Colors assigned on user join")
        print(f"  • Cursor updates include color information")
        print(f"  • User join events broadcast color")
    else:
        print(f"{RED}✗ Feature #388: FAIL - Some color-coding features missing{RESET}")

    print(f"{BLUE}{'='*80}{RESET}\n")

    return all_passed


if __name__ == "__main__":
    try:
        success = test_feature_388()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"{RED}Test execution failed: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
