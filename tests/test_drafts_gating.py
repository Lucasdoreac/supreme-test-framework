import configparser
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class DraftsGatingTests(unittest.TestCase):
    """The scenarios that need the Web Drafts must not run by default (main stays green)."""

    def test_the_default_run_skips_drafts(self):
        config = configparser.ConfigParser()
        config.read(ROOT / "behave.ini")
        expression = config["behave"]["default_tags"]
        self.assertIn("not @drafts", expression)
        self.assertIn("not @skip", expression)

    def test_every_scenario_of_the_logged_in_feature_is_tagged_drafts(self):
        text = (ROOT / "features" / "logged_in.feature").read_text(encoding="utf-8")
        blocks = re.split(r"\n(?=\s*@)", text)
        scenarios = [b for b in blocks if re.search(r"^\s*Scenario( Outline)?:", b, re.M)]
        self.assertGreaterEqual(len(scenarios), 3)
        for block in scenarios:
            self.assertRegex(block.split("\n", 1)[0], r"@drafts", block[:80])

    def test_login_feature_stays_ungated(self):
        text = (ROOT / "features" / "login.feature").read_text(encoding="utf-8")
        self.assertNotIn("@drafts", text)


if __name__ == "__main__":
    unittest.main()
