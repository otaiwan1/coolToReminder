import json
import os
import msal
from src import config
from src.logger import logger

def _build_msal_app(cache=None):
    return msal.PublicClientApplication(
        config.CLIENT_ID,
        authority=config.AUTHORITY,
        token_cache=cache
    )

def _load_cache():
    cache = msal.SerializableTokenCache()
    if os.path.exists(config.TOKEN_CACHE_FILE):
        with open(config.TOKEN_CACHE_FILE, "r") as f:
            cache.deserialize(f.read())
    return cache

def _save_cache(cache):
    if cache.has_state_changed:
        with open(config.TOKEN_CACHE_FILE, "w") as f:
            f.write(cache.serialize())

def get_access_token():
    """Get access token, prompting device code flow if necessary."""
    if not config.CLIENT_ID or not config.TENANT_ID:
        raise ValueError("AZURE_CLIENT_ID or AZURE_TENANT_ID is not configured in .env")

    cache = _load_cache()
    app = _build_msal_app(cache)
    
    result = None
    
    # Attempt to find a token in cache
    accounts = app.get_accounts()
    if accounts:
        # Assuming single user scenario
        result = app.acquire_token_silent(config.SCOPES, account=accounts[0])

    if not result:
        logger.info("No cached token found. Initiating device code flow...")
        flow = app.initiate_device_flow(scopes=config.SCOPES)
        if "user_code" not in flow:
            raise ValueError(f"Fail to create device flow. Err: {json.dumps(flow, indent=4)}")

        logger.info(flow.get("message"))
        
        # Block and wait for user authentication in browser
        result = app.acquire_token_by_device_flow(flow)

    if "access_token" in result:
        _save_cache(cache)
        return result["access_token"]
    else:
        raise RuntimeError(f"Could not authenticate. {result.get('error')}: {result.get('error_description')}")
