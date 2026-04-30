import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_TIMEOUT = 30

# Device Configuration
DEVICE_IP = os.getenv("DEVICE_IP", "192.168.1.100")
DEVICE_USERNAME = os.getenv("DEVICE_USERNAME", "admin")
DEVICE_PASSWORD = os.getenv("DEVICE_PASSWORD", "1234")
DEVICE_TIMEOUT = int(os.getenv("DEVICE_TIMEOUT", 5))

# API Configuration
USE_MOCK = os.getenv("USE_MOCK", "True").lower() == "true"

# Logging and Debug
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

# Validation
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 30))


def validate_config():
    """Validate critical configuration"""
    if not OPENAI_API_KEY and not USE_MOCK:
        raise ValueError("OPENAI_API_KEY is required when USE_MOCK is False")
    if not DEVICE_IP:
        raise ValueError("DEVICE_IP is required")