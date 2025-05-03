from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import json
import logging
import time

from page_objects.login_page import LoginPage
from utils.helpers import get_magic_link, extract_hash_from_link

# Configure logging
logger = logging.getLogger(__name__)


@given('que estou na página de login')
def step_impl_access_login_page(context):
    """Access the login page."""
    base_url = context.config.userdata.get('BASE_URL', 'localhost:3000')
    # Ensure URL has http/https prefix
    if not base_url.startswith(('http://', 'https://')):
        base_url = f'http://{base_url}'
    
    login_url = f"{base_url}/organizer"
    context.driver.get(login_url)
    
    # Create a login page object and store it in context
    context.login_page = LoginPage(context.driver)


@when('insiro "{email}" no campo de email')
def step_impl_enter_email(context, email):
    """Enter the provided email in the email field."""
    context.email = email  # Store for later use
    context.login_page.enter_email(email)


@when('clico no botão "{button_text}"')
def step_impl_click_button(context, button_text):
    """Click the button with the specified text and capture network response if needed."""
    if button_text.lower() == "próximo":
        # Enable network interception using CDP before clicking
        if context.scenario_name == "Login bem-sucedido com magic link":
            # Setup CDP listener for network responses
            context.driver.execute_cdp_cmd('Network.enable', {})
            
            # Create a list to store the captured request IDs
            if not hasattr(context, 'captured_request_ids'):
                context.captured_request_ids = []
            
            # Set up a listener for network events using JavaScript
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
            
            # Click the next button
            context.login_page.click_next()
            
            # Wait briefly for the API request to complete and get the magic link
            max_wait = 10  # seconds
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                magic_link = context.driver.execute_script("return window.__magicLink;")
                if magic_link:
                    context.magic_link = magic_link
                    logger.info(f"Successfully intercepted magic link via CDP")
                    break
                time.sleep(0.5)
        else:
            # Click the next button without interception
            context.login_page.click_next()
    else:
        # Generic button click by text if needed
        button_locator = (By.XPATH, f"//button[contains(text(), '{button_text}')]")
        context.login_page.click_element(button_locator)


@when('recebo o magic link da API')
def step_impl_get_magic_link(context):
    """Get the magic link from the API for the current email."""
    # Check if we already intercepted the magic link via CDP
    if hasattr(context, 'magic_link') and context.magic_link:
        logger.info("Using intercepted magic link from CDP")
        magic_link = context.magic_link
    else:
        # Fallback to the original implementation
        email = getattr(context, 'email', None)
        if not email:
            raise ValueError("Email not found in context. Make sure the email step runs first.")
        
        # Get magic link from API
        logger.info("No intercepted magic link found, fetching via API call")
        magic_link = get_magic_link(email)
        if not magic_link:
            raise RuntimeError("Failed to get magic link from API")
        
        # Store the magic link for later use
        context.magic_link = magic_link
    
    # Extract and store the hash for token verification
    context.hash = extract_hash_from_link(magic_link)
    logger.info(f"Magic link obtained, hash: {context.hash}")


@when('acesso o magic link')
def step_impl_access_magic_link(context):
    """Navigate to the magic link received in a new tab."""
    magic_link = getattr(context, 'magic_link', None)
    if not magic_link:
        raise ValueError("Magic link not found in context. Make sure the API step runs first.")
    
    # Store the email for later verification
    email = getattr(context, 'email', '')
    
    # Navigate to the magic link in a new tab
    context.login_page.open_magic_link(magic_link)
    
    # Wait for token to be stored in localStorage and verify it contains the expected hash
    hash_value = getattr(context, 'hash', None)
    token = context.login_page.verify_token_in_local_storage(expected_hash=hash_value)
    
    # Verify the token exists and contains the hash
    assert token is not None, "Token not found in localStorage"
    if hash_value:
        assert hash_value in token, f"Token doesn't contain expected hash: {hash_value}"
    
    # Verify the heading is "Meus Eventos"
    assert context.login_page.verify_dashboard_heading(), "Dashboard heading 'Meus Eventos' not found"
    
    # Close the tab and return to the original login page
    context.login_page.close_tab_and_return_to_original()
    
    # Verify user's email is displayed on the original page
    assert context.login_page.verify_user_email_displayed(email), f"User email {email} not displayed on login page"
    
    # Click the dashboard button
    context.login_page.click_dashboard_button()


@then('devo ver o token salvo no localStorage')
def step_impl_verify_token(context):
    """Verify that the authentication token is saved in localStorage."""
    # This step is kept for backward compatibility, but the verification is now done in the previous step
    pass


@then('devo ser redirecionado para o dashboard')
def step_impl_verify_redirect(context):
    """Verify that the user is redirected to the dashboard and the 'Meus Eventos' heading is present."""
    # Verify we're on the dashboard URL
    is_redirected = context.login_page.is_redirected_to_dashboard()
    assert is_redirected, "Not redirected to dashboard after authentication"
    
    # Verify the heading is still "Meus Eventos" after clicking the button in the previous step
    assert context.login_page.verify_dashboard_heading(), "Dashboard heading 'Meus Eventos' not found after redirection"


@then('devo ver uma mensagem de erro indicando o domínio obrigatório')
def step_impl_verify_error_message(context):
    """Verify that an error message about required domain is displayed."""
    error_message_locator = (By.XPATH, "/html/body/div/div/section/div/div/div/div/div/div[2]/div/div/span")
    is_error_displayed = context.login_page.is_element_visible(error_message_locator)
    
    assert is_error_displayed, "O campo e-mail está fora do formato permitido."
    
    # Optionally verify error message text contains the required domain
    # error_text = context.login_page.get_text(error_message_locator)
    # assert "@udf.edu.br" in error_text, f"Error message doesn't mention the required domain: {error_text}"