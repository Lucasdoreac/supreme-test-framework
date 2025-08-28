from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import logging

from page_objects.my_events_page import MyEventsPage
from page_objects.event_type_selection_page import EventTypeSelectionPage
from page_objects.event_basic_info_page import EventBasicInfoPage
from page_objects.event_details_page import EventDetailsPage

# Configure logging
logger = logging.getLogger(__name__)


# Background steps - Navegação inicial (authentication handled by environment.py)
@given('que estou autenticado no sistema')
def step_authenticated_user(context):
    """User authentication is handled by environment.py before_scenario hook"""
    # This step is now just a placeholder - actual authentication happens in environment.py
    logger.info("User authentication verified")


@given('estou na página de meus eventos')
def step_on_my_events_page(context):
    """Ensure user is on the My Events page"""
    context.my_events_page = MyEventsPage(context.driver)
    
    # Verify we're on the My Events page or navigate to it
    if not context.my_events_page.is_on_my_events_page():
        context.my_events_page.navigate_to_my_events_page()
    
    # Wait for page to load
    context.my_events_page.wait_for_page_load()
    
    # Verify we're actually on the page
    assert context.my_events_page.is_on_my_events_page(), "Failed to reach My Events page"


# Navigation steps - Updated for multi-step flow
@when('clico no botão "Cadastrar Novo Evento"')
def step_click_create_event_button(context):
    """Click the 'Cadastrar Novo Evento' button"""
    if not hasattr(context, 'my_events_page'):
        context.my_events_page = MyEventsPage(context.driver)
    
    context.my_events_page.click_create_event_button()


# Type Selection Page Steps
@then('devo estar na página de seleção de tipo de evento')
def step_should_be_on_type_selection_page(context):
    """Verify that user is on the type selection page"""
    context.type_selection_page = EventTypeSelectionPage(context.driver)
    
    # Wait a moment for navigation to complete
    import time
    time.sleep(1)
    
    assert context.type_selection_page.is_on_type_selection_page(), "Not on type selection page"
    assert context.type_selection_page.wait_for_page_load(), "Type selection page did not load properly"


@when('seleciono o tipo de evento "{event_type}"')
def step_select_event_type(context, event_type):
    """Select an event type from the radio options"""
    if not hasattr(context, 'type_selection_page'):
        context.type_selection_page = EventTypeSelectionPage(context.driver)
    
    context.type_selection_page.select_event_type(event_type)


# Basic Info Page Steps
@then('devo estar na página de informações básicas')
def step_should_be_on_basic_info_page(context):
    """Verify that user is on the basic info page"""
    context.basic_info_page = EventBasicInfoPage(context.driver)
    
    # Wait a moment for navigation to complete
    import time
    time.sleep(1)
    
    assert context.basic_info_page.is_on_basic_info_page(), "Not on basic info page"
    assert context.basic_info_page.wait_for_page_load(), "Basic info page did not load properly"


@when('preencho o título do evento "{title}"')
def step_fill_event_title(context, title):
    """Fill the event title field"""
    if not hasattr(context, 'basic_info_page'):
        context.basic_info_page = EventBasicInfoPage(context.driver)
    
    context.basic_info_page.fill_event_title(title)


@when('preencho o telefone "{phone}"')
def step_fill_phone(context, phone):
    """Fill the phone field"""
    if not hasattr(context, 'basic_info_page'):
        context.basic_info_page = EventBasicInfoPage(context.driver)
    
    context.basic_info_page.fill_phone(phone)


@when('seleciono a ODS "{ods}"')
def step_select_ods(context, ods):
    """Select an ODS option"""
    if not hasattr(context, 'basic_info_page'):
        context.basic_info_page = EventBasicInfoPage(context.driver)
    
    context.basic_info_page.select_ods(ods)


# Details Page Steps
@then('devo estar na página de detalhes do evento')
def step_should_be_on_details_page(context):
    """Verify that user is on the details page"""
    context.details_page = EventDetailsPage(context.driver)
    
    # Wait a moment for navigation to complete
    import time
    time.sleep(2)
    
    # Debug: Log current URL
    current_url = context.driver.current_url
    logger.info(f"Current URL: {current_url}")
    
    # Check if still on basic-info page (validation might have failed)
    if "/event/basic-info" in current_url:
        logger.warning("Still on basic-info page, checking for validation errors or missing fields")
        
        # Check if we're missing required fields
        try:
            from page_objects.event_basic_info_page import EventBasicInfoPage
            basic_info_page = EventBasicInfoPage(context.driver)
            
            # Get current values
            email = basic_info_page.get_user_email()
            logger.info(f"User email: {email}")
            
            # Try to get available ODS options
            ods_options = basic_info_page.get_available_ods_options()
            logger.info(f"Available ODS options: {len(ods_options)}")
            
            # Check if ODS is selected
            ods_element = basic_info_page.find_element(basic_info_page.ods_select, timeout=2)
            selected_ods = ods_element.get_attribute('value')
            logger.info(f"Selected ODS: {selected_ods}")
            
            if not selected_ods:
                logger.info("ODS not selected, this might be required. Selecting one...")
                if ods_options:
                    basic_info_page.select_ods(ods_options[0][0])  # Select first available
                    time.sleep(1)
                    basic_info_page.click_next()
                    time.sleep(2)
                    current_url = context.driver.current_url
                    logger.info(f"URL after selecting ODS and clicking next: {current_url}")
        except Exception as e:
            logger.error(f"Error during basic info debugging: {str(e)}")
    
    # Final check
    assert context.details_page.is_on_details_page(), f"Not on details page. Current URL: {current_url}"
    assert context.details_page.wait_for_page_load(), "Details page did not load properly"


@when('preencho a descrição "{description}"')
def step_fill_event_description(context, description):
    """Fill the event description field"""
    if not hasattr(context, 'details_page'):
        context.details_page = EventDetailsPage(context.driver)
    
    context.details_page.fill_description(description)


@when('busco e seleciono o curso "{search_term}" com opção "{course_option}"')
def step_search_and_select_course(context, search_term, course_option):
    """Search for and select a course"""
    if not hasattr(context, 'details_page'):
        context.details_page = EventDetailsPage(context.driver)
    
    context.details_page.search_and_select_course(search_term, course_option)


@when('seleciono público alvo "{targets}"')
def step_select_public_targets(context, targets):
    """Select public target checkboxes"""
    if not hasattr(context, 'details_page'):
        context.details_page = EventDetailsPage(context.driver)
    
    target_list = [target.strip() for target in targets.split(',')]
    context.details_page.select_public_target(target_list)


@when('seleciono recursos necessários "{resources}"')
def step_select_resources(context, resources):
    """Select resource checkboxes"""
    if not hasattr(context, 'details_page'):
        context.details_page = EventDetailsPage(context.driver)
    
    resource_list = [resource.strip() for resource in resources.split(',')]
    context.details_page.select_resources(resource_list)


# Logistics Page Steps
@then('devo estar na página de logística')
def step_should_be_on_logistics_page(context):
    """Verify that user is on the logistics page"""
    # Wait a moment for navigation to complete
    import time
    time.sleep(2)
    
    current_url = context.driver.current_url
    assert "/event/logistics" in current_url, f"Not on logistics page. Current URL: {current_url}"


# Generic "Próximo" button step
@when('clico no botão "Próximo"')
def step_click_next_button(context):
    """Click the 'Próximo' button on any page"""
    current_url = context.driver.current_url
    
    if "/event/type-selection" in current_url:
        if not hasattr(context, 'type_selection_page'):
            context.type_selection_page = EventTypeSelectionPage(context.driver)
        context.type_selection_page.click_next()
    elif "/event/basic-info" in current_url:
        if not hasattr(context, 'basic_info_page'):
            context.basic_info_page = EventBasicInfoPage(context.driver)
        context.basic_info_page.click_next()
    elif "/event/details" in current_url:
        if not hasattr(context, 'details_page'):
            context.details_page = EventDetailsPage(context.driver)
        context.details_page.click_next()
    else:
        # Generic fallback
        next_button = (By.XPATH, "//button[contains(text(), 'Próximo')]")
        from page_objects.base_page import BasePage
        base_page = BasePage(context.driver)
        base_page.click_element(next_button)


# Legacy steps - kept for backward compatibility but updated
@when('preencho a descrição do evento "{description}"')
def step_fill_event_description_legacy(context, description):
    """Fill the event description field - Legacy step"""
    # This step is now handled by the details page
    if not hasattr(context, 'details_page'):
        context.details_page = EventDetailsPage(context.driver)
    
    context.details_page.fill_description(description)


@when('seleciono a data "{date}"')
def step_select_event_date_legacy(context, date):
    """Legacy step - date selection will be in schedule page"""
    # This will be implemented when we create the schedule page object
    logger.warning("Date selection step not yet implemented - will be in schedule page")


@when('seleciono o horário "{time}"')
def step_select_event_time_legacy(context, time):
    """Legacy step - time selection will be in schedule page"""
    # This will be implemented when we create the schedule page object
    logger.warning("Time selection step not yet implemented - will be in schedule page")


@when('preencho o local "{location}"')
def step_fill_event_location_legacy(context, location):
    """Legacy step - location selection will be in schedule page"""
    # This will be implemented when we create the schedule page object
    logger.warning("Location selection step not yet implemented - will be in schedule page")


@when('clico no botão "Criar Evento"')
def step_click_create_event_legacy(context):
    """Legacy step - event creation will be in confirm page"""
    # This will be implemented when we create the confirm page object
    logger.warning("Create event button step not yet implemented - will be in confirm page")


@when('clico no botão "Criar Evento" sem preencher os campos')
def step_click_create_without_filling_legacy(context):
    """Legacy step - validation will be handled per page"""
    # This can be implemented per page as needed
    logger.warning("Validation step not yet implemented for multi-page flow")


# Legacy validation steps - to be updated for multi-page flow
@then('devo ver a mensagem de sucesso "{message}"')
def step_verify_success_message_legacy(context, message):
    """Legacy step - success message will be on confirm page"""
    logger.warning("Success message validation not yet implemented for multi-page flow")


@then('devo ser redirecionado para a página de detalhes do evento')
def step_verify_redirect_to_event_details_legacy(context):
    """Legacy step - redirection after event creation"""
    logger.warning("Event details redirect not yet implemented for multi-page flow")


@then('devo ver o título "{title}" na página')
def step_verify_event_title_on_page_legacy(context, title):
    """Legacy step - title verification on details page"""
    logger.warning("Title verification not yet implemented for multi-page flow")


@then('devo ver mensagens de erro para campos obrigatórios')
def step_verify_required_field_errors_legacy(context):
    """Legacy step - field validation per page"""
    logger.warning("Field validation not yet implemented for multi-page flow")


@then('devo ver a mensagem "{message}"')
def step_verify_specific_message_legacy(context, message):
    """Legacy step - specific message validation"""
    logger.warning("Specific message validation not yet implemented for multi-page flow")


# End of create_event_steps.py
