import os
import re
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

    def test_no_environment_variable_turns_the_host_guard_off(self):
        for value in ("1", "true", "yes"):
            with patch.dict(os.environ, {"E2E_ALLOW_REMOTE_SEED": value}):
                with self.assertRaises(UnsafeSeedTarget, msg=value):
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
        with patch.dict(os.environ, {}, clear=False) as env, patch("utils.seed.MongoClient") as client:
            env.pop("TEST_EMAIL", None)
            for email in ("pessoa@udf.edu.br", "coordenacao@udf.edu.br", "ce2e-ci@udf.edu.br", "",
                          None, "e2e-ci2@udf.edu.br", "e2e-ci@outro.edu.br", "e2e-ci@udf.edu.br.evil.test",
                          "e2e-ci+x@udf.edu.br", "e2e-ci@udf.edu.brx"):
                with self.assertRaises(UnsafeSeedTarget, msg=str(email)):
                    seed.seed_requested_change_event(email, "x")
            client.assert_not_called()

    def test_the_account_is_the_one_the_login_steps_use(self):
        with patch.dict(os.environ, {"TEST_EMAIL": "Outra-Conta@udf.edu.br"}), patch("utils.seed.MongoClient") as client:
            with self.assertRaises(UnsafeSeedTarget):
                seed.seed_requested_change_event("e2e-ci@udf.edu.br", "x")
            client.assert_not_called()
            self.assertTrue(seed.is_isolated_account("outra-conta@UDF.edu.br"))

    def test_the_match_ignores_case_only(self):
        with patch.dict(os.environ, {}) as env:
            env.pop("TEST_EMAIL", None)
            self.assertTrue(seed.is_isolated_account("E2E-CI@Udf.Edu.Br"))
            self.assertFalse(seed.is_isolated_account("e2e-ci@udf.edu.brx"))

    def test_delete_matches_the_exact_address_not_a_pattern(self):
        with patch.dict(os.environ, {"E2E_MONGO_URI": "mongodb://mongo:27017"}) as env, \
                patch("utils.seed.MongoClient") as client:
            env.pop("TEST_EMAIL", None)
            db = client.return_value.__getitem__.return_value
            db.events.find.return_value = []
            seed.delete_events(["507f1f77bcf86cd799439011"])
            condition = db.events.find.call_args.args[0]["organizer.email"]
            self.assertEqual(condition["$regex"], r"^e2e\-ci@udf\.edu\.br$")
            self.assertEqual(condition["$options"], "i")
            self.assertTrue(re.match(condition["$regex"], "E2E-ci@udf.edu.br", re.I))
            for other in ("e2e-ci@outro.edu.br", "e2e-cixudf.edu.br", "e2e-ci2@udf.edu.br", "xe2e-ci@udf.edu.br"):
                self.assertIsNone(re.match(condition["$regex"], other, re.I), other)

    def test_the_isolated_account_is_accepted(self):
        with patch.dict(os.environ, {"E2E_MONGO_URI": "mongodb://mongo:27017"}), \
                patch("utils.seed.MongoClient") as client:
            seed.seed_requested_change_event("e2e-ci@udf.edu.br", "x")
            client.return_value.__getitem__.return_value.events.insert_one.assert_called_once()


if __name__ == "__main__":
    unittest.main()
