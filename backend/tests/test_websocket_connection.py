#!/usr/bin/env python3
"""
WebSocket Connection Test Script
Tests WebSocket connectivity through Vite proxy and direct to backend
"""

import asyncio
import websockets
import json
import sys
from datetime import datetime

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def log(message, color=RESET):
    """Print colored log message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{timestamp}] {message}{RESET}")

async def test_websocket(url, test_name):
    """Test WebSocket connection"""
    log(f"\n{'='*60}", BLUE)
    log(f"Testing: {test_name}", BLUE)
    log(f"URL: {url}", BLUE)
    log(f"{'='*60}", BLUE)

    try:
        log("Connecting to WebSocket...", YELLOW)
        async with websockets.connect(url, timeout=10) as websocket:
            log("✓ WebSocket connected successfully!", GREEN)

            # Wait for welcome message
            try:
                welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=5)
                log(f"✓ Received welcome message:", GREEN)
                try:
                    parsed = json.loads(welcome_msg)
                    print(json.dumps(parsed, indent=2))
                except:
                    print(welcome_msg)
            except asyncio.TimeoutError:
                log("No welcome message received (timeout)", YELLOW)

            # Send test message
            test_message = {
                "type": "message",
                "content": "Test message from Python script",
                "context": {
                    "test": True,
                    "timestamp": datetime.now().isoformat()
                }
            }

            log("Sending test message...", YELLOW)
            await websocket.send(json.dumps(test_message))
            log("✓ Message sent!", GREEN)

            # Wait for response
            try:
                log("Waiting for response...", YELLOW)
                response = await asyncio.wait_for(websocket.recv(), timeout=30)
                log("✓ Received response:", GREEN)
                try:
                    parsed = json.loads(response)
                    print(json.dumps(parsed, indent=2))
                except:
                    print(response[:500])  # Print first 500 chars
            except asyncio.TimeoutError:
                log("No response received (30s timeout)", YELLOW)

            # Close connection
            await websocket.close()
            log("✓ Connection closed cleanly", GREEN)
            return True

    except websockets.exceptions.InvalidStatusCode as e:
        log(f"✗ Invalid status code: {e.status_code}", RED)
        log(f"  This usually means the WebSocket endpoint doesn't exist", RED)
        return False
    except websockets.exceptions.WebSocketException as e:
        log(f"✗ WebSocket error: {e}", RED)
        return False
    except ConnectionRefusedError:
        log(f"✗ Connection refused - server not running?", RED)
        return False
    except asyncio.TimeoutError:
        log(f"✗ Connection timeout", RED)
        return False
    except Exception as e:
        log(f"✗ Unexpected error: {e}", RED)
        return False

async def main():
    """Run all WebSocket tests"""
    session_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    log("\n" + "="*60, BLUE)
    log("WebSocket Connection Test Suite", BLUE)
    log("="*60, BLUE)

    results = []

    # Test 1: Direct backend connection
    backend_url = f"ws://localhost:8000/ws/enterprise/{session_id}_backend"
    result1 = await test_websocket(backend_url, "Direct Backend Connection (Port 8000)")
    results.append(("Direct Backend", result1))

    await asyncio.sleep(2)

    # Test 2: Via Vite proxy
    proxy_url = f"ws://localhost:5173/ws/enterprise/{session_id}_proxy"
    result2 = await test_websocket(proxy_url, "Via Vite Proxy (Port 5173)")
    results.append(("Vite Proxy", result2))

    # Summary
    log("\n" + "="*60, BLUE)
    log("Test Summary", BLUE)
    log("="*60, BLUE)

    for test_name, result in results:
        status = f"{GREEN}✓ PASS{RESET}" if result else f"{RED}✗ FAIL{RESET}"
        log(f"{test_name}: {status}", RESET)

    # Overall result
    all_passed = all(result for _, result in results)
    if all_passed:
        log("\n✓ All tests passed!", GREEN)
        return 0
    else:
        log("\n✗ Some tests failed", RED)
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        log("\nTest interrupted by user", YELLOW)
        sys.exit(130)
