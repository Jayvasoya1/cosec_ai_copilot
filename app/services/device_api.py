import requests
from app.config import DEVICE_IP, DEVICE_USERNAME, DEVICE_PASSWORD

def call_device_api(url):
    full_url = f"http://{DEVICE_IP}{url}"

    try:
        res = requests.get(
            full_url,
            auth=(DEVICE_USERNAME, DEVICE_PASSWORD),
            timeout=5
        )
        return res.text
    except Exception as e:
        return f"API Error: {str(e)}"