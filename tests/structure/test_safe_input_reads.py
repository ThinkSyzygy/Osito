from __future__ import annotations

import os
from pathlib import Path
import runpy
import subprocess
from types import SimpleNamespace
import tempfile
import unittest
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ID = "safe-input-project"
TEMPLATE = """---
type: project
id: "INDEX-{{project_id}}"
project_id: "{{project_id}}"
owner: "{{owner}}"
created: "{{date}}"
---

# {{project_title}}
"""


def load_script(relative_path: str) -> SimpleNamespace:
    script_path = REPOSITORY_ROOT.joinpath(relative_path)
    return SimpleNamespace(
        **runpy.run_path(
            str(script_path),
            run_name=f"osito_safe_input_test_{script_path.stem}",
        )
    )


create_project = load_script("scripts/setup/create_project.py")
archive_project = load_script("scripts/maintenance/archive_project.py")
fs_safe = create_project.fs_safe


class SafeInputReadTests(unittest.TestCase):
    def make_repository(self, parent: Path) -> Path:
        root = parent / "repository"
        templates = root / "templates" / "project"
        templates.mkdir(parents=True)
        (templates / "project-charter.md").write_text(TEMPLATE, encoding="utf-8")
        (templates / "project-index.md").write_text(TEMPLATE, encoding="utf-8")
        config = root / "config"
        config.mkdir()
        (config / "osito.example.yaml").write_text(
            "workspace:\n  project_root: projects\n  archive_root: archive\n",
            encoding="utf-8",
        )
        return root

    def create(self, root: Path) -> dict[str, object]:
        return create_project.create_project(
            root,
            project_id=PROJECT_ID,
            name="Safe Input Project",
            owner="Example Owner",
            created="2032-06-14",
        )

    def assert_no_created_project(self, root: Path) -> None:
        for parent_name in ("projects", "local-projects", "replacement-projects"):
            parent = root / parent_name
            self.assertFalse((parent / PROJECT_ID).exists())
            if parent.is_dir():
                self.assertEqual([], list(parent.glob(".osito-create-*")))

    def assert_create_fails(self, root: Path, hook) -> None:
        with mock.patch.object(fs_safe, "_test_hook", new=hook):
            with self.assertRaises(create_project.ProjectSetupError):
                self.create(root)
        self.assert_no_created_project(root)

    @staticmethod
    def is_target_read(
        event: str,
        details: dict[str, object],
        target: Path,
        expected_event: str,
    ) -> bool:
        parent = details.get("parent")
        return (
            event == expected_event
            and details.get("name") == target.name
            and getattr(parent, "path", None) == target.parent
        )

    def assert_config_symlink_replacement_fails(self, config_name: str) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            target = root / "config" / config_name
            if config_name == "osito.local.yaml":
                target.write_text(
                    "workspace:\n  project_root: local-projects\n",
                    encoding="utf-8",
                )
            held = target.with_name(f"{config_name}.original")
            external = root.parent / f"outside-{config_name}"
            external_bytes = b"workspace:\n  project_root: replacement-projects\n"
            external.write_bytes(external_bytes)
            probe = root / ".config-symlink-probe"
            try:
                probe.symlink_to(external)
            except (NotImplementedError, OSError) as exc:
                self.skipTest(f"File symlinks are unavailable in this test environment: {exc}")
            else:
                probe.unlink()
            fired = False

            def replace_with_symlink(event: str, details: dict[str, object]) -> None:
                nonlocal fired
                if not fired and self.is_target_read(
                    event,
                    details,
                    target,
                    "before_file_read",
                ):
                    target.rename(held)
                    target.symlink_to(external)
                    fired = True

            try:
                self.assert_create_fails(root, replace_with_symlink)
                self.assertTrue(fired)
                self.assertEqual(external_bytes, external.read_bytes())
            finally:
                if fired:
                    target.unlink()
                    held.rename(target)

    def test_normal_creation_reads_bounded_inputs_successfully(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            external = root.parent / "outside-sensitive.txt"
            external_bytes = b"outside sentinel\n"
            external.write_bytes(external_bytes)

            result = self.create(root)

            self.assertEqual("created", result["status"])
            project = root / str(result["destination"])
            self.assertTrue((project / "project.yaml").is_file())
            rendered = (project / "project-index.md").read_text(encoding="utf-8")
            self.assertIn("# Safe Input Project", rendered)
            self.assertNotIn("{{", rendered)
            self.assertEqual(external_bytes, external.read_bytes())
            self.assertEqual([], list(project.parent.glob(".osito-create-*")))

    def test_template_regular_replacement_before_open_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            target = root / "templates" / "project" / "project-charter.md"
            held = target.with_name("project-charter.original.md")
            fired = False

            def replace_before_open(event: str, details: dict[str, object]) -> None:
                nonlocal fired
                if not fired and self.is_target_read(event, details, target, "before_file_read"):
                    target.rename(held)
                    target.write_text("# unreviewed replacement\n", encoding="utf-8")
                    fired = True

            self.assert_create_fails(root, replace_before_open)
            self.assertTrue(fired)
            self.assertEqual(TEMPLATE, held.read_text(encoding="utf-8"))

    def test_template_hardlink_replacement_before_open_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            target = root / "templates" / "project" / "project-charter.md"
            held = target.with_name("project-charter.original.md")
            external = root.parent / "outside-hardlink-target.md"
            external_bytes = b"outside hardlink sentinel\n"
            external.write_bytes(external_bytes)
            original_link_count = external.stat().st_nlink
            probe = root / ".hardlink-probe"
            try:
                os.link(external, probe)
            except (NotImplementedError, OSError) as exc:
                self.skipTest(f"Hardlinks are unavailable in this test environment: {exc}")
            else:
                probe.unlink()
            fired = False

            def replace_with_hardlink(event: str, details: dict[str, object]) -> None:
                nonlocal fired
                if not fired and self.is_target_read(event, details, target, "before_file_read"):
                    target.rename(held)
                    os.link(external, target)
                    fired = True

            try:
                self.assert_create_fails(root, replace_with_hardlink)
                self.assertTrue(fired)
                self.assertEqual(external_bytes, external.read_bytes())
            finally:
                if fired:
                    target.unlink()
                    held.rename(target)

            self.assertEqual(external_bytes, external.read_bytes())
            self.assertEqual(original_link_count, external.stat().st_nlink)

    def test_template_symlink_replacement_before_open_fails_when_supported(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            target = root / "templates" / "project" / "project-charter.md"
            held = target.with_name("project-charter.original.md")
            external = root.parent / "outside-symlink-target.md"
            external_bytes = b"outside symlink sentinel\n"
            external.write_bytes(external_bytes)
            probe = root / ".symlink-probe"
            try:
                probe.symlink_to(external)
            except (NotImplementedError, OSError) as exc:
                self.skipTest(f"File symlinks are unavailable in this test environment: {exc}")
            else:
                probe.unlink()
            fired = False

            def replace_with_symlink(event: str, details: dict[str, object]) -> None:
                nonlocal fired
                if not fired and self.is_target_read(event, details, target, "before_file_read"):
                    target.rename(held)
                    target.symlink_to(external)
                    fired = True

            try:
                self.assert_create_fails(root, replace_with_symlink)
                self.assertTrue(fired)
                self.assertEqual(external_bytes, external.read_bytes())
            finally:
                if fired:
                    target.unlink()
                    held.rename(target)

            self.assertEqual(external_bytes, external.read_bytes())

    def test_example_config_regular_replacement_before_open_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            target = root / "config" / "osito.example.yaml"
            held = target.with_name("osito.example.original.yaml")
            fired = False

            def replace_example(event: str, details: dict[str, object]) -> None:
                nonlocal fired
                if not fired and self.is_target_read(event, details, target, "before_file_read"):
                    target.rename(held)
                    target.write_text(
                        "workspace:\n  project_root: replacement-projects\n",
                        encoding="utf-8",
                    )
                    fired = True

            self.assert_create_fails(root, replace_example)
            self.assertTrue(fired)

    def test_local_config_regular_replacement_before_open_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            target = root / "config" / "osito.local.yaml"
            target.write_text(
                "workspace:\n  project_root: local-projects\n  archive_root: local-archive\n",
                encoding="utf-8",
            )
            held = target.with_name("osito.local.original.yaml")
            fired = False

            def replace_local(event: str, details: dict[str, object]) -> None:
                nonlocal fired
                if not fired and self.is_target_read(event, details, target, "before_file_read"):
                    target.rename(held)
                    target.write_text(
                        "workspace:\n  project_root: replacement-projects\n",
                        encoding="utf-8",
                    )
                    fired = True

            self.assert_create_fails(root, replace_local)
            self.assertTrue(fired)

    def test_example_config_symlink_replacement_before_open_fails_when_supported(self):
        self.assert_config_symlink_replacement_fails("osito.example.yaml")

    def test_local_config_symlink_replacement_before_open_fails_when_supported(self):
        self.assert_config_symlink_replacement_fails("osito.local.yaml")

    def test_config_directory_junction_swap_fails_without_external_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            root = self.make_repository(parent)
            configured = root / "config"
            held = root / "config-held"
            external = parent / "external-config"
            external.mkdir()
            external_config = external / "osito.example.yaml"
            external_bytes = b"workspace:\n  project_root: replacement-projects\n"
            external_config.write_bytes(external_bytes)
            target = configured / "osito.example.yaml"
            fired = False

            def swap_config_directory(event: str, details: dict[str, object]) -> None:
                nonlocal fired
                if not fired and self.is_target_read(
                    event,
                    details,
                    target,
                    "before_file_read",
                ):
                    configured.rename(held)
                    if os.name == "nt":
                        result = subprocess.run(
                            ["cmd", "/d", "/c", "mklink", "/J", str(configured), str(external)],
                            check=False,
                            capture_output=True,
                            text=True,
                        )
                        if result.returncode != 0:
                            self.skipTest("Directory junctions unavailable in this Windows environment.")
                    else:
                        configured.symlink_to(external, target_is_directory=True)
                    fired = True

            try:
                self.assert_create_fails(root, swap_config_directory)
                self.assertTrue(fired)
                self.assertEqual(external_bytes, external_config.read_bytes())
            finally:
                if configured.is_symlink():
                    configured.unlink()
                elif getattr(configured, "is_junction", lambda: False)():
                    configured.rmdir()

    def test_archive_config_replacement_fails_without_moving_project(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            created = self.create(root)
            source = root / str(created["destination"])
            target = root / "config" / "osito.local.yaml"
            target.write_text(
                "workspace:\n  project_root: projects\n  archive_root: archive\n",
                encoding="utf-8",
            )
            held = target.with_name("osito.local.original.yaml")
            external = root.parent / "outside-archive-config.txt"
            external_bytes = b"outside archive sentinel\n"
            external.write_bytes(external_bytes)
            fired = False

            def replace_local(event: str, details: dict[str, object]) -> None:
                nonlocal fired
                if not fired and self.is_target_read(event, details, target, "before_file_read"):
                    target.rename(held)
                    target.write_text(
                        "workspace:\n  project_root: replacement-projects\n  archive_root: archive\n",
                        encoding="utf-8",
                    )
                    fired = True

            with mock.patch.object(fs_safe, "_test_hook", new=replace_local):
                with self.assertRaises(archive_project.ArchiveError):
                    archive_project.archive_project(
                        root,
                        project_id=PROJECT_ID,
                        archived_on="2032-07-01",
                    )

            self.assertTrue(fired)
            self.assertTrue(source.is_dir())
            self.assertFalse((root / "archive" / PROJECT_ID).exists())
            self.assertFalse((root / "replacement-projects" / PROJECT_ID).exists())
            self.assertEqual(external_bytes, external.read_bytes())

    def test_oversized_config_fails_before_project_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            target = root / "config" / "osito.example.yaml"
            target.write_bytes(b"x" * (create_project.MAX_CONFIG_BYTES + 1))

            with self.assertRaises(create_project.ProjectSetupError):
                self.create(root)

            self.assert_no_created_project(root)

    def test_oversized_template_fails_before_project_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            target = root / "templates" / "project" / "project-index.md"
            target.write_bytes(b"x" * (create_project.MAX_TEMPLATE_BYTES + 1))

            with self.assertRaises(create_project.ProjectSetupError):
                self.create(root)

            self.assert_no_created_project(root)

    def test_invalid_utf8_input_fails_before_project_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            target = root / "templates" / "project" / "project-index.md"
            target.write_bytes(b"valid prefix\n\xff\xfe\n")

            with self.assertRaises(create_project.ProjectSetupError):
                self.create(root)

            self.assert_no_created_project(root)

    def test_template_becoming_non_regular_before_open_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            target = root / "templates" / "project" / "project-index.md"
            held = target.with_name("project-index.original.md")
            fired = False

            def replace_with_directory(event: str, details: dict[str, object]) -> None:
                nonlocal fired
                if not fired and self.is_target_read(event, details, target, "before_file_read"):
                    target.rename(held)
                    target.mkdir()
                    fired = True

            self.assert_create_fails(root, replace_with_directory)
            self.assertTrue(fired)
            self.assertTrue(target.is_dir())
            self.assertEqual(TEMPLATE, held.read_text(encoding="utf-8"))

    def test_post_open_name_replacement_fails_without_reporting_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            target = root / "templates" / "project" / "project-charter.md"
            held = target.with_name("project-charter.opened.md")
            external = root.parent / "outside-post-open.txt"
            external_bytes = b"outside post-open sentinel\n"
            external.write_bytes(external_bytes)
            fired = False

            def replace_after_open(event: str, details: dict[str, object]) -> None:
                nonlocal fired
                if not fired and self.is_target_read(event, details, target, "file_read_opened"):
                    target.rename(held)
                    target.write_text("# post-open replacement\n", encoding="utf-8")
                    fired = True

            self.assert_create_fails(root, replace_after_open)
            self.assertTrue(fired)
            self.assertEqual(TEMPLATE, held.read_text(encoding="utf-8"))
            self.assertEqual(external_bytes, external.read_bytes())

    def test_in_place_change_after_open_fails_without_reporting_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            target = root / "templates" / "project" / "project-charter.md"
            replacement = "# changed while the input handle was open\n"
            fired = False

            def mutate_after_open(event: str, details: dict[str, object]) -> None:
                nonlocal fired
                if not fired and self.is_target_read(
                    event,
                    details,
                    target,
                    "file_read_opened",
                ):
                    target.write_text(replacement, encoding="utf-8")
                    fired = True

            self.assert_create_fails(root, mutate_after_open)
            self.assertTrue(fired)
            self.assertEqual(replacement, target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
