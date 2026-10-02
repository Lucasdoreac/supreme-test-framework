from typing import Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base_page import BasePage


class LoginPage(BasePage):
    """Page object for the login page"""
    
    def __init__(self, driver: WebDriver):
        """
        Initialize the LoginPage with locators
        
        Args:
            driver: WebDriver instance for browser interaction
        """
        super().__init__(driver)
        
        # Locators
        self.email_input = (By.NAME, "email")
        self.submit_button = (By.CSS_SELECTOR, "button[type='submit']")
        self.email_error = (By.CSS_SELECTOR, ".error-message")
        self.loading_indicator = (By.CSS_SELECTOR, ".loading-spinner")
    
    def enter_email(self, email: str) -> None:
        """
        Enter email address in the login form
        
        Args:
            email: Email address to enter
        """
        self.enter_text(self.email_input, email)
    
    def click_next(self) -> None:
        """Click the Next/Submit button on the login form"""
        self.click_element(self.submit_button)
        
        # Wait for loading indicator to disappear if present
        try:
            WebDriverWait(self.driver, 5).until_not(
                EC.visibility_of_element_located(self.loading_indicator)
            )
        except TimeoutException:
            # Continue if loading indicator isn't found
            pass
    
    def verify_email_validation(self) -> bool:
        """
        Verify that email validation rule (ending with @udf.edu.br) is enforced
        
        Returns:
            True if validation is working, False otherwise
        """
        # Try with invalid email
        self.enter_email("test@example.com")
        self.click_next()
        
        # Check if error message is displayed
        return self.is_element_visible(self.email_error)
    
    def login_with_email(self, email: str) -> None:
        """
        Perform login by entering email and clicking next
        
        Args:
            email: Email address to use for login
        """
        self.enter_email(email)
        self.click_next()
    
    def open_magic_link(self, link: str) -> None:
        """
        Open the magic link received for authentication in a new tab
        
        Args:
            link: The magic link URL to navigate to
        """
        # Store current window handle
        self.original_window = self.driver.current_window_handle
        
        # Open a new tab with JavaScript
        self.driver.execute_script("window.open();")
        
        # Switch to the new tab (it will be the last window handle)
        self.driver.switch_to.window(self.driver.window_handles[-1])
        
        # Navigate to the magic link in the new tab
        self.navigate_to(link)
    
    def wait_for_session_token(self, max_wait: int = 10) -> Optional[str]:
        """Wait until the app stores a session token and return it.

        The e-mailed link is single use: the app trades it for a session token,
        so the stored token is a different value than the link's hash.
        """
        import time
        deadline = time.time() + max_wait
        while time.time() < deadline:
            token = self.get_local_storage_item("token")
            if token:
                return token
            time.sleep(0.5)
        return self.get_local_storage_item("token") or None

    def verify_token_in_local_storage(self, expected_hash: Optional[str] = None, 
                                   max_wait: int = 10) -> Optional[str]:
        """
        Verify that authentication token is present in localStorage and optionally wait
        until it matches an expected hash value
        
        Args:
            expected_hash: The expected hash that should be part of the token
            max_wait: Maximum time to wait in seconds for the token to match
            
        Returns:
            Token value if found, None otherwise
        """
        if expected_hash:
            import time
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                token = self.get_local_storage_item("token")
                if token and expected_hash in token:
                    return token
                time.sleep(0.5)
                
            # One final check
            token = self.get_local_storage_item("token")
            return token if token and expected_hash in token else None
        else:
            # Just check once without waiting
            return self.get_local_storage_item("token")
    
    def is_redirected_to_events_page(self) -> bool:
        """
        Check if user is redirected to events page after login
        
        Returns:
            True if on events page, False otherwise
        """
        # Wait for redirect to events page
        return self.wait_until_url_contains("/event/mine", 10)
        
    def verify_events_heading(self) -> bool:
        """
        Verify that the events page heading shows "Meus Eventos"
        
        Returns:
            True if heading matches, False otherwise
        """
        heading_locator = (By.XPATH, "//h2[normalize-space(.)='Meus Eventos']")
        
        try:
            heading = self.get_text(heading_locator)
            return heading == "Meus Eventos"
        except (TimeoutException, NoSuchElementException):
            return False
            
    def close_tab_and_return_to_original(self) -> None:
        """
        Close the current tab and return to the original window
        """
        # Close the current tab
        self.driver.close()
        
        # Switch back to the original window
        self.driver.switch_to.window(self.original_window)
        
    def verify_user_email_displayed(self, expected_email: str) -> bool:
        """
        Verify that user's email is displayed on the page
        
        Args:
            expected_email: The email that should be displayed
            
        Returns:
            True if email is displayed, False otherwise
        """
        try:
            paragraphs = self.driver.find_elements(By.TAG_NAME, "p")
            if any(expected_email in paragraph.text for paragraph in paragraphs):
                return True
            return any(
                element.get_attribute("value") == expected_email
                for element in self.driver.find_elements(*self.email_input)
            )
        except (TimeoutException, NoSuchElementException):
            return False
            
    def click_events_button(self) -> None:
        """
        Click the button on the events page
        """
        button_locator = (By.XPATH, "//button[normalize-space(.)='Já Confirmei!']")
        self.click_element(button_locator)
