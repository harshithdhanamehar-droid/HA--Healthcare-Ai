#!/usr/bin/env python3
"""Simple edge case test - no unicode issues"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from main import validate_health_query

# Test cases with unfamiliar medical terminology
edge_cases = [
    ("I have tinnitus", "HEALTH"),
    ("What is gastroparesis?", "HEALTH"),
    ("Do I have dermatitis?", "HEALTH"),
    ("Explain acupuncture", "HEALTH"),
    ("What is polymyalgia?", "HEALTH"),
    ("I have myalgia", "HEALTH"),
    ("What causes epistaxis?", "HEALTH"),
    ("Explain pathophysiology", "HEALTH"),
    ("What is etiology?", "HEALTH"),
    ("I have hyperglycemia", "HEALTH"),
    ("Do I need anticoagulation?", "HEALTH"),
    ("What is prophylaxis?", "HEALTH"),
]

print("=" * 70)
print("EDGE CASE TEST - UNFAMILIAR MEDICAL TERMS")
print("=" * 70)

passed = 0
failed = 0
failures = []

for query, expected in edge_cases:
    result = validate_health_query(query)
    is_pass = result == expected
    
    if is_pass:
        print("PASS: '{}' -> {}".format(query, result))
        passed += 1
    else:
        print("FAIL: '{}' -> {} (expected {})".format(query, result, expected))
        failed += 1
        failures.append((query, result, expected))

print()
print("=" * 70)
print("Results: {} passed, {} failed".format(passed, failed))
print("=" * 70)

if failures:
    print()
    print("Failed cases:")
    for query, result, expected in failures:
        print("  - '{}': got {}, expected {}".format(query, result, expected))

sys.exit(0 if failed == 0 else 1)
