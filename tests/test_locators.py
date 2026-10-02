import unittest

from selenium.webdriver.common.by import By

from features.steps.login_steps import DOMAIN_ERROR_LOCATOR
from page_objects.login_page import EVENTS_HEADING_LOCATOR


class MarkupCompatibleLocatorTests(unittest.TestCase):
    """No HTML parser is a dependency, so the XPath structure is asserted:
    each locator must name both the current and the upcoming element."""

    def test_domain_error_matches_span_and_role_alert(self):
        by, xpath = DOMAIN_ERROR_LOCATOR
        self.assertEqual(by, By.XPATH)
        self.assertTrue(xpath.startswith("//*["))
        self.assertIn("self::span", xpath)
        self.assertIn("@role='alert'", xpath)
        self.assertIn("fora do formato permitido", xpath)

    def test_events_heading_matches_h2_and_h1(self):
        by, xpath = EVENTS_HEADING_LOCATOR
        self.assertEqual(by, By.XPATH)
        self.assertTrue(xpath.startswith("//*["))
        self.assertIn("self::h1", xpath)
        self.assertIn("self::h2", xpath)
        self.assertIn("normalize-space(.)='Meus Eventos'", xpath)


if __name__ == "__main__":
    unittest.main()
