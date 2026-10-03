import logging
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from features import environment


def make_context(seeded=("507f1f77bcf86cd799439011",)):
    return SimpleNamespace(driver=Mock(), seeded_event_ids=list(seeded))


class AfterScenarioCleanupTests(unittest.TestCase):
    def run_hook(self, context, status="passed", **patches):
        scenario = SimpleNamespace(status=status, tags=["auth"], name="cenario")
        with patch("utils.seed.delete_events", **patches.get("delete", {"return_value": 1})), \
                patch.object(environment, "get_browser_logs", **patches.get("logs", {"return_value": []})) as logs, \
                patch.object(environment, "take_screenshot", **patches.get("shot", {})) as shot:
            driver = context.driver
            try:
                environment.after_scenario(context, scenario)
            finally:
                self.logs, self.shot, self.driver = logs, shot, driver

    def test_a_clean_run_passes_and_closes_the_browser(self):
        context = make_context()
        self.run_hook(context)
        self.driver.quit.assert_called_once()
        self.assertEqual(context.seeded_event_ids, [])

    def test_a_failing_seed_cleanup_does_not_skip_the_other_steps_and_is_an_error(self):
        context = make_context()
        with self.assertLogs(environment.logger, level=logging.ERROR) as captured:
            with self.assertRaises(RuntimeError) as raised:
                self.run_hook(context, status="failed", delete={"side_effect": ConnectionError("secret-host")})
        self.logs.assert_called_once()
        self.shot.assert_called_once()
        self.driver.execute_script.assert_called_once()
        self.driver.quit.assert_called_once()
        self.assertIn("remove seeded events", str(raised.exception))
        text = "\n".join(captured.output)
        self.assertIn("ConnectionError", text)
        self.assertNotIn("secret-host", text)

    def test_each_later_step_failing_is_isolated_and_reported(self):
        context = make_context(seeded=())
        with self.assertLogs(environment.logger, level=logging.ERROR):
            with self.assertRaises(RuntimeError) as raised:
                self.run_hook(context, status="failed", logs={"side_effect": OSError()},
                              shot={"side_effect": ValueError()})
        self.driver.execute_script.assert_called_once()
        self.driver.quit.assert_called_once()
        message = str(raised.exception)
        self.assertIn("browser logs", message)
        self.assertIn("failure screenshot", message)

    def test_a_failing_quit_is_an_error_too(self):
        context = make_context(seeded=())
        context.driver.quit.side_effect = RuntimeError("boom")
        with self.assertLogs(environment.logger, level=logging.ERROR):
            with self.assertRaises(RuntimeError):
                self.run_hook(context)


if __name__ == "__main__":
    unittest.main()
