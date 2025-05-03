import os
import logging
from typing import Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_browser_capabilities() -> Dict[str, Any]:
    """
    Get browser capabilities based on environment settings
    
    Returns:
        Dictionary of browser capabilities
    """
    env = os.getenv('ENV', 'development')
    
    # Basic capabilities for all environments
    capabilities = {
        'browserName': 'chrome',
        'pageLoadStrategy': 'normal',
        'acceptInsecureCerts': True,
    }
    
    # Add environment-specific capabilities
    if env == 'development':
        capabilities.update({
            'loggingPrefs': {'browser': 'ALL', 'performance': 'ALL'},
        })
    
    return capabilities


def setup_chrome_options() -> Options:
    """
    Configure Chrome options for WebDriver
    
    Returns:
        Configured Chrome options object
    """
    env = os.getenv('ENV', 'development')
    options = Options()
    
    # Common options
    options.add_argument('--start-maximized')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-notifications')
    options.add_argument('--disable-popup-blocking')
    
    # Performance options
    options.add_argument('--disable-gpu')  # Applicable to Windows only
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # Environment-specific options
    if env == 'development':
        # In development, don't use headless mode for debugging
        pass
    else:
        # In other environments, use headless mode
        options.add_argument('--headless')
    
    # Enable browser console logs
    options.set_capability('goog:loggingPrefs', {'browser': 'ALL', 'performance': 'ALL'})
    
    # User agent (if needed)
    user_agent = os.getenv('USER_AGENT', '')
    if user_agent:
        options.add_argument(f'--user-agent={user_agent}')
    
    return options


def setup_webdriver(download_dir: Optional[str] = None) -> webdriver.Chrome:
    """
    Initialize and configure WebDriver
    
    Args:
        download_dir: Optional directory path for downloads
        
    Returns:
        Configured WebDriver instance
    """
    options = setup_chrome_options()
    
    # Configure download directory if provided
    if download_dir:
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        
        prefs = {
            'download.default_directory': download_dir,
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'safebrowsing.enabled': False
        }
        options.add_experimental_option('prefs', prefs)
    
    # Initialize WebDriver
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        
        # Set default timeout
        page_load_timeout = int(os.getenv('PAGE_LOAD_TIMEOUT', '30'))
        implicit_wait = int(os.getenv('IMPLICIT_WAIT', '10'))
        driver.set_page_load_timeout(page_load_timeout)
        driver.implicitly_wait(implicit_wait)
        
        # Set window size if specified
        window_width = os.getenv('WINDOW_WIDTH')
        window_height = os.getenv('WINDOW_HEIGHT')
        if window_width and window_height:
            driver.set_window_size(int(window_width), int(window_height))
        else:
            driver.maximize_window()
        
        logger.info("WebDriver initialized successfully")
        return driver
        
    except Exception as e:
        logger.error(f"Failed to initialize WebDriver: {str(e)}")
        raise