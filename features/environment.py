import os
import logging
from dotenv import load_dotenv
from utils.browser_setup import setup_webdriver
from utils.helpers import take_screenshot, get_browser_logs

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


def after_scenario(context, scenario):
    """Run after each scenario.

    Every cleanup step runs on its own: a failure is logged by class and the next step still runs, so a
    broken seed cleanup cannot leave the browser open. If any step failed the scenario ends in error.
    """
    failures = []

    def step(name, action):
        try:
            action()
        except Exception as error:  # keep cleaning; reported below
            failures.append(name)
            logger.error("Cleanup step '%s' failed: %s", name, type(error).__name__)

    def remove_seeded():
        # Remove only what this scenario seeded, by id (see utils/seed.py).
        seeded = getattr(context, "seeded_event_ids", [])
        if seeded:
            from utils.seed import delete_events
            logger.info(f"Removed {delete_events(seeded)} seeded event(s)")
            context.seeded_event_ids = []

    def remove_created():
        # Events the scenario created through the UI (drafts, submitted requests): everything the
        # isolated account owns now that it did not own when the scenario recorded its baseline.
        baseline = getattr(context, "event_baseline", None)
        if baseline is not None:
            from utils.seed import account_events, delete_events
            created = [i for i in account_events(context.email) if i not in baseline]
            logger.info(f"Removed {delete_events(created)} event(s) created by the scenario")
            context.event_baseline = None

    def restart_services():
        # A scenario that stopped the API or the Auth must never leave them down for the next one.
        for service in list(getattr(context, "stopped_services", [])):
            from utils import service_control
            service_control.restart(service, context.config.userdata['API_URL'])
            context.stopped_services.remove(service)

    def browser_logs():
        for log in get_browser_logs(context.driver) or []:
            logger.info(f"Browser log: {log}")

    def failure_screenshot():
        if scenario.status == "failed":
            take_screenshot(context.driver, f"FAILED_{scenario.name}")

    def clear_storage():
        # Clear localStorage if we're testing auth
        if 'auth' in scenario.tags or 'login' in scenario.tags:
            context.driver.execute_script("window.localStorage.clear();")

    def quit_driver():
        driver = context.driver
        del context.driver
        driver.quit()

    step("restart stopped services", restart_services)
    step("remove seeded events", remove_seeded)
    step("remove created events", remove_created)
    if getattr(context, 'driver', None):
        step("browser logs", browser_logs)
        step("failure screenshot", failure_screenshot)
        step("clear storage", clear_storage)
        step("quit driver", quit_driver)

    if failures:
        raise RuntimeError(f"cleanup failed in: {', '.join(failures)}")


def after_feature(context, feature):
    """Run after each feature."""
    logger.info(f"Completed feature: {feature.name}")


def after_all(context):
    """Run after all tests."""
    logger.info("Test run completed")