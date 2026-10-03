"""Steps of the Drafts that need two browser tabs or a service going down (Web #42, #47, #53)."""
import json
import logging
import os
import time
from urllib.parse import parse_qs, urlparse

import requests
from behave import given, when, then
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from features.steps.logged_in_steps import _SESSION, base_url, wait
from utils import service_control
from utils.seed import account_events

logger = logging.getLogger(__name__)

NOTICE_TEXT = "não conseguimos confirmar o encerramento da sessão no servidor"
# Fields the logistics, schedule and confirmation steps need so that a lecture can be submitted.
DRAFT_FORM = {
    "tituloEvento": "Evento E2E de duas abas", "telefone": "61999999999", "classificacao": "lecture",
    "ods": "1", "odsId": "1", "descricaoEvento": "Evento sintético do E2E; removido ao fim do cenário.",
    "publicoAlvo": [], "recursosNecessarios": [], "numeroParticipantes": "30", "espacos": "salaAula",
    "trilha": "nao", "projeto": "nao",
}


def eid(url):
    return (parse_qs(urlparse(url).query).get("eventId") or [""])[0]


def tab_on_path(context, handle, path, timeout=20):
    context.driver.switch_to.window(handle)
    wait(context, lambda d: path in urlparse(d.current_url).path, timeout=timeout,
         message=f"not on {path}: {context.driver.current_url}")


def press(context, element):
    """Click after centring; if a fixed bar still covers it, click through the DOM (same handler)."""
    context.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    try:
        element.click()
    except ElementClickInterceptedException:
        context.driver.execute_script("arguments[0].click();", element)


def click_next(context, handle):
    context.driver.switch_to.window(handle)
    button = wait(context, EC.element_to_be_clickable((By.XPATH, "//button[normalize-space(.)='Próximo']")))
    press(context, button)


def created(context):
    """Events the scenario created: what the account owns now minus the baseline taken at the start."""
    return {i: s for i, s in account_events(context.email).items() if i not in context.event_baseline}


@given("a conta isolada não tem pedido em andamento")
def step_baseline(context):
    context.event_baseline = set(account_events(context.email))


@given("abro a etapa de logística em duas abas sem rascunho")
def step_two_tabs(context):
    driver = context.driver
    driver.get(f"{base_url(context)}/event/mine")  # an origin to hold the storage
    driver.execute_script(
        "window.localStorage.removeItem('eventId'); window.localStorage.setItem('formData', arguments[0]);",
        json.dumps(DRAFT_FORM))
    context.tabs = {"first": driver.current_window_handle}
    driver.get(f"{base_url(context)}/event/logistics")
    driver.switch_to.new_window("tab")
    context.tabs["second"] = driver.current_window_handle
    driver.get(f"{base_url(context)}/event/logistics")
    for handle in context.tabs.values():
        driver.switch_to.window(handle)
        wait(context, EC.presence_of_element_located((By.XPATH, "//button[normalize-space(.)='Próximo']")),
             message="logistics step did not open (session lost?)")
    assert not driver.execute_script("return window.localStorage.getItem('eventId');"), "a draft id was already stored"


@when("avanço na primeira aba e depois na segunda")
def step_advance_both(context):
    # Both tabs hold no eventId in their state. The click on the second one follows at once, while the
    # first request may still be in flight: that is what two people-tabs advancing together look like.
    click_next(context, context.tabs["first"])
    click_next(context, context.tabs["second"])
    for handle in context.tabs.values():
        tab_on_path(context, handle, "/event/schedule", timeout=30)


@when("avanço na primeira aba")
def step_advance_first(context):
    click_next(context, context.tabs["first"])
    tab_on_path(context, context.tabs["first"], "/event/schedule", timeout=30)
    context.first_draft = eid(context.driver.current_url)
    assert context.first_draft, "the first tab advanced without a draft id"


@when("envio o pedido pela primeira aba")
def step_submit_first(context):
    driver = context.driver
    driver.switch_to.window(context.tabs["first"])
    driver.find_element(By.XPATH, "//input[@type='radio' and @value='Manha']").click()
    room = wait(context, EC.element_to_be_clickable((By.CSS_SELECTOR, ".room-card")), message="no room listed")
    room.click()
    proceed = wait(context, EC.element_to_be_clickable((By.XPATH, "//button[normalize-space(.)='Continuar']")))
    press(context, proceed)
    tab_on_path(context, context.tabs["first"], "/event/confirm-data")
    confirm = wait(context, EC.element_to_be_clickable((By.XPATH, "//button[normalize-space(.)='Confirmar']")))
    press(context, confirm)
    tab_on_path(context, context.tabs["first"], "/event/confirmation", timeout=40)
    assert not driver.execute_script("return window.localStorage.getItem('eventId');"), \
        "the stored draft id survived the final submit"


@when("avanço na segunda aba")
def step_advance_second(context):
    click_next(context, context.tabs["second"])
    time.sleep(0)  # the outcome is asserted by the Then steps


@then("as duas abas devem estar na agenda do mesmo rascunho")
def step_same_draft(context):
    ids = {}
    for name, handle in context.tabs.items():
        context.driver.switch_to.window(handle)
        ids[name] = eid(context.driver.current_url)
    assert ids["first"] and ids["first"] == ids["second"], f"the tabs hold different drafts: {ids}"
    context.first_draft = ids["first"]


@then("a segunda aba deve estar na agenda de um rascunho diferente do enviado")
def step_second_new_draft(context):
    handle = context.tabs["second"]
    try:
        tab_on_path(context, handle, "/event/schedule", timeout=30)
    except TimeoutException:
        raise AssertionError(f"the second tab did not advance (409 on the submitted draft?): {context.driver.current_url}")
    context.second_draft = eid(context.driver.current_url)
    assert context.second_draft and context.second_draft != context.first_draft, \
        f"the second tab reused the submitted draft: {context.second_draft}"


@then("a conta deve ter exatamente {count:d} rascunho novo")
def step_draft_count(context, count):
    drafts = [i for i, s in created(context).items() if s == "draft"]
    assert len(drafts) == count, f"expected {count} new draft(s), found {len(drafts)}: {created(context)}"


@then("a conta deve ter {sent:d} pedido enviado e {drafts:d} rascunho novo")
def step_sent_and_draft(context, sent, drafts):
    statuses = list(created(context).values())
    found_drafts = statuses.count("draft")
    found_sent = len(statuses) - found_drafts
    assert (found_sent, found_drafts) == (sent, drafts), f"expected {sent} sent + {drafts} draft, found {statuses}"


# ---- #42: room list with the API down -------------------------------------------------------------

@given("abro a agenda com a lista de salas carregada")
def step_open_schedule(context):
    driver = context.driver
    context.api_url = context.config.userdata["API_URL"]
    context.event_baseline = set(account_events(context.email))
    driver.get(f"{base_url(context)}/event/schedule?eventId={'0' * 24}")
    press(context, wait(context, EC.element_to_be_clickable((By.XPATH, "//input[@type='radio' and @value='Manha']"))))
    wait(context, EC.presence_of_element_located((By.CSS_SELECTOR, ".room-card")), message="no room listed")


def stop_service(context, service):
    service_control.stop(service)
    context.stopped_services = getattr(context, "stopped_services", []) + [service]


def start_service(context, service):
    service_control.restart(service, context.config.userdata["API_URL"])
    context.stopped_services.remove(service)


@when("a API fica fora do ar")
def step_api_down(context):
    stop_service(context, "api")


@when("a API volta ao ar")
def step_api_up(context):
    start_service(context, "api")


@when("mudo o período da agenda")
def step_change_period(context):
    """Pick another period. A request that reuses a connection the stopped API left half-open can hang
    instead of failing, as a real network does; the person then picks another period, and so does this."""
    for value in ("Tarde", "Noite", "Manha", "Tarde"):
        press(context, context.driver.find_element(By.XPATH, f"//input[@type='radio' and @value='{value}']"))
        try:
            wait(context, EC.visibility_of_element_located(ALERT), timeout=12)
            return
        except TimeoutException:
            logger.info("no alert yet after choosing %s; trying another period", value)


ALERT = (By.CSS_SELECTOR, ".error-message[role='alert']")


@then('devo ver o alerta da lista de salas com o botão "{label}"')
def step_alert_with_retry(context, label):
    try:
        alert = wait(context, EC.visibility_of_element_located(ALERT), timeout=40)
    except TimeoutException:
        body = context.driver.find_element(By.TAG_NAME, "body").text[-300:].replace("\n", " | ")
        raise AssertionError(f"the room list showed no alert after the API went down; page ends: {body}")
    assert alert.find_elements(By.XPATH, f".//button[normalize-space(.)='{label}']"), \
        f"the alert has no '{label}' button: {alert.text!r}"


@then("a lista deve mostrar salas e nenhum alerta")
def step_rooms_back(context):
    wait(context, EC.presence_of_element_located((By.CSS_SELECTOR, ".room-card")),
         message="the retry did not bring the rooms back")
    assert not context.driver.find_elements(*ALERT), "the alert is still on screen"


# ---- #53: Sair with the Auth down -------------------------------------------------------------------

def session_status(context):  # the kept session as the API sees it, or None when unreachable
    headers = {"token": _SESSION.get("token", ""), "email": _SESSION.get("userEmail", "")}
    try:
        return requests.get(f"{context.config.userdata['API_URL']}/auth/validate", headers=headers, timeout=5).status_code
    except requests.RequestException:
        return None


@given("o Auth está fora do ar")
def step_auth_down(context):
    logger.info("kept session status before stopping the Auth: %s", session_status(context))
    stop_service(context, "auth")


@then("a tela de login deve avisar que o encerramento não foi confirmado")
def step_notice_shown(context):
    try:
        notice = wait(context, EC.visibility_of_element_located(
            (By.XPATH, f"//*[@role='status' and contains(normalize-space(.), '{NOTICE_TEXT}')]")), timeout=15)
    except TimeoutException:
        body = context.driver.find_element(By.TAG_NAME, "body").text[:300].replace("\n", " | ")
        state = context.driver.execute_script("return JSON.stringify(window.history.state);")
        raise AssertionError(f"no status notice after Sair with the Auth down at {context.driver.current_url}; "
                             f"history.state={state}; page: {body}")


@then("a tela de login não deve avisar sobre o encerramento")
def step_notice_absent(context):
    time.sleep(1)  # the notice, if any, is rendered with the page
    assert NOTICE_TEXT not in context.driver.find_element(By.TAG_NAME, "body").text, "the notice is shown after a confirmed logout"


@then("o Auth volta ao ar")
def step_auth_up(context):
    start_service(context, "auth")
    # The browser gave up after a few seconds, but the API keeps retrying the Auth for a while; if that
    # retry lands after the Auth is back, the session is revoked anyway. The next scenario then needs a
    # new login, so forget the shared session unless the Auth still validates it.
    time.sleep(5)
    if session_status(context) != 200:
        logger.info("the kept session no longer validates; the next scenario logs in again")
        _SESSION.clear()
