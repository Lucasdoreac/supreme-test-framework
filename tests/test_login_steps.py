import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from features.steps.login_steps import step_impl_access_magic_link, step_impl_verify_redirect


class RedirectStepTests(unittest.TestCase):
    def test_keeps_the_magic_link_tab_open_after_redirect(self):
        login_page = Mock()
        login_page.is_redirected_to_events_page.return_value = True
        login_page.verify_events_heading.return_value = True
        context = SimpleNamespace(login_page=login_page, email="tester@udf.edu.br")

        step_impl_verify_redirect(context)

        login_page.close_tab_and_return_to_original.assert_not_called()


class SingleUseLinkTests(unittest.TestCase):
    def make_context(self, stored_token):
        login_page = Mock()
        login_page.wait_for_session_token.return_value = stored_token
        login_page.is_redirected_to_events_page.return_value = True
        login_page.verify_events_heading.return_value = True
        driver = Mock(current_url="http://web:3000/event/mine")
        config = SimpleNamespace(userdata={"BASE_URL": "http://web:3000"})
        return SimpleNamespace(
            login_page=login_page, driver=driver, config=config,
            magic_link="http://localhost:3000/auth/callback?email=a%40udf.edu.br&hash=" + "L" * 43,
            hash="L" * 43,
        )

    def test_accepts_a_session_token_that_differs_from_the_link(self):
        context = self.make_context("S" * 43)
        step_impl_access_magic_link(context)
        context.login_page.click_enter_on_callback.assert_called_once()

    def test_rejects_a_stored_token_equal_to_the_single_use_link(self):
        with self.assertRaises(AssertionError):
            step_impl_access_magic_link(self.make_context("L" * 43))

    def test_fails_when_no_token_is_stored(self):
        with self.assertRaises(AssertionError):
            step_impl_access_magic_link(self.make_context(None))


if __name__ == "__main__":
    unittest.main()
