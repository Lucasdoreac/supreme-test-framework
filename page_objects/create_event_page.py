from typing import Dict, List, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base_page import BasePage


class CreateEventPage(BasePage):
    """Page object for the create event page"""
    
    def __init__(self, driver: WebDriver):
        """
        Initialize the CreateEventPage with locators
        
        Args:
            driver: WebDriver instance for browser interaction
        """
        super().__init__(driver)
        
        # Page identification
        self.page_title = (By.XPATH, "//h1[contains(text(), 'Criar')] | //h1[contains(text(), 'Novo Evento')] | //h2[contains(text(), 'Criar')] | //h2[contains(text(), 'Novo Evento')]")
        
        # Basic form locators
        self.title_input = (By.NAME, "title")
        self.title_input_alt = (By.CSS_SELECTOR, "input[placeholder*='título'], input[placeholder*='Título'], #title")
        
        self.description_textarea = (By.NAME, "description")
        self.description_textarea_alt = (By.CSS_SELECTOR, "textarea[placeholder*='descrição'], textarea[placeholder*='Descrição'], #description")
        
        self.date_input = (By.NAME, "date")
        self.date_input_alt = (By.CSS_SELECTOR, "input[type='date'], input[placeholder*='data'], input[placeholder*='Data'], #date")
        
        self.time_input = (By.NAME, "time")
        self.time_input_alt = (By.CSS_SELECTOR, "input[type='time'], input[placeholder*='horário'], input[placeholder*='Horário'], #time")
        
        self.location_input = (By.NAME, "location")
        self.location_input_alt = (By.CSS_SELECTOR, "input[placeholder*='local'], input[placeholder*='Local'], #location")
        
        # Action buttons
        self.create_button = (By.XPATH, "//button[contains(text(), 'Criar Evento')] | //button[contains(text(), 'Salvar')] | //button[@type='submit']")
        self.next_button = (By.XPATH, "//button[contains(text(), 'Próximo')]")
        
        # Error message locators
        self.title_error = (By.CSS_SELECTOR, "[data-testid='title-error'], .title-error, .error-message")
        self.date_error = (By.CSS_SELECTOR, "[data-testid='date-error'], .date-error")
        self.general_error = (By.CSS_SELECTOR, ".error-message, .alert-error, [role='alert'][class*='error']")
        
        # Success message locators
        self.success_message = (By.CSS_SELECTOR, ".success-message, .alert-success, [role='alert'][class*='success']")
        
        # Event details page elements
        self.event_details_title = (By.CSS_SELECTOR, "[data-testid='event-title'], .event-title, h1, h2")
    
    def find_input_element(self, primary_locator: tuple, alternative_locator: tuple):
        """
        Try to find an input element using primary locator, fallback to alternative
        
        Args:
            primary_locator: Primary locator tuple
            alternative_locator: Alternative locator tuple
            
        Returns:
            WebElement if found
        """
        try:
            return self.find_element(primary_locator, timeout=3)
        except TimeoutException:
            return self.find_element(alternative_locator)
    
    def fill_event_title(self, title: str) -> None:
        """
        Fill the event title field
        
        Args:
            title: Event title to enter
        """
        element = self.find_input_element(self.title_input, self.title_input_alt)
        element.clear()
        element.send_keys(title)
    
    def fill_event_description(self, description: str) -> None:
        """
        Fill the event description field
        
        Args:
            description: Event description to enter
        """
        element = self.find_input_element(self.description_textarea, self.description_textarea_alt)
        element.clear()
        element.send_keys(description)
    
    def fill_event_date(self, date: str) -> None:
        """
        Fill the event date field
        
        Args:
            date: Event date in format DD/MM/YYYY or YYYY-MM-DD
        """
        element = self.find_input_element(self.date_input, self.date_input_alt)
        element.clear()
        
        # Convert DD/MM/YYYY to YYYY-MM-DD for date input if needed
        if "/" in date and len(date.split("/")) == 3:
            day, month, year = date.split("/")
            date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        element.send_keys(date)
    
    def fill_event_time(self, time: str) -> None:
        """
        Fill the event time field
        
        Args:
            time: Event time in format HH:MM
        """
        element = self.find_input_element(self.time_input, self.time_input_alt)
        element.clear()
        element.send_keys(time)
    
    def fill_event_location(self, location: str) -> None:
        """
        Fill the event location field
        
        Args:
            location: Event location
        """
        element = self.find_input_element(self.location_input, self.location_input_alt)
        element.clear()
        element.send_keys(location)
    
    def click_create_event_button(self) -> None:
        """Click the 'Criar Evento' button"""
        self.click_element(self.create_button)
    
    def click_next_button(self) -> None:
        """Click the 'Próximo' button for multi-step forms"""
        self.click_element(self.next_button)
    
    def is_on_create_event_page(self) -> bool:
        """
        Check if currently on the create event page or type selection page
        
        Returns:
            True if on create event page, False otherwise
        """
        try:
            # Check current URL first - this is more reliable
            current_url = self.get_current_url()
            
            # Check if we're on type-selection page (first step of event creation)
            if "/event/type-selection" in current_url:
                return True
            
            # Check if we're on a general event creation page
            if "/event/create" in current_url or "/criar" in current_url:
                return True
            
            # Check for page title
            if self.is_element_visible(self.page_title, timeout=3):
                return True
            
            # Check for form elements as alternative
            return (self.is_element_visible(self.title_input, timeout=3) or 
                   self.is_element_visible(self.title_input_alt, timeout=3))
        except:
            return False
    
    def get_success_message(self) -> Optional[str]:
        """
        Get the success message text
        
        Returns:
            Success message text if found, None otherwise
        """
        try:
            if self.is_element_visible(self.success_message, timeout=5):
                return self.get_text(self.success_message)
            return None
        except (TimeoutException, NoSuchElementException):
            return None
    
    def get_error_messages(self) -> List[str]:
        """
        Get all visible error messages
        
        Returns:
            List of error message texts
        """
        error_messages = []
        
        # Check for specific field errors and general errors
        error_locators = [self.title_error, self.date_error, self.general_error]
        
        for locator in error_locators:
            try:
                if self.is_element_visible(locator, timeout=2):
                    error_text = self.get_text(locator)
                    if error_text and error_text not in error_messages:
                        error_messages.append(error_text)
            except:
                continue
        
        return error_messages
    
    def is_redirected_to_event_details(self) -> bool:
        """
        Check if redirected to event details page
        
        Returns:
            True if on event details page, False otherwise
        """
        try:
            # Wait for URL change and check for event details elements
            self.wait_until_url_contains("/event", 10)
            return self.is_element_visible(self.event_details_title, timeout=5)
        except:
            return False
    
    def get_event_title_from_details_page(self) -> Optional[str]:
        """
        Get the event title from the event details page
        
        Returns:
            Event title if found, None otherwise
        """
        try:
            return self.get_text(self.event_details_title)
        except (TimeoutException, NoSuchElementException):
            return None
    
    def fill_basic_event_info(self, event_data: Dict[str, str]) -> None:
        """
        Fill all basic event information from a dictionary
        
        Args:
            event_data: Dictionary with event information
        """
        if 'título' in event_data:
            self.fill_event_title(event_data['título'])
        if 'descrição' in event_data:
            self.fill_event_description(event_data['descrição'])
        if 'data' in event_data:
            self.fill_event_date(event_data['data'])
        if 'horário' in event_data:
            self.fill_event_time(event_data['horário'])
        if 'local' in event_data:
            self.fill_event_location(event_data['local'])
