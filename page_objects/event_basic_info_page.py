from typing import Optional
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base_page import BasePage

# Configure logging
logger = logging.getLogger(__name__)


class EventBasicInfoPage(BasePage):
    """Page object for the event basic info page (/event/basic-info)"""
    
    def __init__(self, driver: WebDriver):
        """
        Initialize the EventBasicInfoPage with locators
        
        Args:
            driver: WebDriver instance for browser interaction
        """
        super().__init__(driver)
        
        # Form fields
        self.title_input = (By.ID, "formTitulo")
        self.email_input = (By.ID, "formProfessor")  # Disabled field
        self.phone_input = (By.ID, "telefone")
        self.ods_select = (By.ID, "ods")
        
        # Navigation buttons
        self.next_button = (By.XPATH, "//button[contains(text(), 'Próximo')]")
        self.back_button = (By.CSS_SELECTOR, "svg[viewBox='0 0 1024 1024']")
    
    def is_on_basic_info_page(self) -> bool:
        """
        Check if currently on the basic info page
        
        Returns:
            True if on basic info page, False otherwise
        """
        try:
            current_url = self.get_current_url()
            return "/event/basic-info" in current_url
        except:
            return False
    
    def fill_event_title(self, title: str) -> None:
        """
        Fill the event title field with better persistence
        
        Args:
            title: Event title to enter
        """
        element = self.find_element(self.title_input)
        
        # Clear field properly
        element.clear()
        
        # Click to focus
        element.click()
        
        # Enter text with small delay
        import time
        time.sleep(0.2)
        element.send_keys(title)
        
        # Trigger blur event to ensure value persists
        self.driver.execute_script("arguments[0].blur();", element)
        
        # Verify the value was set
        time.sleep(0.2)
        actual_value = element.get_attribute('value')
        if actual_value != title:
            logger.warning(f"Title not persisted properly. Expected: '{title}', Got: '{actual_value}'. Retrying...")
            element.clear()
            element.click()
            element.send_keys(title)
            self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", element)
            self.driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", element)
        
        logger.info(f"Filled event title: {title}")
    
    def get_user_email(self) -> Optional[str]:
        """
        Get the user email from the disabled field
        
        Returns:
            User email if found, None otherwise
        """
        try:
            element = self.find_element(self.email_input)
            return element.get_attribute('value')
        except (TimeoutException, NoSuchElementException):
            return None
    
    def fill_phone(self, phone: str) -> None:
        """
        Fill the phone field with better persistence
        
        Args:
            phone: Phone number to enter
        """
        element = self.find_element(self.phone_input)
        
        # Clear field properly
        element.clear()
        
        # Click to focus
        element.click()
        
        # Enter text with small delay
        import time
        time.sleep(0.2)
        element.send_keys(phone)
        
        # Trigger events to ensure value persists
        self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", element)
        self.driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", element)
        self.driver.execute_script("arguments[0].blur();", element)
        
        # Verify the value was set
        time.sleep(0.2)
        actual_value = element.get_attribute('value')
        logger.info(f"Filled phone: {phone}, actual value: {actual_value}")
    
    def select_ods(self, ods_value: str) -> None:
        """
        Select an ODS option from the dropdown with better persistence
        
        Args:
            ods_value: ODS value to select (can be number or text)
        """
        try:
            select_element = Select(self.find_element(self.ods_select))
            
            # Click to focus on select
            select_element._el.click()
            
            import time
            time.sleep(0.5)
            
            # Try to select by value first
            try:
                select_element.select_by_value(ods_value)
                logger.info(f"Selected ODS by value: {ods_value}")
            except:
                # Try to select by visible text
                select_element.select_by_visible_text(ods_value)
                logger.info(f"Selected ODS by text: {ods_value}")
            
            # Trigger change event
            self.driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", select_element._el)
            
            # Verify selection
            time.sleep(0.2)
            selected_value = select_element._el.get_attribute('value')
            logger.info(f"ODS selection verified - value: {selected_value}")
            
        except (TimeoutException, NoSuchElementException) as e:
            raise Exception(f"Failed to select ODS '{ods_value}': {str(e)}")
    
    def get_available_ods_options(self) -> list:
        """
        Get all available ODS options
        
        Returns:
            List of available ODS options as tuples (value, text)
        """
        try:
            select_element = Select(self.find_element(self.ods_select))
            options = []
            for option in select_element.options:
                value = option.get_attribute('value')
                text = option.text
                if value:  # Skip empty/disabled options
                    options.append((value, text))
            return options
        except (TimeoutException, NoSuchElementException):
            return []
    
    def verify_fields_filled(self) -> bool:
        """
        Verify that all required fields are properly filled
        
        Returns:
            True if all fields are filled, False otherwise
        """
        try:
            # Check title
            title_element = self.find_element(self.title_input)
            title_value = title_element.get_attribute('value')
            
            # Check phone  
            phone_element = self.find_element(self.phone_input)
            phone_value = phone_element.get_attribute('value')
            
            # Check ODS
            ods_element = self.find_element(self.ods_select)
            ods_value = ods_element.get_attribute('value')
            
            logger.info(f"Field verification - Title: '{title_value}', Phone: '{phone_value}', ODS: '{ods_value}'")
            
            return bool(title_value and phone_value and ods_value)
            
        except Exception as e:
            logger.error(f"Error verifying fields: {str(e)}")
            return False
    
    def click_next(self) -> None:
        """Click the 'Próximo' button to go to details page"""
        # Verify fields before clicking next
        if not self.verify_fields_filled():
            logger.warning("Not all required fields are filled!")
        
        self.click_element(self.next_button)
        logger.info("Clicked 'Próximo' button on basic info page")
    
    def click_back(self) -> None:
        """Click the back arrow to return to type selection"""
        self.click_element(self.back_button)
        logger.info("Clicked back button on basic info page")
    
    def fill_basic_info(self, title: str, phone: str = None, ods: str = None) -> None:
        """
        Fill all basic info fields
        
        Args:
            title: Event title
            phone: Phone number (optional)
            ods: ODS selection (optional)
        """
        self.fill_event_title(title)
        
        if phone:
            self.fill_phone(phone)
        
        if ods:
            self.select_ods(ods)
    
    def wait_for_page_load(self) -> bool:
        """
        Wait for the basic info page to fully load
        
        Returns:
            True if page loaded successfully, False otherwise
        """
        try:
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(self.title_input)
            )
            return True
        except TimeoutException:
            return False
