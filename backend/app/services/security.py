import os
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def get_api_key(
    api_key_header: str = Security(api_key_header),
):
    """
    Validate API key from header.
    To disable auth in dev, set API_KEY=None or empty.
    """
    expected_api_key = os.getenv("API_KEY")
    
    # If no API key is configured, allow all requests (dev mode)
    if not expected_api_key:
        return None
        
    if api_key_header == expected_api_key:
        return api_key_header
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate API Key",
        )
