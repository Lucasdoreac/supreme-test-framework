import os
import unittest
from unittest.mock import patch

from utils import seed, service_control
from utils.service_control import ServiceControlUnavailable


class ServiceControlGuardTests(unittest.TestCase):
    """The resilience scenarios may stop the API or the Auth, and nothing else, only on request."""

    def test_refuses_without_the_opt_in(self):
        with patch.dict(os.environ, {"E2E_COMPOSE_PROJECT": "labtech-dev"}, clear=False):
            os.environ.pop("E2E_ALLOW_SERVICE_CONTROL", None)
            with self.assertRaises(ServiceControlUnavailable):
                service_control.stop("api")

    def test_refuses_services_outside_the_allowlist(self):
        env = {"E2E_ALLOW_SERVICE_CONTROL": "1", "E2E_COMPOSE_PROJECT": "labtech-dev"}
        with patch.dict(os.environ, env), patch("os.path.exists", return_value=True):
            for service in ("mongo", "redis", "reservas", "internal", "../api"):
                with self.assertRaises(ValueError, msg=service):
                    service_control.stop(service)

    def test_refuses_without_a_compose_project(self):
        with patch.dict(os.environ, {"E2E_ALLOW_SERVICE_CONTROL": "1"}), patch("os.path.exists", return_value=True):
            os.environ.pop("E2E_COMPOSE_PROJECT", None)
            with self.assertRaises(ServiceControlUnavailable):
                service_control.stop("auth")

    def test_allowlist_is_only_api_and_auth(self):
        self.assertEqual(service_control.ALLOWED_SERVICES, {"api", "auth"})


class AccountEventsGuardTests(unittest.TestCase):
    def test_reading_events_of_another_account_is_refused(self):
        with self.assertRaises(seed.UnsafeSeedTarget):
            seed.account_events("someone.else@udf.edu.br")


if __name__ == "__main__":
    unittest.main()
