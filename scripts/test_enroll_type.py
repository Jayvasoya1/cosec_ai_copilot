import sys
sys.path.insert(0, r'E:\matbot\cosec_ai_copilot')
from app.services import api_builder
import app.services.device_api as device_api
# Monkeypatch api_builder's call_device_api reference to avoid external network calls
orig_api_call = api_builder.call_device_api if hasattr(api_builder, 'call_device_api') else None
api_builder.call_device_api = lambda *a, **k: {'status_code':200,'data':{}}

params = {'action':'enroll','pdid':'1','user-id':'1','type':'7'}
try:
    url = api_builder.build_url('enrolluser', params)
    print('Built URL:', url)
finally:
    if orig_api_call is not None:
        api_builder.call_device_api = orig_api_call
