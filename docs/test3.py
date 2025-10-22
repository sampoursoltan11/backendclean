#!/usr/bin/env python3
"""
Simple script to test Bedrock model access through the FastAPI backend
Usage: python test_bedrock.py [--url BASE_URL] [--message "test message"]
"""

import requests
import argparse
import json
import time

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_direct_bedrock_access():
    """Test direct Bedrock access (without FastAPI)"""
    print("\n1️⃣  Testing Direct Bedrock Access...")
    try:
        import boto3
        from botocore.exceptions import ClientError

        bedrock = boto3.client('bedrock-runtime', region_name='ap-southeast-2')

        # Try to invoke a simple model
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 100,
                "messages": [
                    {
                        "role": "user",
                        "content": "Say 'Hello from Bedrock!' if you can hear me."
                    }
                ]
            })
        )

        response_body = json.loads(response['body'].read())
        message = response_body.get('content', [{}])[0].get('text', '')

        print(f"   ✅ Bedrock API is accessible")
        print(f"   Model response: {message[:100]}")
        return True

    except ImportError:
        print(f"   ⚠️  boto3 not installed - cannot test direct access")
        return None
    except ClientError as e:
        print(f"   ❌ Bedrock access denied: {e.response['Error']['Code']}")
        print(f"   Message: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_websocket_chat(base_url, message):
    """Test chat through WebSocket endpoint"""
    print(f"\n2️⃣  Testing WebSocket Chat Endpoint...")
    print(f"   Message: '{message}'")

    try:
        import websocket
        import json
        import time

        # Connect to WebSocket
        ws_url = base_url.replace('http://', 'ws://').replace('https://', 'wss://')
        ws_url = f"{ws_url}/ws/test-session"

        print(f"   Connecting to: {ws_url}")

        ws = websocket.create_connection(ws_url, timeout=10)
        print(f"   ✅ WebSocket connected")

        # Send message
        ws.send(json.dumps({
            "message": message,
            "session_id": "test-session"
        }))
        print(f"   📤 Message sent")

        # Wait for response
        print(f"   ⏳ Waiting for response...")
        response_text = ""
        timeout = time.time() + 30  # 30 second timeout

        while time.time() < timeout:
            try:
                result = ws.recv()
                data = json.loads(result)

                if data.get('type') == 'message':
                    response_text += data.get('content', '')
                elif data.get('type') == 'done':
                    break

            except websocket.WebSocketTimeoutException:
                break

        ws.close()

        if response_text:
            print(f"   ✅ Received response from agent")
            print(f"   Response (first 200 chars): {response_text[:200]}")
            return True
        else:
            print(f"   ❌ No response received")
            return False

    except ImportError:
        print(f"   ⚠️  websocket-client not installed")
        print(f"   Install with: pip install websocket-client")
        return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_chat_endpoint(base_url, message):
    """Test chat through REST API endpoint if available"""
    print(f"\n3️⃣  Testing REST Chat Endpoint...")
    print(f"   Message: '{message}'")

    try:
        # Try to find a chat endpoint
        response = requests.post(
            f"{base_url}/api/chat",
            json={"message": message, "session_id": "test-session"},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ REST chat endpoint working")
            print(f"   Response: {str(data)[:200]}")
            return True
        elif response.status_code == 404:
            print(f"   ⚠️  REST chat endpoint not found (404)")
            print(f"   This is normal if you only use WebSocket")
            return None
        else:
            print(f"   ❌ Failed (Status: {response.status_code})")
            return False

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_agent_initialization(base_url):
    """Test if agents are initialized"""
    print(f"\n4️⃣  Testing Agent Initialization...")

    try:
        # Check status endpoint for agent info
        response = requests.get(f"{base_url}/status", timeout=5)

        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status endpoint accessible")

            # Check for agent-related info
            if 'connected_sessions' in data:
                print(f"   Connected sessions: {data['connected_sessions']}")

            return True
        else:
            print(f"   ⚠️  Status endpoint returned: {response.status_code}")
            return None

    except Exception as e:
        print(f"   ⚠️  Status endpoint not available: {e}")
        return None

def test_strands_import():
    """Test if Strands framework is available"""
    print(f"\n5️⃣  Testing Strands Framework...")

    try:
        from strands import Agent
        from strands.session import FileSessionManager
        print(f"   ✅ Strands framework is installed")
        return True
    except ImportError as e:
        print(f"   ❌ Strands not installed: {e}")
        print(f"   Install with: pip install strands-framework")
        return False

def test_backend_agents():
    """Test if backend agents can be imported"""
    print(f"\n6️⃣  Testing Backend Agent Imports...")

    try:
        import sys
        import os

        # Add backend to path
        backend_path = os.path.join(os.getcwd(), 'backend')
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)

        from backend.variants.enterprise.agents.status_agent import StatusAgent
        print(f"   ✅ StatusAgent can be imported")

        from backend.variants.enterprise.agents.question_agent import QuestionAgent
        print(f"   ✅ QuestionAgent can be imported")

        return True

    except ImportError as e:
        print(f"   ❌ Agent import failed: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test Bedrock model access through FastAPI backend')
    parser.add_argument('--url', '-u',
                       help='Base URL of the backend (default: http://localhost:8000)',
                       default='http://localhost:8000')
    parser.add_argument('--message', '-m',
                       help='Test message to send (default: "Hello, can you hear me?")',
                       default='Hello, can you hear me?')
    args = parser.parse_args()

    base_url = args.url.rstrip('/')

    print_section("Bedrock Model Test Suite")
    print(f"\n🔍 Testing Bedrock access through: {base_url}")

    results = {
        'direct_bedrock': None,
        'strands_framework': None,
        'backend_agents': None,
        'agent_init': None,
        'websocket_chat': None,
        'rest_chat': None,
    }

    # Test 1: Direct Bedrock access
    results['direct_bedrock'] = test_direct_bedrock_access()

    # Test 2: Strands framework
    results['strands_framework'] = test_strands_import()

    # Test 3: Backend agents
    results['backend_agents'] = test_backend_agents()

    # Test 4: Agent initialization
    results['agent_init'] = test_agent_initialization(base_url)

    # Test 5: WebSocket chat
    results['websocket_chat'] = test_websocket_chat(base_url, args.message)

    # Test 6: REST chat (optional)
    results['rest_chat'] = test_chat_endpoint(base_url, args.message)

    # Print summary
    print_section("Test Results Summary")

    print("\n📊 Results:")
    status_map = {True: "✅ PASS", False: "❌ FAIL", None: "⚠️  SKIP"}

    print(f"   Direct Bedrock Access      {status_map[results['direct_bedrock']]}")
    print(f"   Strands Framework          {status_map[results['strands_framework']]}")
    print(f"   Backend Agents             {status_map[results['backend_agents']]}")
    print(f"   Agent Initialization       {status_map[results['agent_init']]}")
    print(f"   WebSocket Chat             {status_map[results['websocket_chat']]}")
    print(f"   REST Chat                  {status_map[results['rest_chat']]}")

    # Overall assessment
    print("\n" + "=" * 80)

    critical_tests = ['direct_bedrock', 'strands_framework', 'backend_agents']
    critical_passed = sum(1 for k in critical_tests if results[k] is True)

    chat_tests = ['websocket_chat', 'rest_chat']
    chat_passed = any(results[k] is True for k in chat_tests)

    print(f"\n📈 Critical Tests: {critical_passed}/{len(critical_tests)} passed")

    if results['direct_bedrock'] is True and results['strands_framework'] is True and results['backend_agents'] is True:
        print("✅ Backend setup is correct - Bedrock access is working!")

        if chat_passed:
            print("✅ Can communicate with Bedrock through the backend!")
        else:
            print("⚠️  Backend setup OK but chat endpoint may need configuration")
    elif results['direct_bedrock'] is False:
        print("❌ No Bedrock access - Check AWS credentials and permissions")
    elif results['strands_framework'] is False:
        print("❌ Strands framework missing - Install required packages")
    elif results['backend_agents'] is False:
        print("❌ Backend agents not loading - Check backend code")
    else:
        print("⚠️  Partial setup - Some components may need attention")

    print("=" * 80)

    # Recommendations
    if results['direct_bedrock'] is False:
        print("\n💡 RECOMMENDATION: Check Bedrock permissions")
        print("   Run: python check_iam_policies.py")
        print("   Required permissions:")
        print("   - bedrock:InvokeModel")
        print("   - bedrock:InvokeModelWithResponseStream")

    if results['strands_framework'] is False:
        print("\n💡 RECOMMENDATION: Install Strands framework")
        print("   pip install strands-framework")

    if results['websocket_chat'] is False and results['rest_chat'] is False:
        print("\n💡 RECOMMENDATION: Check if server is running")
        print("   python -m uvicorn backend.api.main:app --reload")

    if results['direct_bedrock'] is None:
        print("\n💡 RECOMMENDATION: Install boto3")
        print("   pip install boto3")

if __name__ == "__main__":
    main()
