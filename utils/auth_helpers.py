import logging
import time
from page_objects.login_page import LoginPage
from utils.helpers import get_magic_link, extract_hash_from_link

# Configure logging
logger = logging.getLogger(__name__)


def perform_login(context, email="danrley.pereira@udf.edu.br"):
    """
    Perform complete authentication with magic link
    
    Args:
        context: Behave context object
        email: Email to use for authentication (default: test email)
    """
    try:
        # Get base URL
        base_url = context.config.userdata.get('BASE_URL', 'localhost:3000')
        if not base_url.startswith(('http://', 'https://')):
            base_url = f'http://{base_url}'
        
        # Navigate to login page
        login_url = f"{base_url}/organizer"
        context.driver.get(login_url)
        
        # Create login page object
        login_page = LoginPage(context.driver)
        
        # Setup CDP listener for network responses (similar to login_steps.py)
        context.driver.execute_cdp_cmd('Network.enable', {})
        
        # Set up JavaScript to intercept magic link
        script = """
        // Function to be called when magic link is received
        window.__magicLinkReceived = function(link) {
            window.__magicLink = link;
            console.log("Magic link received: " + link);
        };
        
        // Create listeners for network activity
        if (!window.__interceptInitialized) {
            window.__interceptInitialized = true;
            
            // Save original fetch function
            const originalFetch = window.fetch;
            
            // Override fetch
            window.fetch = async function(url, options) {
                // Call original fetch
                const response = await originalFetch(url, options);
                
                // Check if this is the magic link endpoint
                if (url.includes('/auth/send-link')) {
                    // Clone the response so we can read the body
                    const clonedResponse = response.clone();
                    
                    try {
                        // Get the JSON data
                        const jsonData = await clonedResponse.json();
                        
                        // If it has a magic_link field, save it
                        if (jsonData && jsonData.magic_link) {
                            window.__magicLinkReceived(jsonData.magic_link);
                        }
                    } catch (e) {
                        console.error("Error intercepting response:", e);
                    }
                }
                
                // Return the original response
                return response;
            };
            
            // Handle XMLHttpRequest as well
            const originalXHROpen = XMLHttpRequest.prototype.open;
            const originalXHRSend = XMLHttpRequest.prototype.send;
            
            XMLHttpRequest.prototype.open = function(method, url, ...rest) {
                this.__url = url;
                return originalXHROpen.apply(this, [method, url, ...rest]);
            };
            
            XMLHttpRequest.prototype.send = function(data) {
                if (this.__url && this.__url.includes('/auth/send-link')) {
                    const originalOnLoad = this.onload;
                    
                    this.onload = function(e) {
                        try {
                            const jsonData = JSON.parse(this.responseText);
                            if (jsonData && jsonData.magic_link) {
                                window.__magicLinkReceived(jsonData.magic_link);
                            }
                        } catch (e) {
                            console.error("Error intercepting XHR response:", e);
                        }
                        
                        if (originalOnLoad) {
                            originalOnLoad.apply(this, [e]);
                        }
                    };
                }
                
                return originalXHRSend.apply(this, [data]);
            };
            
            console.log("Network interception initialized");
        }
        """
        context.driver.execute_script(script)
        
        # Perform login steps
        login_page.enter_email(email)
        login_page.click_next()
        
        # Wait for the API request to complete and get the magic link
        max_wait = 10  # seconds
        start_time = time.time()
        magic_link = None
        
        while time.time() - start_time < max_wait:
            magic_link = context.driver.execute_script("return window.__magicLink;")
            if magic_link:
                logger.info(f"Successfully intercepted magic link via CDP")
                break
            time.sleep(0.5)
        
        if not magic_link:
            logger.warning("Failed to intercept magic link via CDP, trying API fallback")
            magic_link = get_magic_link(email)
        
        if not magic_link:
            raise RuntimeError("Failed to get magic link for authentication")
        
        # Extract hash for verification
        hash_value = extract_hash_from_link(magic_link)
        
        # Navigate to magic link to complete authentication
        login_page.open_magic_link(magic_link)
        
        # Wait for token to be stored and verify authentication
        token = login_page.verify_token_in_local_storage(expected_hash=hash_value)
        if not token:
            raise RuntimeError("Authentication token not found in localStorage")
        
        # Verify we reached the events page
        if not login_page.verify_events_heading():
            raise RuntimeError("Did not reach events page after authentication")
        
        # Close the magic link tab and return to original
        login_page.close_tab_and_return_to_original()
        
        # Click events button to complete the flow
        login_page.click_events_button()
        
        # Final verification - should be on /event/mine
        login_page.wait_until_url_contains("/event", 15)
        
        logger.info(f"Complete authentication successful for {email}")
        
        # Store authentication state
        context.authenticated = True
        context.authenticated_email = email
        
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        context.authenticated = False
        raise


def is_already_authenticated(context):
    """
    Check if user is already authenticated
    
    Args:
        context: Behave context object
        
    Returns:
        True if already authenticated, False otherwise
    """
    try:
        # Check if we have authentication state
        if not hasattr(context, 'authenticated') or not context.authenticated:
            return False
        
        # Check current URL to verify we're still authenticated
        current_url = context.driver.current_url
        
        # If we're on login page, we're not authenticated
        if "/organizer" in current_url and "/event" not in current_url:
            return False
        
        # If we're on events page or similar, we're likely authenticated
        if "/event" in current_url:
            return True
        
        return False
        
    except Exception:
        return False


def ensure_authenticated(context, email="danrley.pereira@udf.edu.br"):
    """
    Ensure user is authenticated, performing login if needed
    
    Args:
        context: Behave context object
        email: Email to use for authentication if login is needed
    """
    if not is_already_authenticated(context):
        logger.info("User not authenticated, performing login...")
        perform_login(context, email)
    else:
        logger.info("User already authenticated, skipping login")
