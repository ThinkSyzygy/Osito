from __future__ import annotations

import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path
from types import SimpleNamespace


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def load_validator():
    path = REPOSITORY_ROOT / "scripts" / "validation" / "validate.py"
    spec = importlib.util.spec_from_file_location("osito_validate", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load repository validator")
    module = importlib.util.module_from_spec(spec)
    sys.modules["osito_validate"] = module
    spec.loader.exec_module(module)
    return module


validate = load_validator()


class RepositoryStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.issues = validate.validate_repository(REPOSITORY_ROOT)

    def assert_no_rules(self, *rules: str):
        failures = [issue for issue in self.issues if issue.rule_id in set(rules)]
        self.assertEqual([], failures, validate.format_issues(failures))

    def with_file_attributes(self, observation, attributes: int):
        return SimpleNamespace(
            st_mode=observation.st_mode,
            st_dev=observation.st_dev,
            st_ino=observation.st_ino,
            st_nlink=observation.st_nlink,
            st_size=observation.st_size,
            st_file_attributes=attributes,
        )

    def test_required_files_and_directories_exist(self):
        self.assert_no_rules("MISSING_REQUIRED_FILE", "MISSING_REQUIRED_DIRECTORY")

    def test_repository_tree_has_only_expected_top_level_entries(self):
        self.assert_no_rules("UNEXPECTED_TOP_LEVEL", "EMPTY_PUBLIC_AREA")

    def test_templates_are_nonempty_and_have_required_fields(self):
        self.assert_no_rules(
            "EMPTY_TEMPLATE",
            "MISSING_TEMPLATE_FRONTMATTER",
            "MISSING_TEMPLATE_FIELD",
        )

    def test_template_placeholders_are_consistent(self):
        self.assert_no_rules(
            "MISSING_TEMPLATE_PLACEHOLDER",
            "INVALID_TEMPLATE_PLACEHOLDER",
        )

    def test_yaml_and_frontmatter_are_valid(self):
        self.assert_no_rules("INVALID_SIMPLE_YAML", "INVALID_FRONTMATTER")

    def test_relative_markdown_links_resolve(self):
        self.assert_no_rules(
            "BROKEN_RELATIVE_LINK",
            "BROKEN_SOURCE_LINK",
            "INVALID_SOURCE_LINKS",
            "OUTSIDE_REPOSITORY_LINK",
            "OUTSIDE_REPOSITORY_SOURCE_LINK",
        )

    def test_identifiers_are_unique(self):
        self.assert_no_rules("DUPLICATE_IDENTIFIER")

    def test_repository_has_no_binary_links_or_nested_repositories(self):
        self.assert_no_rules(
            "BINARY_FILE",
            "GIT_SUBMODULE_CONFIG",
            "NESTED_GIT_REPOSITORY",
            "SYMLINK",
            "UNEXPECTED_FILE_TYPE",
        )

    def test_external_denylist_interface_exists(self):
        self.assert_no_rules("MISSING_DENYLIST_INTERFACE", "MISSING_AUDIT_WRAPPER")

    def test_simple_yaml_rejects_common_invalid_forms(self):
        invalid = "root:\n   child: value\nroot: duplicate\n"
        self.assertTrue(validate.validate_simple_yaml(invalid))

    def test_broken_link_detector_is_repository_relative(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            document = root / "README.md"
            document.write_text("[Missing](docs/missing.md)\n", encoding="utf-8")
            issues = validate.broken_markdown_links(document, root, document.read_text(encoding="utf-8"))
            self.assertEqual(["BROKEN_RELATIVE_LINK"], [issue.rule_id for issue in issues])

    def test_repository_validation_reports_broken_markdown_link(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            document = root / "README.md"
            document.write_text("[Missing](docs/missing.md)\n", encoding="utf-8")
            issues = validate.validate_repository(root)
            self.assertIn("BROKEN_RELATIVE_LINK", {issue.rule_id for issue in issues})

    def test_relative_link_cannot_escape_repository(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            root = parent / "repository"
            root.mkdir()
            (parent / "outside.md").write_text("outside\n", encoding="utf-8")
            document = root / "README.md"
            text = "[Outside](../outside.md)\n"
            document.write_text(text, encoding="utf-8")
            issues = validate.broken_markdown_links(document, root, text)
            self.assertEqual(["OUTSIDE_REPOSITORY_LINK"], [issue.rule_id for issue in issues])

    def test_symlinked_link_target_cannot_escape_repository_when_supported(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            root = parent / "repository"
            docs = root / "docs"
            docs.mkdir(parents=True)
            outside = parent / "outside.md"
            outside.write_text("outside\n", encoding="utf-8")
            link = docs / "linked.md"
            try:
                link.symlink_to(outside)
            except OSError as exc:
                self.skipTest(f"Symlinks unavailable in this test environment: {exc}")
            document = root / "README.md"
            text = "[Outside](docs/linked.md)\n"
            document.write_text(text, encoding="utf-8")
            issues = validate.broken_markdown_links(document, root, text)
            self.assertEqual(["OUTSIDE_REPOSITORY_LINK"], [issue.rule_id for issue in issues])

    def test_resolved_link_escape_is_rejected_without_platform_symlink_support(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            root = parent / "repository"
            docs = root / "docs"
            docs.mkdir(parents=True)
            linked = docs / "linked.md"
            linked.write_text("fixture\n", encoding="utf-8")
            outside = parent / "outside.md"
            outside.write_text("outside\n", encoding="utf-8")
            document = root / "README.md"
            text = "[Outside](docs/linked.md)\n"
            original_resolve = Path.resolve

            def resolve_escape(path: Path, *args, **kwargs):
                if path == linked:
                    return outside
                return original_resolve(path, *args, **kwargs)

            with mock.patch.object(Path, "resolve", new=resolve_escape):
                issues = validate.broken_markdown_links(document, root, text)
            self.assertEqual(["OUTSIDE_REPOSITORY_LINK"], [issue.rule_id for issue in issues])

    def test_frontmatter_source_links_are_validated(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            root = parent / "repository"
            records = root / "records"
            records.mkdir(parents=True)
            (parent / "outside.md").write_text("outside\n", encoding="utf-8")
            document = records / "record.md"
            text = (
                "---\n"
                "source_links: [\"MTG-DEMO-001\", \"missing.md\", \"../../outside.md\"]\n"
                "---\n"
            )
            fields, error = validate.parse_frontmatter(text)
            self.assertIsNone(error)
            self.assertIsNotNone(fields)
            issues = validate.frontmatter_source_link_issues(document, root, text, fields)
            self.assertEqual(
                ["BROKEN_SOURCE_LINK", "OUTSIDE_REPOSITORY_SOURCE_LINK"],
                [issue.rule_id for issue in issues],
            )

    def test_fictional_label_requires_positive_declaration(self):
        self.assertIsNone(validate.FICTIONAL_LABEL_RE.search("This example is not fictional."))
        self.assertIsNone(validate.FICTIONAL_LABEL_RE.search("fictional: false"))
        self.assertIsNotNone(validate.FICTIONAL_LABEL_RE.search("fictional: true"))
        self.assertIsNotNone(
            validate.FICTIONAL_LABEL_RE.search("> **Fictional example:** all values are invented.")
        )

    def test_required_example_areas_include_assumptions_and_archive(self):
        self.assertTrue({"assumptions", "archive"}.issubset(validate.REQUIRED_EXAMPLE_AREAS))

    def test_binary_sniff_reads_only_the_sample(self):
        sizes: list[int] = []

        class GuardedStream(io.BytesIO):
            def read(self, size: int = -1) -> bytes:
                sizes.append(size)
                return super().read(size)

        stream = GuardedStream(b"plain text")
        with mock.patch.object(Path, "open", return_value=stream):
            self.assertFalse(validate._is_binary(Path("fixture.md")))
        self.assertEqual([8192], sizes)

    def test_validator_reports_and_prunes_mocked_directory_reparse_point(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            linked = root / "linked-directory"
            linked.mkdir()
            target_content = linked / "must-not-be-read.md"
            target_content.write_text("outside-like fixture\n", encoding="utf-8")
            original_lstat = Path.lstat
            original_open = Path.open

            def reparse_lstat(path: Path, *args, **kwargs):
                observation = original_lstat(path, *args, **kwargs)
                if path == linked:
                    return self.with_file_attributes(
                        observation,
                        validate.FILE_ATTRIBUTE_REPARSE_POINT,
                    )
                return observation

            def guarded_open(path: Path, *args, **kwargs):
                if path == target_content:
                    raise AssertionError("validator descended into a mocked reparse directory")
                return original_open(path, *args, **kwargs)

            with (
                mock.patch.object(Path, "lstat", new=reparse_lstat),
                mock.patch.object(Path, "is_junction", new=None, create=True),
                mock.patch.object(Path, "open", new=guarded_open),
            ):
                issues = validate.validate_repository(root)
            self.assertIn("REPARSE_POINT", {item.rule_id for item in issues})
            self.assertNotIn(
                target_content.relative_to(root).as_posix(),
                {item.path for item in issues},
            )

    def test_validator_does_not_read_mocked_file_reparse_point(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            linked = root / "linked-file.md"
            linked.write_text("target fixture\n", encoding="utf-8")
            original_lstat = Path.lstat
            original_open = Path.open

            def reparse_lstat(path: Path, *args, **kwargs):
                observation = original_lstat(path, *args, **kwargs)
                if path == linked:
                    return self.with_file_attributes(
                        observation,
                        validate.FILE_ATTRIBUTE_REPARSE_POINT,
                    )
                return observation

            def guarded_open(path: Path, *args, **kwargs):
                if path == linked:
                    raise AssertionError("validator opened a mocked file reparse point")
                return original_open(path, *args, **kwargs)

            with (
                mock.patch.object(Path, "lstat", new=reparse_lstat),
                mock.patch.object(Path, "is_junction", new=None, create=True),
                mock.patch.object(Path, "open", new=guarded_open),
            ):
                issues = validate.validate_repository(root)
            self.assertIn("REPARSE_POINT", {item.rule_id for item in issues})

    def test_validator_does_not_reread_reparse_at_audit_interface_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            audit_root = root / "scripts" / "audit"
            audit_root.mkdir(parents=True)
            linked = audit_root / "sanitize.py"
            linked.write_text("target fixture\n", encoding="utf-8")
            original_lstat = Path.lstat
            original_open = Path.open

            def reparse_lstat(path: Path, *args, **kwargs):
                observation = original_lstat(path, *args, **kwargs)
                if path == linked:
                    return self.with_file_attributes(
                        observation,
                        validate.FILE_ATTRIBUTE_REPARSE_POINT,
                    )
                return observation

            def guarded_open(path: Path, *args, **kwargs):
                if path == linked:
                    raise AssertionError("validator reread the audit reparse target")
                return original_open(path, *args, **kwargs)

            with (
                mock.patch.object(Path, "lstat", new=reparse_lstat),
                mock.patch.object(Path, "is_junction", new=None, create=True),
                mock.patch.object(Path, "open", new=guarded_open),
            ):
                issues = validate.validate_repository(root)
            rules = {item.rule_id for item in issues}
            self.assertIn("REPARSE_POINT", rules)
            self.assertIn("MISSING_DENYLIST_INTERFACE", rules)

    def test_validator_reports_file_identity_change_before_content_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            root = parent / "repository"
            root.mkdir()
            victim = root / "victim.md"
            victim.write_text("original fixture\n", encoding="utf-8")
            replacement = parent / "replacement.md"
            replacement.write_text("replacement fixture\n", encoding="utf-8")
            original_open = Path.open

            def swapped_open(path: Path, *args, **kwargs):
                if path == victim:
                    return original_open(replacement, *args, **kwargs)
                return original_open(path, *args, **kwargs)

            with mock.patch.object(Path, "open", new=swapped_open):
                issues = validate.validate_repository(root)
            self.assertIn("IDENTITY_CHANGED", {item.rule_id for item in issues})

    def test_validator_reports_mocked_junction_when_path_api_is_available(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            junction = root / "junction"
            junction.mkdir()
            target_content = junction / "must-not-be-read.md"
            target_content.write_text("outside-like fixture\n", encoding="utf-8")
            original_open = Path.open

            def is_junction(path: Path) -> bool:
                return path == junction

            def guarded_open(path: Path, *args, **kwargs):
                if path == target_content:
                    raise AssertionError("validator descended into a mocked junction")
                return original_open(path, *args, **kwargs)

            with (
                mock.patch.object(Path, "is_junction", new=is_junction, create=True),
                mock.patch.object(Path, "open", new=guarded_open),
            ):
                issues = validate.validate_repository(root)
            self.assertIn("JUNCTION", {item.rule_id for item in issues})
            self.assertNotIn(
                target_content.relative_to(root).as_posix(),
                {item.path for item in issues},
            )

    @unittest.skipUnless(os.name == "nt", "real Windows junction regression")
    def test_validator_reports_real_windows_junction_without_traversal(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            root = parent / "repository"
            root.mkdir()
            external = parent / "external"
            external.mkdir()
            (external / "outside.md").write_text("outside fixture\n", encoding="utf-8")
            junction = root / "junction"
            result = subprocess.run(
                ["cmd", "/d", "/c", "mklink", "/J", str(junction), str(external)],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                self.skipTest("Directory junctions unavailable in this Windows test environment.")
            try:
                issues = validate.validate_repository(root)
                self.assertTrue(
                    {"JUNCTION", "REPARSE_POINT"}.intersection(
                        item.rule_id for item in issues
                    )
                )
                self.assertNotIn(
                    "junction/outside.md",
                    {item.path for item in issues},
                )
            finally:
                if junction.exists():
                    junction.rmdir()


if __name__ == "__main__":
    unittest.main()
