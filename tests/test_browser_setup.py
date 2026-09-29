import os
import unittest
from unittest.mock import Mock, patch

from utils.browser_setup import setup_webdriver


class BrowserSetupTests(unittest.TestCase):
    @patch("utils.browser_setup.webdriver.Chrome")
    @patch("utils.browser_setup.webdriver.Remote")
    def test_uses_remote_grid_when_url_is_configured(self, remote, chrome):
        driver = Mock()
        remote.return_value = driver
        with patch.dict(os.environ, {"SELENIUM_REMOTE_URL": "http://grid:4444/wd/hub"}):
            result = setup_webdriver()

        self.assertIs(result, driver)
        remote.assert_called_once()
        self.assertEqual(remote.call_args.kwargs["command_executor"], "http://grid:4444/wd/hub")
        chrome.assert_not_called()
        driver.set_page_load_timeout.assert_called_once_with(30)
        driver.implicitly_wait.assert_called_once_with(10)

    @patch("utils.browser_setup.webdriver.Chrome")
    @patch("utils.browser_setup.webdriver.Remote")
    def test_uses_local_chrome_without_remote_url(self, remote, chrome):
        driver = Mock()
        chrome.return_value = driver
        with patch.dict(os.environ, {}, clear=True):
            result = setup_webdriver()

        self.assertIs(result, driver)
        chrome.assert_called_once()
        remote.assert_not_called()


if __name__ == "__main__":
    unittest.main()
