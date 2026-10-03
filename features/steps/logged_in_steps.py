import logging
import os
import time
from urllib.parse import urlparse

import requests
from behave import given, when, then
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from page_objects.login_page import LoginPage
from utils.helpers import get_magic_link, rebase_magic_link
from utils.seed import seed_requested_change_event

logger = logging.getLogger(__name__)

SAIR_LOCATOR = (By.XPATH, "//button[normalize-space(.)='Sair']")
NOTICE_HEADING = "A Coordenação pediu alterações."


def base_url(context):
    url = context.config.userdata.get("BASE_URL", "localhost:3000")
    return url if url.startswith(("http://", "https://")) else f"http://{url}"


def wait(context, condition, timeout=20, message=""):
    return WebDriverWait(context.driver, timeout).until(condition, message)


def stored(context, key):
    return context.driver.execute_script("return window.localStorage.getItem(arguments[0]);", key)


# One real login per run: the Auth allows 3 link requests per e-mail per 15 minutes, so a login per
# scenario would be refused. The first scenario logs in through the real link flow (magic link from
# the API, "Entrar" click); later ones, which start in a new browser, restore that session's own
# localStorage entries instead of asking for another link.
_SESSION = {}


@given('que estou logado como "{email}"')
def step_logged_in(context, email):
    test_email = os.getenv("TEST_EMAIL", email)
    context.email = test_email
    context.login_page = LoginPage(context.driver)
    if _SESSION:
        context.driver.get(f"{base_url(context)}/organizer")  # an origin to hold the storage
        context.driver.execute_script(
            "for (const [k, v] of Object.entries(arguments[0])) window.localStorage.setItem(k, v);", _SESSION)
        context.driver.get(f"{base_url(context)}/event/mine")
        wait(context, EC.presence_of_element_located(
            (By.XPATH, "//*[(self::h1 or self::h2) and normalize-space(.)='Meus Eventos']")),
            message="the stored session did not open /event/mine")
        return
    link = get_magic_link(test_email)
    assert link, "the API did not return a magic link (rate limit reached or e-mail provider active?)"
    context.driver.get(rebase_magic_link(link, base_url(context)))
    context.login_page.click_enter_on_callback()
    assert context.login_page.wait_for_session_token(), "no session token after Entrar"
    assert context.login_page.is_redirected_to_events_page(), context.driver.current_url
    _SESSION.update(context.driver.execute_script("return Object.assign({}, window.localStorage);"))


@when('clico em "{label}"')
def step_click_label(context, label):
    locator = (By.XPATH, f"//button[normalize-space(.)='{label}'] | //a[normalize-space(.)='{label}']")
    element = wait(context, EC.element_to_be_clickable(locator), message=f"'{label}' not clickable")
    # long pages: bring it to the middle of the viewport so a fixed bar cannot cover it
    context.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    element.click()


@then('devo ser levado para a página "{path}"')
def step_taken_to_path(context, path):
    wait(context, lambda d: path in urlparse(d.current_url).path, message=f"not on {path}: {context.driver.current_url}")


@then("a sessão não deve mais existir no localStorage")
def step_session_gone(context):
    assert stored(context, "token") is None, "the session token is still stored"
    assert stored(context, "userEmail") is None, "the stored e-mail is still there"


@then("uma rota privada deve me mandar embora ao abri-la")
def step_private_route_redirects(context):
    context.driver.get(f"{base_url(context)}/event/mine")
    try:
        wait(context, lambda d: "/event/mine" not in d.current_url, timeout=15)
    except TimeoutException:
        raise AssertionError("a private route stayed open after logging out")
    assert not context.driver.find_elements(By.XPATH, "//*[self::h1 or self::h2][normalize-space(.)='Meus Eventos']")


@then('devo ver o indicador "{text}"')
def step_step_indicator(context, text):
    locator = (By.XPATH, f"//*[@role='progressbar' and starts-with(@aria-label, '{text}')]")
    try:
        wait(context, EC.presence_of_element_located(locator), message=text)
    except TimeoutException:
        raise AssertionError(f"'{text}' not shown at {context.driver.current_url}")
    visible = context.driver.find_elements(By.XPATH, f"//*[contains(normalize-space(.), '{text}')]")
    assert visible, f"the text '{text}' is not on the page"


@given('existe um evento meu em "{status}" com o motivo "{message}"')
def step_seed_event(context, status, message):
    assert status == "requested_change", "only requested_change is seeded"
    context.seeded_event_ids = getattr(context, "seeded_event_ids", [])
    context.seeded_event_ids.append(seed_requested_change_event(context.email, message))
    context.change_message = message
    logger.info("Seeded event %s for %s", context.seeded_event_ids[-1], context.email)


@when("abro Meus Eventos")
def step_open_my_events(context):
    context.driver.get(f"{base_url(context)}/event/mine")
    wait(context, EC.presence_of_element_located(
        (By.XPATH, "//*[(self::h1 or self::h2) and normalize-space(.)='Meus Eventos']")))


@then("devo ver o aviso de alterações com o motivo como texto")
def step_change_notice(context):
    locator = (By.XPATH, f"//*[@role='alert' and contains(normalize-space(.), '{NOTICE_HEADING}')]")
    notice = wait(context, EC.visibility_of_element_located(locator), message="no change-request notice")
    assert context.change_message in notice.text, f"the reason is not shown as text: {notice.text!r}"
    assert not notice.find_elements(By.XPATH, ".//b"), "the reason was rendered as markup, not as text"


@then('devo estar no fluxo de edição do evento semeado')
def step_edit_flow(context):
    event_id = context.seeded_event_ids[-1]
    wait(context, lambda d: "/event/type-selection" in d.current_url and f"eventId={event_id}" in d.current_url,
         message=f"not in the edit flow of {event_id}: {context.driver.current_url}")


@given("guardo o token e o e-mail da sessão")
def step_keep_session(context):
    context.kept_session = {"token": stored(context, "token"), "email": stored(context, "userEmail")}
    assert context.kept_session["token"] and context.kept_session["email"], "no session to keep"


@then("a API deve recusar o token guardado")
def step_api_refuses_kept_token(context):
    """After Sair the server itself must reject the old token (not only the browser forget it)."""
    api = context.config.userdata.get("API_URL", "http://localhost:5000")
    kept = context.kept_session
    headers = {"token": kept["token"], "email": kept["email"]}
    # the logout call is made by the app before it navigates; give the Auth a moment to settle
    status = None
    for _ in range(10):
        status = requests.get(f"{api}/auth/validate", headers=headers, timeout=15).status_code
        if status == 403:
            break
        time.sleep(0.5)
    _SESSION.clear()  # the shared session is gone for later scenarios, which must log in again
    assert status == 403, f"the API still accepts the old session token (status {status})"


@when("pressiono Enter no campo de email")
def step_press_enter_in_email(context):
    context.driver.find_element(*context.login_page.email_input).send_keys(Keys.ENTER)
