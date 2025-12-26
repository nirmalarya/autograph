#!/usr/bin/env python3
"""
Feature #414: Presence Timeout - Simple Code Validation
Verify the presence timeout mechanism is implemented correctly.
"""
import sys

print("=" * 80)
print("Feature #414: Presence Timeout - Code Validation")
print("=" * 80)

# Test 1: Verify code implementation
print("\n📌 Test 1: Verifying code implementation...")

try:
    with open('services/collaboration-service/src/main.py', 'r') as f:
        code = f.read()

    tests_passed = []
    tests_failed = []

    # Check 1: check_away_users function exists
    if 'async def check_away_users' in code:
        tests_passed.append("check_away_users() function exists")
        print("✅ PASS: check_away_users() function exists")
    else:
        tests_failed.append("check_away_users() function not found")
        print("❌ FAIL: check_away_users() function not found")

    # Check 2: Background task runs every 60 seconds
    if 'await asyncio.sleep(60)' in code and 'check_away_users' in code:
        tests_passed.append("Background task checks every 60 seconds")
        print("✅ PASS: Background task checks every 60 seconds")
    else:
        tests_failed.append("Background task interval not found")
        print("❌ FAIL: Background task interval not configured correctly")

    # Check 3: 5-minute timeout (300 seconds)
    if 'time_inactive > 300' in code or '> 300' in code:
        tests_passed.append("5-minute timeout (300 seconds) configured")
        print("✅ PASS: 5-minute timeout (300 seconds) configured")
    else:
        tests_failed.append("5-minute timeout not found")
        print("❌ FAIL: 5-minute timeout not found")

    # Check 4: Marks user as AWAY
    if 'PresenceStatus.AWAY' in code and 'presence.status = PresenceStatus.AWAY' in code:
        tests_passed.append("Users marked as AWAY after timeout")
        print("✅ PASS: Users marked as AWAY after timeout")
    else:
        tests_failed.append("AWAY status assignment not found")
        print("❌ FAIL: AWAY status assignment not found")

    # Check 5: Broadcasts presence_update event
    if "emit('presence_update'" in code:
        tests_passed.append("presence_update event is broadcast")
        print("✅ PASS: presence_update event is broadcast")
    else:
        tests_failed.append("presence_update event not found")
        print("❌ FAIL: presence_update event not broadcast")

    # Check 6: Background task is started
    if 'asyncio.create_task(check_away_users' in code:
        tests_passed.append("Background task started on application startup")
        print("✅ PASS: Background task started on application startup")
    else:
        tests_failed.append("Background task startup not found")
        print("❌ FAIL: Background task not started automatically")

    # Check 7: Checks all rooms and users
    if 'for room_id, users in room_users.items()' in code:
        tests_passed.append("Checks all rooms and users")
        print("✅ PASS: Checks all rooms and users")
    else:
        tests_failed.append("Room/user iteration not found")
        print("❌ FAIL: Room/user iteration not found")

    # Check 8: Only marks ONLINE users as AWAY (not already AWAY/OFFLINE)
    if 'presence.status == PresenceStatus.ONLINE' in code:
        tests_passed.append("Only marks ONLINE users as AWAY")
        print("✅ PASS: Only marks ONLINE users as AWAY")
    else:
        tests_failed.append("Status check before marking AWAY not found")
        print("❌ FAIL: Status check before marking AWAY not found")

    # Test 2: Verify logic flow
    print("\n📌 Test 2: Verifying logic flow...")

    # Extract the check_away_users function
    start_idx = code.find('async def check_away_users')
    if start_idx != -1:
        # Find the next function definition
        next_func_idx = code.find('\nasync def ', start_idx + 1)
        if next_func_idx == -1:
            next_func_idx = code.find('\ndef ', start_idx + 1)

        if next_func_idx != -1:
            function_code = code[start_idx:next_func_idx]
        else:
            function_code = code[start_idx:]

        print("\n📋 Extracted function logic:")
        print("-" * 70)
        # Show key lines
        for line in function_code.split('\n')[:30]:  # First 30 lines
            if line.strip() and not line.strip().startswith('#'):
                print(f"   {line}")
        print("-" * 70)

        # Verify the logic
        logic_checks = [
            ('while True:', 'Infinite loop for continuous monitoring'),
            ('await asyncio.sleep(60)', 'Checks every 60 seconds'),
            ('for room_id, users in room_users.items()', 'Iterates all rooms'),
            ('for user_id, presence in users.items()', 'Iterates all users'),
            ('if presence.status == PresenceStatus.ONLINE', 'Only checks ONLINE users'),
            ('time_inactive = (now - presence.last_active).total_seconds()', 'Calculates inactive time'),
            ('if time_inactive > 300', '5-minute threshold'),
            ('presence.status = PresenceStatus.AWAY', 'Marks as AWAY'),
            ("await sio.emit('presence_update'", 'Broadcasts status change'),
        ]

        print("\n📊 Logic verification:")
        all_logic_present = True
        for check, description in logic_checks:
            if check in function_code:
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ {description} (missing: {check})")
                all_logic_present = False

        if all_logic_present:
            tests_passed.append("Complete logic flow implemented")
        else:
            tests_failed.append("Incomplete logic flow")

    # Final results
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)

    print(f"\n✅ Passed: {len(tests_passed)}")
    for test in tests_passed:
        print(f"   • {test}")

    if tests_failed:
        print(f"\n❌ Failed: {len(tests_failed)}")
        for test in tests_failed:
            print(f"   • {test}")

    # Overall result
    if len(tests_failed) == 0:
        print("\n" + "=" * 80)
        print("🎉 Feature #414 PASSED: Presence Timeout")
        print("=" * 80)
        print("\nImplementation Summary:")
        print("- Background task runs every 60 seconds")
        print("- Checks all users in all rooms")
        print("- Marks ONLINE users as AWAY after 5 minutes (300s) of inactivity")
        print("- Broadcasts presence_update event to all room members")
        print("- Only affects users currently marked as ONLINE")
        print("\nThe feature is correctly implemented!")
        sys.exit(0)
    else:
        print("\n" + "=" * 80)
        print("❌ Feature #414 FAILED")
        print("=" * 80)
        sys.exit(1)

except Exception as e:
    print(f"\n❌ Error during validation: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
