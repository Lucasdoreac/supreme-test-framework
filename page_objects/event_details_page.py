from typing import Optional, List
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base_page import BasePage

# Configure logging
logger = logging.getLogger(__name__)


class EventDetailsPage(BasePage):
    """Page object for the event details page (/event/details)"""
    
    def __init__(self, driver: WebDriver):
        """
        Initialize the EventDetailsPage with locators
        
        Args:
            driver: WebDriver instance for browser interaction
        """
        super().__init__(driver)
        
        # Form fields
        self.description_textarea = (By.ID, "descricaoEvento")
        self.course_search_input = (By.ID, "curso-search")
        self.course_select = (By.ID, "curso")
        self.course_change_button = (By.XPATH, "//button[contains(text(), 'Alterar curso')]")
        
        # Public target checkboxes
        self.students_checkbox = (By.ID, "alunosUDF")
        self.professors_checkbox = (By.ID, "professores")
        self.external_checkbox = (By.ID, "publicoExterno")
        
        # Resources checkboxes
        self.human_resources_checkbox = (By.ID, "humanas")
        self.technology_checkbox = (By.ID, "tecnologias")
        self.services_checkbox = (By.ID, "servicos")
        self.materials_checkbox = (By.ID, "materiais")
        
        # Navigation buttons
        self.next_button = (By.XPATH, "//button[contains(text(), 'Próximo')]")
        self.back_button = (By.CSS_SELECTOR, "svg[viewBox='0 0 1024 1024']")
    
    def is_on_details_page(self) -> bool:
        """
        Check if currently on the details page
        
        Returns:
            True if on details page, False otherwise
        """
        try:
            current_url = self.get_current_url()
            return "/event/details" in current_url
        except:
            return False
    
    def fill_description(self, description: str) -> None:
        """
        Fill the event description textarea
        
        Args:
            description: Event description
        """
        self.enter_text(self.description_textarea, description)
        logger.info(f"Filled event description: {description}")
    
    def search_and_select_course(self, course_search: str, course_option: str = None) -> None:
        """
        Search for a course and select one from the dropdown
        
        Args:
            course_search: Text to search for courses
            course_option: Specific course option to select (if None, selects first available)
        """
        # Clear and enter search term
        self.enter_text(self.course_search_input, course_search)
        logger.info(f"Searching for course: {course_search}")
        
        # Wait for dropdown to populate
        time.sleep(2)
        
        try:
            select_element = Select(self.find_element(self.course_select))
            
            if course_option:
                # Select specific option
                select_element.select_by_visible_text(course_option)
                logger.info(f"Selected course: {course_option}")
            else:
                # Select first available option (not the disabled placeholder)
                options = [opt for opt in select_element.options if opt.get_attribute('value')]
                if options:
                    select_element.select_by_visible_text(options[0].text)
                    logger.info(f"Selected first available course: {options[0].text}")
                else:
                    raise Exception("No course options available")
                    
        except Exception as e:
            raise Exception(f"Failed to select course: {str(e)}")
    
    def get_available_courses(self) -> List[str]:
        """
        Get list of available courses in the dropdown
        
        Returns:
            List of course names
        """
        try:
            select_element = Select(self.find_element(self.course_select))
            return [opt.text for opt in select_element.options if opt.get_attribute('value')]
        except (TimeoutException, NoSuchElementException):
            return []
    
    def click_change_course(self) -> None:
        """Click the 'Alterar curso' button to change selected course"""
        if self.is_element_visible(self.course_change_button, timeout=3):
            self.click_element(self.course_change_button)
            logger.info("Clicked 'Alterar curso' button")
    
    def select_public_target(self, targets: List[str]) -> None:
        """
        Select public target checkboxes
        
        Args:
            targets: List of targets ('students', 'professors', 'external', 
                    'alunos udf', 'professores', 'público externo')
        """
        target_mapping = {
            'students': self.students_checkbox,
            'alunos udf': self.students_checkbox,
            'alunosudf': self.students_checkbox,
            'professors': self.professors_checkbox,
            'professores': self.professors_checkbox,
            'external': self.external_checkbox,
            'público externo': self.external_checkbox,
            'publicoexterno': self.external_checkbox
        }
        
        for target in targets:
            target_key = target.lower().replace(' ', '')
            if target_key in target_mapping:
                checkbox = target_mapping[target_key]
                element = self.find_element(checkbox)
                if not element.is_selected():
                    element.click()
                    logger.info(f"Selected public target: {target}")
    
    def select_resources(self, resources: List[str]) -> None:
        """
        Select resource checkboxes
        
        Args:
            resources: List of resources ('human', 'technology', 'services', 'materials',
                      'humanas', 'tecnologias', 'serviços', 'materiais')
        """
        resource_mapping = {
            'human': self.human_resources_checkbox,
            'humanas': self.human_resources_checkbox,
            'technology': self.technology_checkbox,
            'tecnologias': self.technology_checkbox,
            'services': self.services_checkbox,
            'serviços': self.services_checkbox,
            'servicos': self.services_checkbox,
            'materials': self.materials_checkbox,
            'materiais': self.materials_checkbox
        }
        
        for resource in resources:
            resource_key = resource.lower()
            if resource_key in resource_mapping:
                checkbox = resource_mapping[resource_key]
                element = self.find_element(checkbox)
                if not element.is_selected():
                    element.click()
                    logger.info(f"Selected resource: {resource}")
    
    def get_selected_public_targets(self) -> List[str]:
        """
        Get currently selected public targets
        
        Returns:
            List of selected target names
        """
        selected = []
        targets = [
            ('Alunos UDF', self.students_checkbox),
            ('Professores', self.professors_checkbox),
            ('Público Externo', self.external_checkbox)
        ]
        
        for name, selector in targets:
            try:
                element = self.find_element(selector, timeout=2)
                if element.is_selected():
                    selected.append(name)
            except:
                pass
        
        return selected
    
    def get_selected_resources(self) -> List[str]:
        """
        Get currently selected resources
        
        Returns:
            List of selected resource names
        """
        selected = []
        resources = [
            ('Humanas', self.human_resources_checkbox),
            ('Tecnologias', self.technology_checkbox),
            ('Serviços', self.services_checkbox),
            ('Materiais', self.materials_checkbox)
        ]
        
        for name, selector in resources:
            try:
                element = self.find_element(selector, timeout=2)
                if element.is_selected():
                    selected.append(name)
            except:
                pass
        
        return selected
    
    def click_next(self) -> None:
        """Click the 'Próximo' button to go to logistics page"""
        self.click_element(self.next_button)
        logger.info("Clicked 'Próximo' button on details page")
    
    def click_back(self) -> None:
        """Click the back arrow to return to basic info page"""
        self.click_element(self.back_button)
        logger.info("Clicked back button on details page")
    
    def wait_for_page_load(self) -> bool:
        """
        Wait for the details page to fully load
        
        Returns:
            True if page loaded successfully, False otherwise
        """
        try:
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(self.description_textarea)
            )
            return True
        except TimeoutException:
            return False
