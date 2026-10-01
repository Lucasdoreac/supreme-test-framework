import unittest
from pathlib import Path


class DependencyManifestTests(unittest.TestCase):
    def test_webdriver_manager_is_not_declared_without_code_usage(self):
        project = Path(__file__).resolve().parents[1]
        poetry_manifest = (project / "pyproject.toml").read_text().lower()
        poetry_lock = (project / "poetry.lock").read_text().lower()

        self.assertNotIn("webdriver-manager", poetry_manifest)
        self.assertNotIn('name = "webdriver-manager"', poetry_lock)


if __name__ == "__main__":
    unittest.main()
