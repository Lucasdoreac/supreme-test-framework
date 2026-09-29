import unittest
from unittest.mock import Mock, patch

from utils.helpers import get_browser_logs, get_magic_link, rebase_magic_link


class BrowserLogTests(unittest.TestCase):
    def test_returns_no_logs_when_remote_driver_does_not_expose_log_endpoint(self):
        driver = Mock(spec=[])
        self.assertEqual(get_browser_logs(driver), [])


class MagicLinkTests(unittest.TestCase):
    def test_rebases_callback_to_frontend_service_without_changing_token(self):
        link = "http://127.0.0.1:3000/auth/callback?email=a%40udf.edu.br&hash=abc#fragment"

        rebased = rebase_magic_link(link, "http://reservas-e2e:3000")

        self.assertEqual(
            rebased,
            "http://reservas-e2e:3000/auth/callback?email=a%40udf.edu.br&hash=abc#fragment",
        )

    @patch("utils.helpers.requests.post")
    @patch.dict("os.environ", {"API_URL": "http://api.test"})
    def test_requests_magic_link_using_api_query_contract(self, post):
        response = Mock(status_code=201)
        response.json.return_value = {"magic_link": "http://web.test/auth/callback?hash=abc"}
        post.return_value = response

        link = get_magic_link("tester@udf.edu.br")

        self.assertEqual(link, "http://web.test/auth/callback?hash=abc")
        post.assert_called_once_with(
            "http://api.test/auth/send-link",
            params={"email": "tester@udf.edu.br"},
        )


if __name__ == "__main__":
    unittest.main()
