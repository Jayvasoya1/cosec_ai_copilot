#!/usr/bin/env python
"""Simple test to verify device response is displayed"""

from app.graph.nodes import respond_node
import json

# Simulate a success result with device response
state = {
    'current_intent': 'add_user',
    'missing_fields': [],
    'execution_result': {
        'status': 'success',
        'url': '/device.cgi/users?action=set&user-id=101&name=John',
        'mock': False,
        'message': '✅ Command executed successfully',
        'response': '<response><status>OK</status><message>User added successfully</message></response>',
        'device_status': 200,
    }
}

result = respond_node(state)
print('Response Status:', result['response_status'])
print('Response Message:', result['response_message'])
print('Response Details:')
print(json.dumps(result['response_details'], indent=2))
