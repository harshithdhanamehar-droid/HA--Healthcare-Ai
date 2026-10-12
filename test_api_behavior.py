#!/usr/bin/env python3
"""
Test actual API behavior end-to-end
Verify request/response contract
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)

print("=" * 80)
print("API BEHAVIOR VERIFICATION")
print("=" * 80)
print()

# Test 1: NON_HEALTH response format
print("TEST 1: Non-health query response format")
print("-" * 80)

response = client.post("/chat", json={
    "message": "What is the weather?",
    "username": "TestUser",
    "user_phone": "9999999999",
    "chat_id": "test_nonhealth"
})

print("Request:")
print('  POST /chat')
print('  {"message": "What is the weather?", ...}')
print()

print("Response Status:", response.status_code)
data = response.json()

print("Response Body:")
print(json.dumps(data, indent=2))
print()

# Verify format
checks = [
    ("status_code == 200", response.status_code == 200),
    ("has 'response' key", "response" in data),
    ("has 'classification' key", "classification" in data),
    ("has 'timestamp' key", "timestamp" in data),
    ("response is None", data.get("response") is None),
    ("classification is 'NON_HEALTH'", data.get("classification") == "NON_HEALTH"),
]

for check_name, result in checks:
    status = "OK" if result else "FAIL"
    print("{}: {}".format(status, check_name))

print()

# Test 2: HEALTH response format (if Groq key available)
print("TEST 2: Health query response format")
print("-" * 80)

groq_key = os.getenv('GROQ_API_KEY', '').strip()

if groq_key:
    response = client.post("/chat", json={
        "message": "What are symptoms of diabetes?",
        "username": "TestUser",
        "user_phone": "9999999999",
        "chat_id": "test_health"
    })
    
    print("Request:")
    print('  POST /chat')
    print('  {"message": "What are symptoms of diabetes?", ...}')
    print()
    
    print("Response Status:", response.status_code)
    data = response.json()
    
    print("Response Body (truncated):")
    if data.get("response"):
        preview = data["response"][:150] + "..." if len(data["response"]) > 150 else data["response"]
        print('  "response": "{}"'.format(preview))
    print('  "classification": "{}"'.format(data.get("classification")))
    print('  "timestamp": "{}"'.format(data.get("timestamp")))
    print()
    
    checks = [
        ("status_code == 200", response.status_code == 200),
        ("has 'response' key", "response" in data),
        ("response not None", data.get("response") is not None),
        ("response has content", len(data.get("response", "")) > 10),
        ("classification is 'HEALTH'", data.get("classification") == "HEALTH"),
    ]
    
    for check_name, result in checks:
        status = "OK" if result else "FAIL"
        print("{}: {}".format(status, check_name))
else:
    print("SKIP: GROQ_API_KEY not configured")
    print("Cannot test live AI response without API key")

print()

# Test 3: Google status endpoint
print("TEST 3: Google OAuth status endpoint")
print("-" * 80)

response = client.get("/auth/google/status")
print("Request:")
print('  GET /auth/google/status')
print()

print("Response Status:", response.status_code)
data = response.json()

print("Response Body:")
print(json.dumps(data, indent=2))
print()

checks = [
    ("status_code == 200", response.status_code == 200),
    ("has 'configured' key", "configured" in data),
    ("has 'client_id' key", "client_id" in data),
]

for check_name, result in checks:
    status = "OK" if result else "FAIL"
    print("{}: {}".format(status, check_name))

if data.get("configured"):
    print()
    print("INFO: Google OAuth IS configured")
    print("  Client ID (first 30 chars): {}...".format(data["client_id"][:30]))
else:
    print()
    print("INFO: Google OAuth NOT configured (expected in local dev)")
    print("  Set GOOGLE_CLIENT_ID environment variable to enable")

print()

# Test 4: Multiple validations in a row
print("TEST 4: Multiple queries in sequence")
print("-" * 80)

test_queries = [
    ("I have a headache", "HEALTH"),
    ("Tell me more", "HEALTH"),
    ("What is the capital of France", "NON_HEALTH"),
    ("I have tinnitus", "HEALTH"),
]

print("Sending {} queries...".format(len(test_queries)))
print()

all_correct = True

for message, expected_classification in test_queries:
    response = client.post("/chat", json={
        "message": message,
        "username": "TestUser",
        "user_phone": "9999999999",
        "chat_id": "test_seq_{}".format(hash(message) % 10000)
    })
    
    data = response.json()
    actual_classification = data.get("classification")
    
    is_correct = actual_classification == expected_classification
    status = "OK" if is_correct else "FAIL"
    
    print("{}: Query='{}', Expected={}, Got={}".format(
        status, message, expected_classification, actual_classification
    ))
    
    if not is_correct:
        all_correct = False

print()

if all_correct:
    print("RESULT: All queries classified correctly")
else:
    print("RESULT: Some queries misclassified")

print()
print("=" * 80)
