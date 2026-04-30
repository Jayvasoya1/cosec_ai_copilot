"""
Device API Client - Handles communication with COSEC devices
Executes curl commands with digest authentication
"""

import subprocess

from app.config import DEVICE_IP, DEVICE_USERNAME, DEVICE_PASSWORD, DEVICE_TIMEOUT
from app.exceptions import DeviceAPIError
from app.logger import logger


def call_device_api(url: str) -> dict:
    """
    Make API call to COSEC device using curl with digest authentication
    
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
    
    full_url = f"http:/{url}"
    logger.debug(f"Making API call to: {full_url}")
    
    # Build curl command with digest auth
    curl_cmd = [
        "curl",
        "-s",  # Silent mode - no progress or error information
        "--digest",
        "-u", f"{DEVICE_USERNAME}:{DEVICE_PASSWORD}",
        "-w", "\n%{http_code}",  # Append HTTP status code to output
        "--max-time", str(DEVICE_TIMEOUT),
        full_url
    ]
    
    logger.debug(f"Executing curl command: curl --digest -u '{DEVICE_USERNAME}:***' -w '\\n%{{http_code}}' --max-time {DEVICE_TIMEOUT} {full_url}")
    
    try:
        # Execute curl command
        result = subprocess.run(
            curl_cmd,
            capture_output=True,
            text=True,
            timeout=DEVICE_TIMEOUT + 5  # Add buffer for curl's own timeout
        )
        
        # Split output: response body and status code
        output_lines = result.stdout.strip().split('\n')
        status_code = 0
        response_body = ""
        
        try:
            if len(output_lines) >= 2:
                response_body = '\n'.join(output_lines[:-1])
                status_code = int(output_lines[-1])
            else:
                response_body = result.stdout
        except (ValueError, IndexError):
            response_body = result.stdout
        
        # If curl failed and no status code was obtained, check stderr
        if result.returncode != 0 and status_code == 0:
            logger.error(f"curl error (code {result.returncode}): {result.stderr}")
            raise DeviceAPIError(
                f"curl execution failed: {result.stderr.strip() if result.stderr else 'unknown error'}",
                full_url
            )
        
        logger.debug(f"Response status: {status_code}")
        
        # Check HTTP status
        if status_code == 401:
            logger.error("Authentication failed - invalid credentials")
            raise DeviceAPIError(
                "Authentication failed - invalid device credentials",
                full_url,
                status_code
            )
        
        if status_code == 404:
            logger.error("Device endpoint not found")
            raise DeviceAPIError(
                "Device endpoint not found",
                full_url,
                status_code
            )
        
        if status_code >= 500:
            logger.error(f"Device server error: {status_code}")
            raise DeviceAPIError(
                f"Device server error: {status_code}",
                full_url,
                status_code
            )
        
        if status_code >= 400:
            logger.error(f"Request failed: {status_code}")
            raise DeviceAPIError(
                f"Request failed: {status_code}",
                full_url,
                status_code
            )
        
        logger.info(f"API call successful: {status_code}")
        
        return {
            "success": True,
            "data": response_body,
            "url": full_url,
            "status_code": status_code
        }
        
    except subprocess.TimeoutExpired:
        logger.error(f"Device API timeout after {DEVICE_TIMEOUT}s")
        raise DeviceAPIError(
            f"Device API timeout after {DEVICE_TIMEOUT}s",
            full_url
        )
        
    except DeviceAPIError:
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error calling device API: {str(e)}")
        raise DeviceAPIError(
            f"Unexpected error: {str(e)}",
            full_url
        )