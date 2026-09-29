import unittest
from pathlib import Path


class DependencyManifestTests(unittest.TestCase):
    def test_webdriver_manager_is_not_declared_without_code_usage(self):
        project = Path(__file__).resolve().parents[1]
        poetry_manifest = (project / "pyproject.toml").read_text().lower()
        pip_requirements = (project / "requirements.txt").read_text().lower()

        self.assertNotIn("webdriver-manager", poetry_manifest)
        self.assertNotIn("webdriver-manager", pip_requirements)


if __name__ == "__main__":
    unittest.main()
