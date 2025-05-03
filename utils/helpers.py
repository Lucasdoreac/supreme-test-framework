import os
import json
import time
import logging
import requests
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import WebDriverException, TimeoutException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def take_screenshot(driver: WebDriver, name: str = None) -> str:
    """
    Take a screenshot and save it to a file
    
    Args:
        driver: WebDriver instance
        name: Optional name for screenshot (default: timestamp)
        
    Returns:
        Path to the saved screenshot file
    """
    # Create screenshots directory if it doesn't exist
    screenshots_dir = os.path.join(os.getcwd(), 'screenshots')
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)
    
    # Generate filename
    if name is None:
        name = datetime.now().strftime("%Y%m%d_%H%M%S")
    else:
        # Replace spaces and special characters
        name = name.replace(' ', '_').replace('/', '_').replace('\\', '_')
    
    filename = f"{name}.png"
    filepath = os.path.join(screenshots_dir, filename)
    
    # Take screenshot
    try:
        driver.save_screenshot(filepath)
        logger.info(f"Screenshot saved: {filepath}")
        return filepath
    except WebDriverException as e:
        logger.error(f"Failed to take screenshot: {str(e)}")
        return ""


def get_browser_logs(driver: WebDriver) -> list:
    """
    Get and format browser console logs
    
    Args:
        driver: WebDriver instance
        
    Returns:
        List of formatted log entries
    """
    try:
        logs = driver.get_log('browser')
        return [f"{log['level']}: {log['message']}" for log in logs]
    except Exception as e:
        logger.error(f"Failed to get browser logs: {str(e)}")
        return []


def get_magic_link(email: str) -> Optional[str]:
    """
    Get magic link from API for the given email
    
    Args:
        email: User email address
        
    Returns:
        Magic link URL if successful, None otherwise
    """
    api_url = f"{os.getenv('API_URL', 'http://localhost:5000')}/auth/send-link"
    
    try:
        response = requests.post(
            api_url, 
            json={"email": email},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            magic_link = data.get("magic_link")
            logger.info(f"Received magic link for {email}")
            return magic_link
        else:
            logger.error(f"Failed to get magic link: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting magic link: {str(e)}")
        return None


def validate_email(email: str) -> bool:
    """
    Validate that the email ends with @udf.edu.br
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    return email.lower().endswith('@udf.edu.br')


def wait_for_page_load(driver: WebDriver, timeout: int = 30) -> bool:
    """
    Wait for page to complete loading
    
    Args:
        driver: WebDriver instance
        timeout: Maximum wait time in seconds
        
    Returns:
        True if page loaded successfully, False on timeout
    """
    try:
        # Wait for the page's ready state to be 'complete'
        start_time = time.time()
        while time.time() - start_time < timeout:
            ready_state = driver.execute_script("return document.readyState")
            if ready_state == "complete":
                return True
            time.sleep(0.5)
        
        # Timeout reached
        logger.warning(f"Page load timeout after {timeout} seconds")
        return False
        
    except Exception as e:
        logger.error(f"Error waiting for page load: {str(e)}")
        return False


def extract_hash_from_link(link: str) -> Optional[str]:
    """
    Extract the hash part from a magic link URL
    
    Args:
        link: Magic link URL
        
    Returns:
        Hash string if found, None otherwise
    """
    if not link:
        return None
        
    try:
        # Example: http://localhost:3000/auth/callback?email=user@udf.edu.br&hash=207e2c0ebb353608f1b28cee2176e7d981f98d4df8b77e9826a84614101402f7
        parts = link.split('hash=')
        if len(parts) > 1:
            # Return the hash part (may need to strip additional URL params)
            hash_value = parts[1].split('&')[0] if '&' in parts[1] else parts[1]
            return hash_value
        return None
    except Exception as e:
        logger.error(f"Error extracting hash from link: {str(e)}")
        return None