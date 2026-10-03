import os
import unittest
from unittest.mock import patch

from utils import seed
from utils.seed import UnsafeSeedTarget


class SeedTargetGuardTests(unittest.TestCase):
    def test_local_hosts_are_accepted(self):
        for uri in ("mongodb://mongo:27017", "mongodb://localhost:27017/db", "mongodb://127.0.0.1"):
            seed.assert_local_uri(uri)

    def test_remote_hosts_are_refused(self):
        for uri in (
            "mongodb://db.example.test:27017",
            "mongodb://mongo,evil.example.test:27017",       # one local host does not excuse another
            "mongodb+srv://cluster0.example.mongodb.net/db",  # Atlas-style SRV
            "mongodb://user:pw@mongo.evil.test/db",
            "not a uri",
        ):
            with self.assertRaises(UnsafeSeedTarget, msg=uri):
                seed.assert_local_uri(uri)

    def test_the_explicit_override_is_the_only_way_out(self):
        with patch.dict(os.environ, {"E2E_ALLOW_REMOTE_SEED": "1"}):
            seed.assert_local_uri("mongodb://db.example.test:27017")
        with patch.dict(os.environ, {"E2E_ALLOW_REMOTE_SEED": "true"}):
            with self.assertRaises(UnsafeSeedTarget):
                seed.assert_local_uri("mongodb://db.example.test:27017")

    def test_a_remote_uri_never_opens_a_connection(self):
        with patch.dict(os.environ, {"E2E_MONGO_URI": "mongodb+srv://cluster0.example.mongodb.net"}), \
                patch("utils.seed.MongoClient") as client:
            with self.assertRaises(UnsafeSeedTarget):
                seed.seed_requested_change_event("e2e-ci@udf.edu.br", "x")
            with self.assertRaises(UnsafeSeedTarget):
                seed.delete_events(["507f1f77bcf86cd799439011"])
            client.assert_not_called()

    def test_only_the_isolated_account_can_be_seeded(self):
        with patch("utils.seed.MongoClient") as client:
            for email in ("pessoa@udf.edu.br", "coordenacao@udf.edu.br", "ce2e-ci@udf.edu.br", "", None):
                with self.assertRaises(UnsafeSeedTarget, msg=str(email)):
                    seed.seed_requested_change_event(email, "x")
            client.assert_not_called()

    def test_the_isolated_account_is_accepted(self):
        with patch.dict(os.environ, {"E2E_MONGO_URI": "mongodb://mongo:27017"}), \
                patch("utils.seed.MongoClient") as client:
            seed.seed_requested_change_event("e2e-ci@udf.edu.br", "x")
            client.return_value.__getitem__.return_value.events.insert_one.assert_called_once()


if __name__ == "__main__":
    unittest.main()
