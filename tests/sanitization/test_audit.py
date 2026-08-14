from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path
from types import SimpleNamespace


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def import_public_script(module_name: str, repository_path: str):
    source_path = REPOSITORY_ROOT / repository_path
    module_spec = importlib.util.spec_from_file_location(module_name, source_path)
    if module_spec is None:
        raise RuntimeError(f"Unable to create an import specification for {repository_path}")
    loader = module_spec.loader
    if loader is None:
        raise RuntimeError(f"No loader is available for {repository_path}")
    loaded_module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_name] = loaded_module
    loader.exec_module(loaded_module)
    return loaded_module


sanitize = import_public_script("osito_sanitize", "scripts/audit/sanitize.py")


class AuditBehaviorTests(unittest.TestCase):
    def make_root(self, parent: Path) -> Path:
        root = parent / "repository"
        root.mkdir()
        (root / "README.md").write_text(
            "# Public test repository\n\nThis is a fictional test fixture.\n",
            encoding="utf-8",
        )
        return root

    def with_file_attributes(self, observation, attributes: int):
        return SimpleNamespace(
            st_mode=observation.st_mode,
            st_dev=observation.st_dev,
            st_ino=observation.st_ino,
            st_nlink=observation.st_nlink,
            st_size=observation.st_size,
            st_file_attributes=attributes,
        )

    def test_clean_text_repository_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(Path(temporary))
            self.assertEqual([], sanitize.run_audit(root))

    def test_external_denylist_is_case_insensitive_and_never_disclosed(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            root = self.make_root(parent)
            private_term = "blue" + "-orchid"
            denylist = parent / "terms.txt"
            denylist.write_text(private_term.upper() + "\n", encoding="utf-8")
            (root / "README.md").write_text(
                "# Fixture\n\n" + private_term + "\n",
                encoding="utf-8",
            )
            findings = sanitize.run_audit(root, denylist_path=denylist)
            self.assertIn("DENYLIST_CONTENT", {item.rule_id for item in findings})
            rendered = sanitize.format_findings(findings)
            self.assertNotIn(private_term.casefold(), rendered.casefold())

    def test_sensitive_filename_is_redacted(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            root = self.make_root(parent)
            private_term = "violet" + "-ledger"
            denylist = parent / "terms.txt"
            denylist.write_text(private_term + "\n", encoding="utf-8")
            (root / f"{private_term}.md").write_text("Fictional fixture.\n", encoding="utf-8")
            findings = sanitize.run_audit(root, denylist_path=denylist)
            rendered = sanitize.format_findings(findings)
            self.assertIn("<redacted-path>", rendered)
            self.assertNotIn(private_term, rendered)

    def test_example_email_domains_are_allowed_and_other_domains_are_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(Path(temporary))
            allowed = "engineer" + "@" + "example.com"
            private = "engineer" + "@" + "private.invalid"
            (root / "README.md").write_text(
                "\n".join(("# Fixture", allowed, private, "")),
                encoding="utf-8",
            )
            findings = sanitize.run_audit(root)
            email_findings = [item for item in findings if item.rule_id == "EMAIL_ADDRESS"]
            self.assertEqual(1, len(email_findings))

    def test_secret_finding_does_not_print_matched_value(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(Path(temporary))
            secret = "AKIA" + "A1B2C3D4E5F6G7H8"
            (root / "README.md").write_text("# Fixture\n\n" + secret + "\n", encoding="utf-8")
            findings = sanitize.run_audit(root)
            self.assertIn("AWS_ACCESS_KEY", {item.rule_id for item in findings})
            self.assertNotIn(secret, sanitize.format_findings(findings))

    def test_structural_hazards_are_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(Path(temporary))
            (root / ".private.txt").write_text("fixture\n", encoding="utf-8")
            (root / "bundle.zip").write_text("not actually an archive\n", encoding="utf-8")
            (root / "sample.bin").write_bytes(b"fixture\x00binary")
            nested = root / "scripts" / "sample" / ".git"
            nested.mkdir(parents=True)
            findings = sanitize.run_audit(root)
            rules = {item.rule_id for item in findings}
            self.assertTrue(
                {"HIDDEN_ENTRY", "ARCHIVE_FILE", "BINARY_FILE", "NESTED_GIT_REPOSITORY"}.issubset(rules)
            )

    def test_symlink_and_hardlink_detection_when_supported(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(Path(temporary))
            original = root / "source.txt"
            original.write_text("fixture\n", encoding="utf-8")
            hardlink = root / "linked.txt"
            try:
                os.link(original, hardlink)
            except OSError as exc:
                self.skipTest(f"Hardlinks unavailable in this test environment: {exc}")
            findings = sanitize.run_audit(root)
            self.assertIn("HARDLINK", {item.rule_id for item in findings})

            symlink = root / "pointer.txt"
            try:
                symlink.symlink_to(original.name)
            except OSError:
                return
            findings = sanitize.run_audit(root)
            self.assertIn("SYMLINK", {item.rule_id for item in findings})

    def test_configuration_errors_use_exit_code_two(self):
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "missing"
            self.assertEqual(sanitize.EXIT_USAGE, sanitize.main(["--root", str(missing)]))

    def test_unreadable_lstat_is_reported_and_returns_findings_status(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(Path(temporary))
            docs = root / "docs"
            docs.mkdir()
            blocked = docs / "blocked.md"
            blocked.write_text("fixture\n", encoding="utf-8")
            original_lstat = Path.lstat

            def fail_blocked(path: Path, *args, **kwargs):
                if path == blocked:
                    raise PermissionError("simulated unreadable entry")
                return original_lstat(path, *args, **kwargs)

            with mock.patch.object(Path, "lstat", new=fail_blocked):
                findings = sanitize.run_audit(root)
                self.assertIn("UNREADABLE_ENTRY", {item.rule_id for item in findings})
                self.assertEqual(sanitize.EXIT_FINDINGS, sanitize.main(["--root", str(root)]))

    def test_walk_errors_are_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(Path(temporary))

            def failed_walk(*args, **kwargs):
                error = PermissionError("simulated traversal failure")
                error.filename = str(root / "docs")
                kwargs["onerror"](error)
                return []

            with mock.patch.object(sanitize.os, "walk", new=failed_walk):
                findings = sanitize.run_audit(root)
            self.assertIn("UNREADABLE_ENTRY", {item.rule_id for item in findings})

    def test_mocked_directory_reparse_point_is_reported_and_pruned(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(Path(temporary))
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
                        sanitize.FILE_ATTRIBUTE_REPARSE_POINT,
                    )
                return observation

            def guarded_open(path: Path, *args, **kwargs):
                if path == target_content:
                    raise AssertionError("audit descended into a mocked reparse directory")
                return original_open(path, *args, **kwargs)

            with (
                mock.patch.object(Path, "lstat", new=reparse_lstat),
                mock.patch.object(Path, "is_junction", new=None, create=True),
                mock.patch.object(Path, "open", new=guarded_open),
            ):
                findings = sanitize.run_audit(root)
            self.assertIn("REPARSE_POINT", {item.rule_id for item in findings})
            self.assertNotIn(
                target_content.relative_to(root).as_posix(),
                {item.path for item in findings},
            )

    def test_mocked_file_reparse_point_is_not_opened(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(Path(temporary))
            linked = root / "linked-file.md"
            linked.write_text("target fixture\n", encoding="utf-8")
            original_lstat = Path.lstat
            original_open = Path.open

            def reparse_lstat(path: Path, *args, **kwargs):
                observation = original_lstat(path, *args, **kwargs)
                if path == linked:
                    return self.with_file_attributes(
                        observation,
                        sanitize.FILE_ATTRIBUTE_REPARSE_POINT,
                    )
                return observation

            def guarded_open(path: Path, *args, **kwargs):
                if path == linked:
                    raise AssertionError("audit opened a mocked file reparse point")
                return original_open(path, *args, **kwargs)

            with (
                mock.patch.object(Path, "lstat", new=reparse_lstat),
                mock.patch.object(Path, "is_junction", new=None, create=True),
                mock.patch.object(Path, "open", new=guarded_open),
            ):
                findings = sanitize.run_audit(root)
            self.assertIn("REPARSE_POINT", {item.rule_id for item in findings})

    def test_file_identity_change_is_reported_before_content_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            root = self.make_root(parent)
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
                findings = sanitize.run_audit(root)
            self.assertIn("IDENTITY_CHANGED", {item.rule_id for item in findings})

    def test_mocked_junction_is_reported_when_path_api_is_available(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_root(Path(temporary))
            junction = root / "junction"
            junction.mkdir()
            target_content = junction / "must-not-be-read.md"
            target_content.write_text("outside-like fixture\n", encoding="utf-8")
            original_open = Path.open

            def is_junction(path: Path) -> bool:
                return path == junction

            def guarded_open(path: Path, *args, **kwargs):
                if path == target_content:
                    raise AssertionError("audit descended into a mocked junction")
                return original_open(path, *args, **kwargs)

            with (
                mock.patch.object(Path, "is_junction", new=is_junction, create=True),
                mock.patch.object(Path, "open", new=guarded_open),
            ):
                findings = sanitize.run_audit(root)
            self.assertIn("JUNCTION", {item.rule_id for item in findings})
            self.assertNotIn(
                target_content.relative_to(root).as_posix(),
                {item.path for item in findings},
            )

    @unittest.skipUnless(os.name == "nt", "real Windows junction regression")
    def test_real_windows_junction_is_reported_without_traversal(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            root = self.make_root(parent)
            external = parent / "external"
            external.mkdir()
            target_content = external / "outside.md"
            target_content.write_text("outside fixture\n", encoding="utf-8")
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
                findings = sanitize.run_audit(root)
                self.assertTrue(
                    {"JUNCTION", "REPARSE_POINT"}.intersection(
                        item.rule_id for item in findings
                    )
                )
                self.assertNotIn(
                    "junction/outside.md",
                    {item.path for item in findings},
                )
            finally:
                if junction.exists():
                    junction.rmdir()


if __name__ == "__main__":
    unittest.main()
