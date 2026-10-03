"""The Coordenação's request for changes, end to end (API #80/#81 and Web #51): real submit, real link, real notice."""
import random

import requests
from behave import given, when, then

from features.steps.drafts_resilience_steps import DRAFT_FORM
from features.steps.logged_in_steps import stored
from utils.seed import any_course_id, any_room_id, coordination_link_token, event_state

# The fields the Web form sends for a lecture, so the PDF and the Coordenação's e-mail can be built from it.
EVENT = {**DRAFT_FORM, "tituloEvento": "Evento E2E de pedido de alterações", "status": "draft"}


def api(context):
    return context.config.userdata.get("API_URL", "http://localhost:5000")


def session_headers(context):
    return {"token": stored(context, "token"), "email": stored(context, "userEmail")}


def submit(context):
    body = {**context.event_body, "roomId": context.room_id, "reservationDate": context.reservation_date}
    return requests.post(f"{api(context)}/events/{context.change_event}/submit", json=body,
                         headers=session_headers(context), timeout=60)


@given("envio um pedido real e a Coordenação pede alterações pelo link do e-mail com o motivo \"{message}\"")
def step_request_changes(context, message):
    context.event_body = {**EVENT, "courseId": any_course_id()}
    created = requests.post(f"{api(context)}/events", json=context.event_body, headers=session_headers(context), timeout=30)
    assert created.status_code == 200, (created.status_code, created.text[:200])
    context.change_event = created.json()["eventId"]
    context.room_id = any_room_id()
    # a far-off day, picked at random, so a leftover reservation never collides with this one
    context.reservation_date = f"20{random.randint(40, 60)}-0{random.randint(1, 9)}-{random.randint(10, 28)}T10:00:00.000Z"
    first = submit(context)
    assert first.status_code == 200, (first.status_code, first.text[:200])
    assert event_state(context.change_event) == {"status": "waiting", "reservations": 1}
    token = coordination_link_token(context.change_event, "request_changes")
    # the link in the e-mail opens a confirmation page whose form posts the reason
    page = requests.post(f"{api(context)}/request_changes",
                         data={"eventId": context.change_event, "tokenId": token, "message": message}, timeout=30)
    assert page.status_code == 200, (page.status_code, page.text[:200])
    context.change_message = message
    assert event_state(context.change_event)["status"] == "requested_change"


@when("reenvio o pedido corrigido")
def step_resubmit(context):
    context.resubmit = submit(context)


@then("o pedido volta a aguardar a Coordenação com uma única reserva")
def step_resubmitted(context):
    assert context.resubmit.status_code == 200, (context.resubmit.status_code, context.resubmit.text[:200])
    assert event_state(context.change_event) == {"status": "waiting", "reservations": 1}
