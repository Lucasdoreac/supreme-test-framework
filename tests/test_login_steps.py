import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from features.steps.login_steps import step_impl_verify_redirect


class RedirectStepTests(unittest.TestCase):
    def test_keeps_the_magic_link_tab_open_after_redirect(self):
        login_page = Mock()
        login_page.is_redirected_to_events_page.return_value = True
        login_page.verify_events_heading.return_value = True
        context = SimpleNamespace(login_page=login_page, email="tester@udf.edu.br")

        step_impl_verify_redirect(context)

        login_page.close_tab_and_return_to_original.assert_not_called()


if __name__ == "__main__":
    unittest.main()
