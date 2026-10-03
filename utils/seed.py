"""Seed and clean data the UI cannot create by itself (the server owns event statuses).

Used only for the isolated E2E account, on a throwaway database, and only for ids the
scenario created: a seeded event is removed by its own id in ``after_scenario``.
"""
import os
import re
from datetime import datetime

from bson import ObjectId
from pymongo import MongoClient
from pymongo.uri_parser import parse_uri

# Seeding writes straight to Mongo, so it refuses anything that is not the local stack's database
# and anything that is not the isolated E2E account: one wrong variable must not reach Atlas.
LOCAL_HOSTS = frozenset({"mongo", "localhost", "127.0.0.1"})
DEFAULT_ISOLATED_ACCOUNT = "e2e-ci@udf.edu.br"


class UnsafeSeedTarget(RuntimeError):
    """The seed was asked to write somewhere or for someone the isolated E2E run may not touch."""


def assert_local_uri(uri: str) -> None:
    """Refuse a URI unless every host is the local stack's. There is no override: no remote seeding is supported."""
    try:
        parsed = parse_uri(uri, validate=False)
    except Exception as error:  # an unparsable URI is not a local one
        raise UnsafeSeedTarget("E2E_MONGO_URI is not a valid MongoDB URI") from error
    if parsed.get("is_srv"):
        raise UnsafeSeedTarget("refusing a mongodb+srv URI: the E2E seed only writes to the local stack")
    hosts = {host for host, _port in parsed["nodelist"]}
    remote = sorted(hosts - LOCAL_HOSTS)
    if not hosts or remote:
        raise UnsafeSeedTarget(
            f"refusing to seed host(s) {remote or sorted(hosts)}: only {sorted(LOCAL_HOSTS)} are allowed")


def isolated_account() -> str:
    """The only account the seed may write for: pinned, never taken from the environment."""
    return DEFAULT_ISOLATED_ACCOUNT


def assert_suite_account_is_the_isolated_one() -> None:
    """Refuse to seed or delete when the run logs in with another account (TEST_EMAIL differs)."""
    configured = (os.getenv("TEST_EMAIL") or DEFAULT_ISOLATED_ACCOUNT).strip().casefold()
    if configured != DEFAULT_ISOLATED_ACCOUNT:
        raise UnsafeSeedTarget(
            "refusing to seed: TEST_EMAIL is not the isolated E2E account the seed is pinned to")


def is_isolated_account(email) -> bool:
    """Exact, case-insensitive match with the pinned address; never a prefix or a pattern."""
    return isinstance(email, str) and email.strip().casefold() == isolated_account()


def assert_isolated_account(email: str) -> None:
    assert_suite_account_is_the_isolated_one()
    if not is_isolated_account(email):
        raise UnsafeSeedTarget("refusing to seed for an account that is not the suite's isolated E2E account")


def _db():
    uri = os.getenv("E2E_MONGO_URI", "mongodb://mongo:27017")
    assert_local_uri(uri)
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return client[os.getenv("E2E_MONGO_DATABASE", "rooms-reservation-app")]


def seed_requested_change_event(email: str, message: str) -> str:
    """Insert one event of ``email`` in status requested_change, as the Coordenação's action leaves it."""
    assert_isolated_account(email)
    event = {
        "_id": ObjectId(),
        "name": "Evento E2E com alterações solicitadas",
        "organizer": {"name": email.split("@")[0], "email": email, "phone": ""},
        "eventTypeId": "lecture",
        "odsId": "1",
        "subscriptionLink": "",
        "description": "Evento sintético do E2E; removido ao fim do cenário.",
        "graduationId": "",
        "targetPublic": [],
        "resources": [],
        "expectedSubscribers": "30",
        "roomType": [],
        "entrepreneuralPath": "",
        "extensionProject": "",
        "studentsMonitors": [],
        "eventLogo": "",
        "status": "requested_change",
        "changeRequest": {
            "message": message,
            "requestedAt": datetime.now().isoformat(timespec="seconds"),
            "by": "coordenacao",
        },
    }
    _db().events.insert_one(event)
    return str(event["_id"])


def delete_events(event_ids) -> int:
    assert_suite_account_is_the_isolated_one()
    ids = [ObjectId(i) for i in event_ids]
    if not ids:
        return 0
    db = _db()
    # by id AND only events of the isolated account, so a stray id can never remove someone's event
    owned = {"_id": {"$in": ids},
             "organizer.email": {"$regex": f"^{re.escape(isolated_account())}$", "$options": "i"}}
    kept = [str(e["_id"]) for e in db.events.find(owned, {"_id": 1})]
    db.reservations.delete_many({"eventId": {"$in": kept}})
    db.pdfs.delete_many({"eventId": {"$in": kept}})  # the PDF a submitted lecture generates
    db.send_email.delete_many({"eventId": {"$in": kept}})  # the approval links issued for the event
    return db.events.delete_many(owned).deleted_count


def account_events(email: str) -> dict:
    """Events of the isolated account as {id: status}, to compare before and after a scenario."""
    assert_isolated_account(email)
    query = {"organizer.email": {"$regex": f"^{re.escape(isolated_account())}$", "$options": "i"}}
    return {str(e["_id"]): e.get("status") for e in _db().events.find(query, {"status": 1})}


def any_room_id() -> str:
    """Id of a room already in the local catalog, for scenarios that submit a real reservation."""
    room = _db().rooms.find_one({}, {"_id": 1})
    assert room, "the local database has no room to reserve"
    return str(room["_id"])


def coordination_link_token(event_id: str, action: str) -> str:
    """The active token the Coordenação's e-mail carries for ``action`` on ``event_id`` (the e-mail is a dry run)."""
    record = _db().send_email.find_one({"eventId": event_id, "step": 0, "action": action, "active": True})
    assert record, f"no active '{action}' link was issued for event {event_id}"
    return record["tokenId"]


def event_state(event_id: str) -> dict:
    """Status of the event and how many reservations it holds."""
    db = _db()
    event = db.events.find_one({"_id": ObjectId(event_id)}, {"status": 1})
    return {"status": (event or {}).get("status"), "reservations": db.reservations.count_documents({"eventId": event_id})}


def any_course_id() -> str:
    """Id of a course already in the local catalog, so the Coordenação's e-mail can look its coordinator up."""
    course = _db().courses.find_one({}, {"_id": 1})
    assert course, "the local database has no course"
    return str(course["_id"])
