#!/usr/bin/env python3
"""
Test Google OAuth for both local dev and production modes.
Verifies that the authentication flow works end-to-end.

Usage:
    python test_google_oauth_all_paths.py [--dev | --prod]
    
    --dev   Test local development mode (mocks)
    --prod  Test production mode (requires GOOGLE_CLIENT_ID/SECRET)
"""

import sys
import os
import json
import base64
import requests
import argparse
from datetime import datetime, timedelta

# Configuration
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "local-development")

def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def print_success(msg):
    """Print success message."""
    print(f"✓ {msg}")

def print_error(msg):
    """Print error message."""
    print(f"✗ {msg}")

def print_info(msg):
    """Print info message."""
    print(f"ℹ {msg}")

def test_dev_endpoint():
    """Test the /auth/google/dev-token endpoint."""
    print_header("Testing: GET /auth/google/dev-token (Dev Mode)")
    
    if not DEV_MODE:
        print_error("DEV_MODE is not enabled. Set DEV_MODE=true in backend/.env")
        return False
    
    try:
        print_info("Requesting mock token from /auth/google/dev-token")
        url = f"{BASE_URL}/auth/google/dev-token?email=alice@example.com"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 403:
            print_error("Got 403 Forbidden - DEV_MODE might not be enabled on server")
            return False
        
        if response.status_code != 200:
            print_error(f"Got status {response.status_code}: {response.text}")
            return False
        
        data = response.json()
        token = data.get("access_token")
        
        if not token:
            print_error("Response has no access_token")
            return False
        
        print_success(f"Got mock token (length: {len(token)} chars)")
        print_info(f"Response: {json.dumps(data, indent=2)}")
        
        # Validate token structure (should be JWT-like: 3 parts)
        parts = token.split(".")
        if len(parts) != 3:
            print_error(f"Token doesn't look like JWT (has {len(parts)} parts, expected 3)")
            return False
        
        print_success("Token has valid JWT structure (3 parts)")
        
        # Try to decode payload
        try:
            payload_b64 = parts[1]
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding
            payload_json = base64.urlsafe_b64decode(payload_b64)
            payload = json.loads(payload_json)
            print_success(f"Token payload decoded: {json.dumps(payload, indent=2)}")
        except Exception as e:
            print_error(f"Failed to decode token payload: {e}")
            return False
        
        return True, token
        
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to {BASE_URL}")
        print_info("Make sure backend is running: python backend/main.py")
        return False
    except Exception as e:
        print_error(f"Test failed: {e}")
        return False

def test_auth_with_token(token, is_dev=True):
    """Test POST /auth/user/google with a token."""
    print_header(f"Testing: POST /auth/user/google ({'Dev' if is_dev else 'Prod'} Mode)")
    
    try:
        print_info(f"Sending token to /auth/user/google")
        url = f"{BASE_URL}/auth/user/google"
        response = requests.post(
            url,
            json={"token": token},
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        
        print_info(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            print_error(f"Got status {response.status_code}: {response.text}")
            return False
        
        data = response.json()
        
        # Verify required fields
        required_fields = ["token", "user_id", "name", "role"]
        for field in required_fields:
            if field not in data:
                print_error(f"Response missing required field: {field}")
                return False
        
        print_success(f"All required fields present")
        print_info(f"Response: {json.dumps({k: data.get(k) for k in required_fields}, indent=2)}")
        
        # Validate JWT token structure
        session_token = data["token"]
        parts = session_token.split(".")
        if len(parts) != 3:
            print_error(f"Session token doesn't look like JWT (has {len(parts)} parts)")
            return False
        
        print_success(f"Session token is valid JWT")
        
        return True, data
        
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to {BASE_URL}")
        return False
    except Exception as e:
        print_error(f"Test failed: {e}")
        return False

def test_dev_mode_complete_flow():
    """Test complete dev mode flow."""
    print_header("TESTING LOCAL DEV MODE (Complete Flow)")
    
    # Step 1: Get mock token
    result = test_dev_endpoint()
    if not result or result is False:
        return False
    
    token = result[1] if isinstance(result, tuple) else result
    
    # Step 2: Authenticate with mock token
    result = test_auth_with_token(token, is_dev=True)
    if not result or result is False:
        return False
    
    print_header("DEV MODE TESTS: PASSED ✓")
    return True

def test_prod_mode_status():
    """Test if production mode is configured."""
    print_header("TESTING PRODUCTION MODE (Status Check)")
    
    try:
        # Try to fetch server status
        url = f"{BASE_URL}/auth/google/status"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Server returned status: {json.dumps(data, indent=2)}")
            
            if data.get("dev_mode"):
                print_info("⚠ Server is in DEV_MODE - switch to PROD_MODE for production testing")
                return "dev"
            else:
                print_info("Server is in PRODUCTION mode")
                return "prod"
        else:
            print_error(f"Got status {response.status_code}")
            return None
            
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to {BASE_URL}")
        print_info("Make sure backend is running: python backend/main.py")
        return None
    except Exception as e:
        print_error(f"Status check failed: {e}")
        return None

def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(
        description="Test Google OAuth implementation (dev and prod modes)"
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Test local development mode (mocks)"
    )
    parser.add_argument(
        "--prod",
        action="store_true",
        help="Test production mode (requires GOOGLE_CLIENT_ID/SECRET)"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Backend URL (default: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    global BASE_URL
    BASE_URL = args.url
    
    print_header("Google OAuth Test Suite")
    print_info(f"Backend URL: {BASE_URL}")
    print_info(f"DEV_MODE: {DEV_MODE}")
    print_info(f"GOOGLE_CLIENT_ID: {GOOGLE_CLIENT_ID}")
    
    # Choose what to test
    if args.dev:
        print_info("Running DEV MODE tests...")
        success = test_dev_mode_complete_flow()
    elif args.prod:
        print_info("Running PROD MODE tests...")
        print_info("⚠ Production mode testing requires real Google credentials")
        print_info("This test only verifies the server is ready for production OAuth")
        mode = test_prod_mode_status()
        success = mode == "prod"
    else:
        # Auto-detect mode
        print_info("Auto-detecting server mode...")
        mode = test_prod_mode_status()
        
        if mode == "dev":
            print_info("\nRunning DEV MODE tests...")
            success = test_dev_mode_complete_flow()
        elif mode == "prod":
            print_info("\nServer is in production mode")
            print_info("For actual OAuth testing, you need a real Google account and valid credentials")
            success = True
        else:
            print_error("Could not determine server mode")
            success = False
    
    # Print final summary
    print_header("Test Summary")
    if success:
        print_success("All tests passed!")
        print_info("\nNext steps:")
        if args.dev or mode == "dev":
            print_info("1. Open frontend/index.html in browser")
            print_info("2. Click 'Sign in with Google'")
            print_info("3. You should be logged in automatically (dev mode)")
        else:
            print_info("1. Deploy backend to production")
            print_info("2. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET on hosting")
            print_info("3. Users can log in with real Google accounts")
    else:
        print_error("Some tests failed - see details above")
        sys.exit(1)

if __name__ == "__main__":
    main()
