"""Seed and clean data the UI cannot create by itself (the server owns event statuses).

Used only for the isolated E2E account, on a throwaway database, and only for ids the
scenario created: a seeded event is removed by its own id in ``after_scenario``.
"""
import os
from datetime import datetime

from bson import ObjectId
from pymongo import MongoClient


def _db():
    client = MongoClient(os.getenv("E2E_MONGO_URI", "mongodb://mongo:27017"), serverSelectionTimeoutMS=5000)
    return client[os.getenv("E2E_MONGO_DATABASE", "rooms-reservation-app")]


def seed_requested_change_event(email: str, message: str) -> str:
    """Insert one event of ``email`` in status requested_change, as the Coordenação's action leaves it."""
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
    ids = [ObjectId(i) for i in event_ids]
    if not ids:
        return 0
    db = _db()
    db.reservations.delete_many({"eventId": {"$in": [str(i) for i in ids]}})
    return db.events.delete_many({"_id": {"$in": ids}}).deleted_count
