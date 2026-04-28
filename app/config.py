import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

DEVICE_IP = "192.168.1.100"
DEVICE_USERNAME = "admin"
DEVICE_PASSWORD = "admin"

USE_MOCK = True   # 🔥 change to False for real device