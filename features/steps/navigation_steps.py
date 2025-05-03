from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from utils.helpers import wait_for_page_load


@when('navego para "{url}"')
def step_impl_navigate_to_url(context, url):
    """Navigate to the specified URL."""
    # Handle relative URLs
    if not url.startswith(('http://', 'https://')):
        base_url = context.config.userdata.get('BASE_URL', 'localhost:3000')
        if not base_url.startswith(('http://', 'https://')):
            base_url = f'http://{base_url}'
        url = f"{base_url}{url if url.startswith('/') else '/' + url}"
    
    context.driver.get(url)
    wait_for_page_load(context.driver)


@then('devo estar na página "{url_part}"')
def step_impl_verify_url(context, url_part):
    """Verify that the current URL contains the specified part."""
    current_url = context.driver.current_url
    assert url_part in current_url, f"Current URL '{current_url}' doesn't contain '{url_part}'"


@then('devo ver o elemento "{element_identifier}"')
def step_impl_verify_element_visible(context, element_identifier):
    """Verify that an element is visible on the page."""
    # This is a simple implementation; in a real project, you might have a mapping
    # of friendly names to locators
    
    # Try different locator strategies
    locators = [
        (By.ID, element_identifier),
        (By.CSS_SELECTOR, element_identifier),
        (By.XPATH, f"//*[contains(text(), '{element_identifier}')]"),
        (By.LINK_TEXT, element_identifier)
    ]
    
    for locator in locators:
        try:
            if context.current_page.is_element_visible(locator):
                return True
        except:
            continue
    
    assert False, f"Element '{element_identifier}' not found on page"


@when('aguardo {seconds:d} segundos')
def step_impl_wait_seconds(context, seconds):
    """Wait for the specified number of seconds."""
    import time
    time.sleep(seconds)


@then('o título da página deve conter "{text}"')
def step_impl_verify_page_title(context, text):
    """Verify that the page title contains the specified text."""
    title = context.driver.title
    assert text in title, f"Page title '{title}' doesn't contain '{text}'"