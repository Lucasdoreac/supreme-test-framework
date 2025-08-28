import os
import logging
from dotenv import load_dotenv
from utils.browser_setup import setup_webdriver
from utils.helpers import take_screenshot, get_browser_logs
from utils.auth_helpers import ensure_authenticated

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def before_all(context):
    """Run before all tests."""
    # Access userdata passed via command line or from behave.ini
    context.config.setup_logging()
    
    # Set default values if not already set in userdata
    if 'BASE_URL' not in context.config.userdata:
        context.config.userdata['BASE_URL'] = os.getenv('BASE_URL', 'localhost:3000')
    
    if 'API_URL' not in context.config.userdata:
        context.config.userdata['API_URL'] = os.getenv('API_URL', 'http://localhost:5000')


def before_feature(context, feature):
    """Run before each feature."""
    logger.info(f"Starting feature: {feature.name}")


def before_scenario(context, scenario):
    """Run before each scenario."""
    logger.info(f"Starting scenario: {scenario.name}")
    
    # Create a download directory if needed for this scenario
    download_dir = os.path.join(os.getcwd(), 'downloads', scenario.name.replace(' ', '_'))
    
    # Initialize WebDriver
    context.driver = setup_webdriver(download_dir)
    
    # Store the scenario name for later use
    context.scenario_name = scenario.name
    
    # Check if scenario requires authentication
    requires_auth = any(tag in ['auth', 'event', 'authenticated'] for tag in scenario.tags)
    
    # Perform authentication if needed
    if requires_auth:
        logger.info("Scenario requires authentication, ensuring user is logged in...")
        ensure_authenticated(context)

    # if 'requires_login' in scenario.tags:
    #     # Realizar o login
    #     perform_login(context)


def after_scenario(context, scenario):
    """Run after each scenario."""
    # Capture browser logs
    logs = get_browser_logs(context.driver)
    if logs:
        for log in logs:
            logger.info(f"Browser log: {log}")
    
    # Take screenshot on failure
    if scenario.status == "failed":
        take_screenshot(context.driver, f"FAILED_{scenario.name}")
    
    # Clean up
    if hasattr(context, 'driver') and context.driver:
        # Clear localStorage if we're testing auth
        if 'auth' in scenario.tags or 'login' in scenario.tags:
            try:
                context.driver.execute_script("window.localStorage.clear();")
            except:
                pass
        
        # Quit the driver
        context.driver.quit()
        del context.driver


def after_feature(context, feature):
    """Run after each feature."""
    logger.info(f"Completed feature: {feature.name}")


def after_all(context):
    """Run after all tests."""
    logger.info("Test run completed")