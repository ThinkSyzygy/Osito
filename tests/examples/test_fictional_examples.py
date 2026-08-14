from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def load_validator():
    path = REPOSITORY_ROOT / "scripts" / "validation" / "validate.py"
    spec = importlib.util.spec_from_file_location("osito_validate_examples", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load repository validator")
    module = importlib.util.module_from_spec(spec)
    sys.modules["osito_validate_examples"] = module
    spec.loader.exec_module(module)
    return module


validate = load_validator()


class FictionalExampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.issues = validate.validate_repository(REPOSITORY_ROOT)

    def test_example_is_complete_and_labeled_fictional(self):
        relevant = {
            "INCOMPLETE_FICTIONAL_EXAMPLE",
            "MISSING_FICTIONAL_EXAMPLE_METADATA",
            "MISSING_FICTIONAL_EXAMPLE_OVERVIEW",
            "MISSING_FICTIONAL_LABEL",
        }
        failures = [issue for issue in self.issues if issue.rule_id in relevant]
        self.assertEqual([], failures, validate.format_issues(failures))

    def test_example_metadata_has_no_duplicate_ids(self):
        failures = [
            issue
            for issue in self.issues
            if issue.rule_id == "DUPLICATE_IDENTIFIER"
            and issue.path.startswith("examples/")
        ]
        self.assertEqual([], failures, validate.format_issues(failures))

    def test_example_links_resolve(self):
        failures = [
            issue
            for issue in self.issues
            if issue.rule_id == "BROKEN_RELATIVE_LINK"
            and issue.path.startswith("examples/")
        ]
        self.assertEqual([], failures, validate.format_issues(failures))


if __name__ == "__main__":
    unittest.main()
