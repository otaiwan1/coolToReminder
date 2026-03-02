import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Azure Settings
CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
TENANT_ID = os.getenv("AZURE_TENANT_ID", "common").strip()

# If the app is registered for Personal Microsoft accounts only, it must use the /consumers endpoint
if TENANT_ID.lower() in ["", "common", "consumers"]:
    AUTHORITY = "https://login.microsoftonline.com/consumers"
else:
    AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
    
SCOPES = ["Tasks.ReadWrite"]
TOKEN_CACHE_FILE = ".token_cache.json"

# NTU Cool Settings
ICAL_FEED_URL = os.getenv("ICAL_FEED_URL")

# Preferences
TODO_LIST_NAME = os.getenv("TODO_LIST_NAME", "NTU Cool 作業")
REMINDER_MINUTES_BEFORE = int(os.getenv("REMINDER_MINUTES_BEFORE", "60"))
SYNC_INTERVAL_MINUTES = int(os.getenv("SYNC_INTERVAL_MINUTES", "60"))

# Sync State
SYNC_STATE_FILE = "sync_state.json"
