#!/usr/bin/env python3
"""
Manual test script for the modified email endpoints
"""

import requests
import json

BASE_URL = "http://localhost:5001/api"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_add_user_no_token():
    """Test add_user with no token"""
    print("\n🔍 Testing add_user with no token...")
    response = requests.post(f"{BASE_URL}/add_user", 
                           headers={'Content-Type': 'application/json'})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 400

def test_add_user_invalid_token():
    """Test add_user with invalid token"""
    print("\n🔍 Testing add_user with invalid token...")
    invalid_token = {"invalid": "token"}
    response = requests.post(f"{BASE_URL}/add_user", 
                           json=invalid_token)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 400

def test_get_emails_no_token():
    """Test get_emails without stored token"""
    print("\n🔍 Testing get_emails without stored token...")
    response = requests.get(f"{BASE_URL}/emails?user_email=test@example.com")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 401

def test_token_storage():
    """Test token storage functionality"""
    print("\n🔍 Testing token storage...")
    from app.utils.token_storage import token_storage
    
    # Test storing and retrieving token
    test_token = {
        'access_token': 'test_token_123',
        'refresh_token': 'refresh_123',
        'token_type': 'Bearer',
        'expires_in': 3600,
        'scope': 'test_scope'
    }
    
    user_email = 'test@example.com'
    
    # Store token
    token_storage.store_token(user_email, test_token)
    print(f"✅ Token stored for {user_email}")
    
    # Retrieve token
    stored_token = token_storage.get_token(user_email)
    print(f"Retrieved token: {stored_token}")
    
    # Check validity
    is_valid = token_storage.is_token_valid(user_email)
    print(f"Token valid: {is_valid}")
    
    return stored_token is not None

if __name__ == "__main__":
    print("🚀 Starting manual tests...")
    
    # Test token storage first (doesn't require server)
    if test_token_storage():
        print("✅ Token storage works")
    else:
        print("❌ Token storage failed")
    
    print("\n" + "="*50)
    print("Server-dependent tests (requires server running):")
    print("Run: uv run python run.py")
    print("="*50)
    
    try:
        # Test endpoints that don't require real tokens
        test_health()
        test_add_user_no_token()
        test_add_user_invalid_token()
        test_get_emails_no_token()
        
        print("\n✅ Basic functionality tests completed")
        print("\nTo test with real Gmail tokens:")
        print("1. Get OAuth2 token from Gmail")
        print("2. curl -X POST localhost:5001/api/add_user -H 'Content-Type: application/json' -d '{\"access_token\":\"YOUR_TOKEN\"}'")
        print("3. curl 'localhost:5001/api/emails?user_email=YOUR_EMAIL'")
        
    except requests.exceptions.ConnectionError:
        print("❌ Server not running. Start with: uv run python run.py")