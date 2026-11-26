"""Synthetic regression tests against the current helpers, never E2E tests."""
import errno
import importlib.util
from pathlib import Path
import socket
import subprocess
import sys
import types
import unittest
from unittest.mock import Mock, patch


def load_helpers_with_stubs():
    # The offline runner needs only stdlib, not Selenium, requests or a browser.
    names = ("requests", "selenium", "selenium.webdriver", "selenium.webdriver.remote",
             "selenium.webdriver.remote.webdriver", "selenium.common", "selenium.common.exceptions")
    modules = {name: types.ModuleType(name) for name in names}
    modules["requests"].post = Mock(side_effect=AssertionError("unexpected HTTP call"))
    modules["selenium.webdriver.remote.webdriver"].WebDriver = type("WebDriver", (), {})
    modules["selenium.common.exceptions"].WebDriverException = type("WebDriverException", (Exception,), {})
    modules["selenium.common.exceptions"].TimeoutException = type("TimeoutException", (Exception,), {})
    with patch.dict(sys.modules, modules):
        path = Path(__file__).resolve().parents[2] / "utils" / "helpers.py"
        spec = importlib.util.spec_from_file_location("offline_helpers", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


helpers = load_helpers_with_stubs()


class NetworkGuardTests(unittest.TestCase):
    def test_socket_is_denied_by_kernel(self):
        with self.assertRaises(OSError) as caught:
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.assertEqual(caught.exception.errno, errno.EPERM)

    def test_child_inherits_guard(self):
        child = subprocess.run([sys.executable, "-c", "import socket; socket.socket()"],
                               capture_output=True, text=True, timeout=5)
        self.assertNotEqual(child.returncode, 0)
        self.assertIn("PermissionError", child.stderr)


class HelperTests(unittest.TestCase):
    # Adapted from test/e2e-logged-in-screens:tests/test_helpers.py.
    def test_browser_logs_no_endpoint(self):
        self.assertEqual(helpers.get_browser_logs(Mock(spec=[])), [])

    def test_browser_logs_formatted(self):
        driver = Mock()
        driver.get_log.return_value = [{"level": "INFO", "message": "synthetic"}]
        self.assertEqual(helpers.get_browser_logs(driver), ["INFO: synthetic"])
        driver.get_log.assert_called_once_with("browser")

    def test_email_suffix(self):
        for email, expected in [("example@udf.edu.br", True), ("X@UDF.EDU.BR", True),
                                ("example@example.invalid", False)]:
            with self.subTest(email=email):
                self.assertEqual(helpers.validate_email(email), expected)

    def test_extract_synthetic_hash(self):
        self.assertEqual(helpers.extract_hash_from_link("http://example.invalid/callback?hash=synthetic&x=1"), "synthetic")
        self.assertIsNone(helpers.extract_hash_from_link("http://example.invalid/callback"))
        self.assertIsNone(helpers.extract_hash_from_link(""))

    def test_magic_link_existing_legacy_behavior_with_fake_http(self):
        # Documents the current branch only, not the unconfirmed API contract.
        response = Mock(status_code=200)
        response.json.return_value = {"magic_link": "http://example.invalid/?hash=synthetic"}
        with patch.object(helpers.requests, "post", return_value=response) as post, \
             patch.dict("os.environ", {"API_URL": "http://example.invalid"}):
            self.assertEqual(helpers.get_magic_link("example@udf.edu.br"),
                             "http://example.invalid/?hash=synthetic")
        post.assert_called_once_with("http://example.invalid/auth/send-link",
                                     json={"email": "example@udf.edu.br"},
                                     headers={"Content-Type": "application/json"})


if __name__ == "__main__":
    unittest.main()
