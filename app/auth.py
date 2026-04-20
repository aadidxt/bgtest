import os
from dotenv import load_dotenv

load_dotenv()

# API keys are loaded from environment variables
# Format: API_KEYS_KEY1=key_value, API_KEYS_KEY2=key_value, etc.
# Example in .env: API_KEYS_PRIMARY=bg-xxxxx
def get_api_keys():
    keys = {}
    api_keys_env = os.getenv("API_KEYS", "")
    
    if api_keys_env:
        # Parse comma-separated API keys
        for key in api_keys_env.split(","):
            key = key.strip()
            if key:
                keys[key] = {"label": "api_key", "created_at": "2026-04-17"}
    
    return keys

API_KEYS = get_api_keys()

def validate_api_key(api_key):
    return api_key in API_KEYS
