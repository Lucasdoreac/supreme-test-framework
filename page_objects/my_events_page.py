from typing import Optional, List
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base_page import BasePage

# Configure logging
logger = logging.getLogger(__name__)


class MyEventsPage(BasePage):
    """Page object for the 'Meus Eventos' (My Events) page"""
    
    def __init__(self, driver: WebDriver):
        """
        Initialize the MyEventsPage with locators based on actual HTML structure
        
        Args:
            driver: WebDriver instance for browser interaction
        """
        super().__init__(driver)
        
        # Page identification locators
        self.page_title = (By.XPATH, "//h1[contains(text(), 'Meus Eventos')] | //h2[contains(text(), 'Meus Eventos')]")
        
        # Main action buttons - Based on actual HTML structure
        self.create_event_button = (By.XPATH, "//a[@class='btn btn-primary text-white'][@href='/event/type-selection']")
        self.create_event_button_text = (By.XPATH, "//a[contains(text(), 'Cadastrar Evento')]")
        
        # Events structure - Based on actual HTML
        self.events_container = (By.CSS_SELECTOR, ".row")
        self.event_cards = (By.CSS_SELECTOR, ".col-md-6.mb-4")
        self.event_card_bodies = (By.CSS_SELECTOR, ".card.h-100.shadow")
        
        # Event card components
        self.event_titles = (By.CSS_SELECTOR, ".card-title")
        self.event_statuses = (By.CSS_SELECTOR, ".badge")
        self.event_descriptions = (By.XPATH, "//strong[contains(text(), 'Descrição:')]/following-sibling::text()")
        
        # Empty state
        self.empty_events_message = (By.XPATH, "//p[contains(text(), 'Nenhum evento')] | //div[contains(text(), 'Você não tem eventos')]")
        
        # User info
        self.user_email = (By.CSS_SELECTOR, "[data-testid='user-email'], .user-info")
        
        # Navigation elements
        self.logout_button = (By.XPATH, "//button[contains(text(), 'Sair')] | //a[contains(text(), 'Logout')]")
    
    def click_create_event_button(self) -> None:
        """
        Click the 'Cadastrar Evento' button to navigate to create event page
        Based on: <a class="btn btn-primary text-white" href="/event/type-selection">Cadastrar Evento</a>
        """
        try:
            # Try the exact selector first
            if self.is_element_visible(self.create_event_button, timeout=5):
                self.click_element(self.create_event_button)
                logger.info("Clicked 'Cadastrar Evento' button using href selector")
                return
            
            # Try by text content
            if self.is_element_visible(self.create_event_button_text, timeout=3):
                self.click_element(self.create_event_button_text)
                logger.info("Clicked 'Cadastrar Evento' button using text selector")
                return
            
            # Try more flexible selectors
            flexible_selectors = [
                (By.XPATH, "//a[contains(@href, '/event/type-selection')]"),
                (By.XPATH, "//a[contains(@href, 'type-selection')]"),
                (By.CSS_SELECTOR, "a.btn.btn-primary"),
                (By.XPATH, "//a[@class='btn btn-primary text-white']"),
            ]
            
            for selector in flexible_selectors:
                if self.is_element_visible(selector, timeout=2):
                    self.click_element(selector)
                    logger.info(f"Clicked button using selector: {selector}")
                    return
            
            # Log available buttons for debugging
            self._log_available_buttons()
            raise Exception("Create event button not found on My Events page")
            
        except Exception as e:
            logger.error(f"Error clicking create event button: {str(e)}")
            raise
    
    def _log_available_buttons(self) -> None:
        """Log available buttons and links for debugging purposes"""
        try:
            # Log all buttons
            all_buttons = self.find_elements((By.TAG_NAME, "button"), timeout=5)
            button_texts = [btn.text.strip() for btn in all_buttons if btn.text.strip()]
            logger.info(f"Available buttons: {button_texts}")
            
            # Log all links
            all_links = self.find_elements((By.TAG_NAME, "a"), timeout=5)
            link_info = []
            for link in all_links:
                text = link.text.strip()
                href = link.get_attribute('href')
                if text or href:
                    link_info.append(f"'{text}' -> {href}")
            logger.info(f"Available links: {link_info[:10]}")  # Limit to first 10
            
        except Exception as e:
            logger.warning(f"Could not retrieve available elements for debugging: {str(e)}")
    
    def is_on_my_events_page(self) -> bool:
        """
        Check if currently on the 'Meus Eventos' page
        
        Returns:
            True if on My Events page, False otherwise
        """
        try:
            # Check for page title
            if self.is_element_visible(self.page_title, timeout=5):
                return True
            
            # Check URL as alternative
            current_url = self.get_current_url()
            return "/event/mine" in current_url or "/meus-eventos" in current_url or "/eventos" in current_url
        except:
            return False
    
    def get_events_count(self) -> int:
        """
        Get the number of events displayed on the page
        Based on: .col-md-6.mb-4 (event card containers)
        
        Returns:
            Number of events
        """
        try:
            event_cards = self.find_elements(self.event_cards, timeout=5)
            # Filter out the button container (which is col-12)
            actual_events = [card for card in event_cards if 'col-md-6' in card.get_attribute('class')]
            return len(actual_events)
        except (TimeoutException, NoSuchElementException):
            return 0
    
    def get_event_titles(self) -> List[str]:
        """
        Get all event titles from the event cards
        
        Returns:
            List of event titles
        """
        try:
            title_elements = self.find_elements(self.event_titles, timeout=5)
            return [title.text.strip() for title in title_elements if title.text.strip()]
        except (TimeoutException, NoSuchElementException):
            return []
    
    def get_event_statuses(self) -> List[str]:
        """
        Get all event statuses from the badges
        
        Returns:
            List of event statuses
        """
        try:
            status_elements = self.find_elements(self.event_statuses, timeout=5)
            return [status.text.strip() for status in status_elements if status.text.strip()]
        except (TimeoutException, NoSuchElementException):
            return []
    
    def has_empty_events_message(self) -> bool:
        """
        Check if the page shows an empty events message
        
        Returns:
            True if empty message is visible, False otherwise
        """
        return self.is_element_visible(self.empty_events_message, timeout=3)
    
    def get_user_email(self) -> Optional[str]:
        """
        Get the displayed user email
        
        Returns:
            User email if found, None otherwise
        """
        try:
            return self.get_text(self.user_email)
        except (TimeoutException, NoSuchElementException):
            return None
    
    def wait_for_page_load(self) -> bool:
        """
        Wait for the My Events page to fully load
        
        Returns:
            True if page loaded successfully, False otherwise
        """
        try:
            # Wait for either the events container or the create event button to be visible
            WebDriverWait(self.driver, 10).until(
                lambda driver: (
                    self.is_element_visible(self.events_container, timeout=1) or
                    self.is_element_visible(self.create_event_button, timeout=1) or
                    self.is_element_visible(self.create_event_button_text, timeout=1)
                )
            )
            return True
        except TimeoutException:
            return False
    
    def navigate_to_my_events_page(self) -> None:
        """
        Navigate directly to the My Events page
        """
        # This assumes we know the URL pattern - adjust based on your application
        current_url = self.get_current_url()
        base_url = current_url.split('/')[0] + '//' + current_url.split('/')[2]
        my_events_url = f"{base_url}/event/mine"
        self.navigate_to(my_events_url)
        self.wait_for_page_load()
