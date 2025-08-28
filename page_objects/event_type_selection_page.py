from typing import Optional
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base_page import BasePage

# Configure logging
logger = logging.getLogger(__name__)


class EventTypeSelectionPage(BasePage):
    """Page object for the event type selection page (/event/type-selection)"""
    
    def __init__(self, driver: WebDriver):
        """
        Initialize the EventTypeSelectionPage with locators
        
        Args:
            driver: WebDriver instance for browser interaction
        """
        super().__init__(driver)
        
        # Page identification
        self.radio_group = (By.CSS_SELECTOR, ".radio-group")
        
        # Event type radio buttons
        self.workshop_radio = (By.ID, "eventType-workshop")
        self.lecture_radio = (By.ID, "eventType-lecture")
        self.exam_radio = (By.ID, "eventType-exam")
        self.class_radio = (By.ID, "eventType-class")
        
        # Event type labels
        self.workshop_label = (By.CSS_SELECTOR, "label[for='eventType-workshop']")
        self.lecture_label = (By.CSS_SELECTOR, "label[for='eventType-lecture']")
        self.exam_label = (By.CSS_SELECTOR, "label[for='eventType-exam']")
        self.class_label = (By.CSS_SELECTOR, "label[for='eventType-class']")
        
        # Navigation buttons
        self.next_button = (By.XPATH, "//button[contains(text(), 'Próximo')]")
        self.back_button = (By.CSS_SELECTOR, "svg[viewBox='0 0 1024 1024']")
    
    def is_on_type_selection_page(self) -> bool:
        """
        Check if currently on the event type selection page
        
        Returns:
            True if on type selection page, False otherwise
        """
        try:
            current_url = self.get_current_url()
            return "/event/type-selection" in current_url
        except:
            return False
    
    def select_event_type(self, event_type: str) -> None:
        """
        Select an event type by clicking the radio button
        
        Args:
            event_type: Type of event ('workshop', 'lecture', 'exam', 'class', 
                       'mão na massa', 'palestra', 'avaliação', 'aula')
        """
        event_type_lower = event_type.lower()
        
        # Map Portuguese names to English IDs
        type_mapping = {
            'mão na massa': 'workshop',
            'palestra': 'lecture', 
            'avaliação': 'exam',
            'aula': 'class'
        }
        
        # Get the actual type to select
        actual_type = type_mapping.get(event_type_lower, event_type_lower)
        
        # Map to selectors
        type_selectors = {
            'workshop': self.workshop_radio,
            'lecture': self.lecture_radio,
            'exam': self.exam_radio,
            'class': self.class_radio
        }
        
        if actual_type in type_selectors:
            selector = type_selectors[actual_type]
            self.click_element(selector)
            logger.info(f"Selected event type: {actual_type}")
        else:
            raise ValueError(f"Unknown event type: {event_type}")
    
    def get_selected_event_type(self) -> Optional[str]:
        """
        Get the currently selected event type
        
        Returns:
            Selected event type or None if none selected
        """
        try:
            # Check which radio button is selected
            for type_name, selector in [
                ('workshop', self.workshop_radio),
                ('lecture', self.lecture_radio),
                ('exam', self.exam_radio),
                ('class', self.class_radio)
            ]:
                element = self.find_element(selector, timeout=2)
                if element.is_selected():
                    return type_name
            return None
        except (TimeoutException, NoSuchElementException):
            return None
    
    def click_next(self) -> None:
        """Click the 'Próximo' button to go to basic info page"""
        self.click_element(self.next_button)
        logger.info("Clicked 'Próximo' button on type selection page")
    
    def click_back(self) -> None:
        """Click the back arrow to return to previous page"""
        self.click_element(self.back_button)
        logger.info("Clicked back button on type selection page")
    
    def wait_for_page_load(self) -> bool:
        """
        Wait for the type selection page to fully load
        
        Returns:
            True if page loaded successfully, False otherwise
        """
        try:
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(self.radio_group)
            )
            return True
        except TimeoutException:
            return False
