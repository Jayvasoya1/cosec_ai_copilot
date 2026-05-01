#!/usr/bin/env python3
"""Test script for enrolluser integration"""

from app.core.router import handler_registry
from app.schemas.registry import schema_registry

print("=" * 60)
print("ENROLLUser INTEGRATION TEST")
print("=" * 60)
print()

# Test 1: Set enrollment with finger count
print("Test 1: set_enroll_options with finger count")
intent = 'set_enroll_options'
params = {'finger_count': '5'}

handler = handler_registry.get_handler(intent)
result = handler(intent, params)
print(f'  Parameters (input): {params}')
print(f'  Result: {result}')
print()

# Test 2: Get enrollment options
print("Test 2: get_enroll_options")
intent = 'get_enroll_options'
params = {'id_format': 'json'}

handler = handler_registry.get_handler(intent)
result = handler(intent, params)
print(f'  Parameters (input): {params}')
print(f'  Result: {result}')
print()

# Test 3: Set default with mixed parameters
print("Test 3: set_default_enroll_options with multiple params")
intent = 'set_default_enroll_options'
params = {'mode': '1', 'finger_count': '8', 'palm_count': '2'}

handler = handler_registry.get_handler(intent)
result = handler(intent, params)
print(f'  Parameters (input): {params}')
print(f'  Result: {result}')
print()

# Test 4: Schema validation
print("Test 4: Schema field validation")
schema = schema_registry.get('enrolluser')

test_values = [
    ('enroll-finger-count', '5', True),
    ('enroll-finger-count', '15', False),  # Max is 10
    ('enroll-mode', '1', True),
    ('enroll-mode', '2', False),  # Only 0 or 1
    ('format', 'text', True),
    ('format', 'xml', True),
]

for field, value, expected in test_values:
    result = schema.validate_field_values(field, value)
    status = "" if result == expected else ""
    print(f"  {status} validate({field}={value}) = {result} (expected {expected})")

print()
print("=" * 60)
print("ALL TESTS COMPLETED")
print("=" * 60)
