from typing import Tuple, Optional, Any, List
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class BasePage:
    """Base class for all page objects"""
    
    def __init__(self, driver: WebDriver):
        """
        Initialize the BasePage with a WebDriver instance
        
        Args:
            driver: WebDriver instance for browser interaction
        """
        self.driver = driver
        self.default_timeout = 10
    
    def find_element(self, locator: Tuple[str, str], timeout: int = None) -> WebElement:
        """
        Find an element on the page with explicit wait
        
        Args:
            locator: Tuple of (By, value) to locate the element
            timeout: Wait timeout in seconds (default: self.default_timeout)
            
        Returns:
            WebElement if found
            
        Raises:
            TimeoutException: If element is not found within timeout
        """
        if timeout is None:
            timeout = self.default_timeout
            
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator),
            f"Element not found with locator {locator}"
        )
    
    def find_elements(self, locator: Tuple[str, str], timeout: int = None) -> List[WebElement]:
        """
        Find multiple elements on the page with explicit wait
        
        Args:
            locator: Tuple of (By, value) to locate the elements
            timeout: Wait timeout in seconds (default: self.default_timeout)
            
        Returns:
            List of WebElements if found
            
        Raises:
            TimeoutException: If no elements are found within timeout
        """
        if timeout is None:
            timeout = self.default_timeout
            
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_all_elements_located(locator),
            f"Elements not found with locator {locator}"
        )
    
    def click_element(self, locator: Tuple[str, str], timeout: int = None) -> None:
        """
        Click on an element after ensuring it's clickable
        
        Args:
            locator: Tuple of (By, value) to locate the element
            timeout: Wait timeout in seconds (default: self.default_timeout)
            
        Raises:
            TimeoutException: If element is not clickable within timeout
        """
        if timeout is None:
            timeout = self.default_timeout
            
        element = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable(locator),
            f"Element not clickable with locator {locator}"
        )
        element.click()
    
    def enter_text(self, locator: Tuple[str, str], text: str, timeout: int = None) -> None:
        """
        Enter text into an input element
        
        Args:
            locator: Tuple of (By, value) to locate the element
            text: Text to enter
            timeout: Wait timeout in seconds (default: self.default_timeout)
            
        Raises:
            TimeoutException: If element is not found within timeout
        """
        element = self.find_element(locator, timeout)
        element.clear()
        element.send_keys(text)
    
    def get_text(self, locator: Tuple[str, str], timeout: int = None) -> str:
        """
        Get text from an element
        
        Args:
            locator: Tuple of (By, value) to locate the element
            timeout: Wait timeout in seconds (default: self.default_timeout)
            
        Returns:
            Text content of the element
            
        Raises:
            TimeoutException: If element is not found within timeout
        """
        element = self.find_element(locator, timeout)
        return element.text
    
    def is_element_visible(self, locator: Tuple[str, str], timeout: int = None) -> bool:
        """
        Check if an element is visible on the page
        
        Args:
            locator: Tuple of (By, value) to locate the element
            timeout: Wait timeout in seconds (default: self.default_timeout)
            
        Returns:
            True if element is visible, False otherwise
        """
        if timeout is None:
            timeout = self.default_timeout
            
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator),
                f"Element not visible with locator {locator}"
            )
            return True
        except TimeoutException:
            return False
    
    def wait_until_url_contains(self, text: str, timeout: int = None) -> bool:
        """
        Wait until the URL contains a specific text
        
        Args:
            text: Text to wait for in URL
            timeout: Wait timeout in seconds (default: self.default_timeout)
            
        Returns:
            True if condition is met, False otherwise
        """
        if timeout is None:
            timeout = self.default_timeout
            
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.url_contains(text),
                f"URL did not contain '{text}' within timeout"
            )
            return True
        except TimeoutException:
            return False
    
    def execute_script(self, script: str, *args) -> Any:
        """
        Execute JavaScript in the browser
        
        Args:
            script: JavaScript to execute
            args: Arguments to pass to the script
            
        Returns:
            Result of the JavaScript execution
        """
        return self.driver.execute_script(script, *args)
    
    def get_local_storage_item(self, key: str) -> Optional[str]:
        """
        Get an item from localStorage
        
        Args:
            key: Key to retrieve from localStorage
            
        Returns:
            Value if found, None if not found or error
        """
        script = f"return window.localStorage.getItem('{key}');"
        return self.execute_script(script)
    
    def set_local_storage_item(self, key: str, value: str) -> None:
        """
        Set an item in localStorage
        
        Args:
            key: Key to set in localStorage
            value: Value to set
        """
        script = f"window.localStorage.setItem('{key}', '{value}');"
        self.execute_script(script)
    
    def clear_local_storage(self) -> None:
        """Clear all items in localStorage"""
        script = "window.localStorage.clear();"
        self.execute_script(script)
    
    def get_current_url(self) -> str:
        """
        Get the current browser URL
        
        Returns:
            Current URL string
        """
        return self.driver.current_url
    
    def navigate_to(self, url: str) -> None:
        """
        Navigate to a specific URL
        
        Args:
            url: URL to navigate to
        """
        self.driver.get(url)