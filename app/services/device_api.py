"""
Device API Client - Handles communication with COSEC devices
"""

import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import (
    Timeout, ConnectionError, RequestException
)

from app.config import DEVICE_IP, DEVICE_USERNAME, DEVICE_PASSWORD, DEVICE_TIMEOUT
from app.exceptions import DeviceAPIError
from app.logger import logger


def call_device_api(url: str) -> dict:
    """
    Make API call to COSEC device
    
    Args:
        url: Relative URL path (e.g., "/device.cgi/users?action=set&user-id=101")
        
    Returns:
        Dict with response data
        {
            "success": bool,
            "data": response_content,
            "url": full_url,
            "status_code": http_status
        }
        
    Raises:
        DeviceAPIError: If API call fails
    """
    
    full_url = f"http://{DEVICE_IP}{url}"
    
    logger.debug(f"Making API call to: {full_url}")
    
    try:
        response = requests.get(
            full_url,
            auth=HTTPBasicAuth(DEVICE_USERNAME, DEVICE_PASSWORD),
            timeout=DEVICE_TIMEOUT
        )
        
        logger.debug(f"Response status: {response.status_code}")
        
        # Check HTTP status
        if response.status_code == 401:
            logger.error("Authentication failed - invalid credentials")
            raise DeviceAPIError(
                "Authentication failed - invalid device credentials",
                full_url,
                response.status_code
            )
        
        if response.status_code == 404:
            logger.error("Device endpoint not found")
            raise DeviceAPIError(
                "Device endpoint not found",
                full_url,
                response.status_code
            )
        
        if response.status_code >= 500:
            logger.error(f"Device server error: {response.status_code}")
            raise DeviceAPIError(
                f"Device server error: {response.status_code}",
                full_url,
                response.status_code
            )
        
        if response.status_code >= 400:
            logger.error(f"Request failed: {response.status_code}")
            raise DeviceAPIError(
                f"Request failed: {response.status_code}",
                full_url,
                response.status_code
            )
        
        logger.info(f"API call successful: {response.status_code}")
        
        return {
            "success": True,
            "data": response.text,
            "url": full_url,
            "status_code": response.status_code
        }
        
    except Timeout:
        logger.error(f"Device API timeout after {DEVICE_TIMEOUT}s")
        raise DeviceAPIError(
            f"Device API timeout after {DEVICE_TIMEOUT}s",
            full_url
        )
        
    except ConnectionError:
        logger.error(f"Cannot connect to device at {DEVICE_IP}")
        raise DeviceAPIError(
            f"Cannot connect to device at {DEVICE_IP}",
            full_url
        )
        
    except RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        raise DeviceAPIError(
            f"Request failed: {str(e)}",
            full_url
        )
        
    except Exception as e:
        logger.error(f"Unexpected error calling device API: {str(e)}")
        raise DeviceAPIError(
            f"Unexpected error: {str(e)}",
            full_url
        )