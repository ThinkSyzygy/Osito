from __future__ import annotations

import json
import os
import runpy
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def load_script(relative_path: str) -> SimpleNamespace:
    script_path = REPOSITORY_ROOT.joinpath(relative_path)
    namespace = runpy.run_path(
        str(script_path),
        run_name=f"osito_test_{script_path.stem}",
    )
    return SimpleNamespace(**namespace)


create_project = load_script("scripts/setup/create_project.py")
archive_project = load_script("scripts/maintenance/archive_project.py")
fs_safe = create_project.fs_safe


TEMPLATE = """---
type: project
id: "INDEX-{{project_id}}"
project_id: "{{project_id}}"
status: active
owner: "{{owner}}"
created: "{{date}}"
updated: "{{date}}"
source_links: []
related_ids: []
---

# {{project_title}}

This record requires human review.
"""


class SetupAndMaintenanceTests(unittest.TestCase):
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

    def create_fixture_project(
        self,
        root: Path,
        project_id: str = "demo-project",
    ) -> dict[str, object]:
        return create_project.create_project(
            root,
            project_id=project_id,
            name="Demo Project",
            created="2031-04-12",
        )

    def archive_preview(
        self,
        root: Path,
        project_id: str = "demo-project",
    ) -> dict[str, object]:
        return archive_project.archive_project(
            root,
            project_id=project_id,
            archived_on="2031-05-01",
            reason="Reviewed closeout",
        )

    def apply_archive(
        self,
        root: Path,
        preview: dict[str, object],
        project_id: str = "demo-project",
    ) -> dict[str, object]:
        return archive_project.archive_project(
            root,
            project_id=project_id,
            archived_on="2031-05-01",
            reason="Reviewed closeout",
            apply=True,
            approval=archive_project.APPROVAL_PHRASE,
            reviewed_hash=str(preview["preview_manifest_hash"]),
            reviewer="Example Reviewer",
        )

    def make_directory_link(self, link: Path, target: Path) -> None:
        if os.name == "nt":
            result = subprocess.run(
                ["cmd", "/d", "/c", "mklink", "/J", str(link), str(target)],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                self.skipTest("Directory junctions unavailable in this Windows test environment.")
            return
        try:
            os.symlink(target, link, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"Directory symlinks unavailable in this test environment: {exc}")

    def remove_directory_link(self, link: Path) -> None:
        if link.is_symlink():
            link.unlink()
        elif link.exists():
            link.rmdir()

    def assert_no_operation_temporaries(self, *directories: Path) -> None:
        for directory in directories:
            if directory.is_dir():
                self.assertEqual([], list(directory.glob(".osito-create-*")))
                self.assertEqual([], list(directory.glob(".osito-publish-*.tmp")))

    def test_create_project_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            result = create_project.create_project(
                root,
                project_id="demo-project",
                name="Demo Project",
                created="2031-04-12",
                dry_run=True,
            )
            self.assertEqual("dry_run", result["status"])
            self.assertFalse((root / "projects").exists())

    def test_create_project_renders_templates_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            result = create_project.create_project(
                root,
                project_id="demo-project",
                name="Demo Project",
                owner="Example Owner",
                created="2031-04-12",
                fictional=True,
            )
            self.assertEqual("created", result["status"])
            project = root / result["destination"]
            self.assertTrue((project / "project.yaml").is_file())
            self.assertTrue((project / "project-index.md").is_file())
            project_yaml = (project / "project.yaml").read_text(encoding="utf-8")
            project_index = (project / "project-index.md").read_text(encoding="utf-8")
            self.assertIn("fictional: true", project_yaml)
            self.assertIn('id: "INDEX-demo-project"', project_index)
            self.assertNotIn("{{", project_index)
            for directory in create_project.PROJECT_DIRECTORIES:
                self.assertTrue((project / directory).is_dir())
            self.assert_no_operation_temporaries(project.parent)
            with self.assertRaises(create_project.ProjectExistsError):
                create_project.create_project(
                    root,
                    project_id="demo-project",
                    name="Demo Project",
                    created="2031-04-12",
                )

            ordinary = create_project.create_project(
                root,
                project_id="ordinary-project",
                name="Ordinary Project",
                created="2031-04-12",
            )
            ordinary_yaml = (root / ordinary["destination"] / "project.yaml").read_text(encoding="utf-8")
            self.assertIn("fictional: false", ordinary_yaml)

    def test_local_configuration_is_preferred_with_example_fallback(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            fallback = create_project.create_project(
                root,
                project_id="fallback-project",
                name="Fallback Project",
                created="2031-04-12",
                dry_run=True,
            )
            self.assertEqual("projects/fallback-project", fallback["destination"])

            (root / "config" / "osito.local.yaml").write_text(
                "workspace:\n"
                '  project_root: "local-projects"\n'
                "  archive_root: local-archive # reviewed local override\n",
                encoding="utf-8",
            )
            local = create_project.create_project(
                root,
                project_id="ORION",
                name="Fictional Orion",
                created="2031-04-12",
            )
            self.assertEqual("local-projects/ORION", local["destination"])

            preview = archive_project.archive_project(
                root,
                project_id="ORION",
                archived_on="2031-05-01",
            )
            self.assertEqual("local-projects/ORION", preview["source"])
            self.assertEqual("local-archive/ORION", preview["destination"])

    def test_archive_is_preview_only_until_exact_approval(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            create_project.create_project(
                root,
                project_id="demo-project",
                name="Demo Project",
                created="2031-04-12",
            )
            archive_reason = "Reviewed fixture closeout"
            preview = archive_project.archive_project(
                root,
                project_id="demo-project",
                archived_on="2031-05-01",
                reason=archive_reason,
            )
            self.assertEqual("preview", preview["status"])
            self.assertEqual(64, len(preview["preview_manifest_hash"]))
            self.assertTrue((root / "projects" / "demo-project").is_dir())
            with self.assertRaises(archive_project.ArchiveError):
                archive_project.archive_project(
                    root,
                    project_id="demo-project",
                    archived_on="2031-05-01",
                    apply=True,
                    approval="not-approved",
                    reviewed_hash=preview["preview_manifest_hash"],
                    reviewer="Example Reviewer",
                    reason=archive_reason,
                )
            with self.assertRaises(archive_project.ArchiveError):
                archive_project.archive_project(
                    root,
                    project_id="demo-project",
                    archived_on="2031-05-01",
                    apply=True,
                    approval=archive_project.APPROVAL_PHRASE,
                    reviewed_hash=preview["preview_manifest_hash"],
                    reason=archive_reason,
                )
            with self.assertRaises(archive_project.ArchiveError):
                archive_project.archive_project(
                    root,
                    project_id="demo-project",
                    archived_on="2031-05-01",
                    apply=True,
                    approval=archive_project.APPROVAL_PHRASE,
                    reviewed_hash="0" * 64,
                    reviewer="Example Reviewer",
                    reason=archive_reason,
                )
            self.assertTrue((root / "projects" / "demo-project").is_dir())

            (root / "projects" / "demo-project" / "review-marker.txt").write_text(
                "Changed after the first preview.\n",
                encoding="utf-8",
            )
            with self.assertRaises(archive_project.ArchiveError):
                archive_project.archive_project(
                    root,
                    project_id="demo-project",
                    archived_on="2031-05-01",
                    apply=True,
                    approval=archive_project.APPROVAL_PHRASE,
                    reviewed_hash=preview["preview_manifest_hash"],
                    reviewer="Example Reviewer",
                    reason=archive_reason,
                )
            self.assertTrue((root / "projects" / "demo-project").is_dir())

            current_preview = archive_project.archive_project(
                root,
                project_id="demo-project",
                archived_on="2031-05-01",
                reason=archive_reason,
            )
            source = root / "projects" / "demo-project"
            source_identity = source.stat(follow_symlinks=False)
            source_yaml = (source / "project.yaml").read_bytes()
            applied = archive_project.archive_project(
                root,
                project_id="demo-project",
                archived_on="2031-05-01",
                apply=True,
                approval=archive_project.APPROVAL_PHRASE,
                reviewed_hash=current_preview["preview_manifest_hash"],
                reviewer="Example Reviewer",
                reason=archive_reason,
            )
            self.assertEqual("archived", applied["status"])
            self.assertFalse((root / "projects" / "demo-project").exists())
            manifest_path = root / "archive" / "demo-project" / "ARCHIVE_MANIFEST.json"
            self.assertTrue(manifest_path.is_file())
            archived_project = manifest_path.parent
            archived_identity = archived_project.stat(follow_symlinks=False)
            self.assertEqual(
                (source_identity.st_dev, source_identity.st_ino),
                (archived_identity.st_dev, archived_identity.st_ino),
            )
            self.assertEqual(source_yaml, (archived_project / "project.yaml").read_bytes())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual("Example Reviewer", manifest["reviewer"])
            self.assertEqual(current_preview["preview_manifest_hash"], manifest["reviewed_hash"])
            self.assertEqual(current_preview["preview_manifest_hash"], manifest["preview_manifest_hash"])
            self.assertEqual(current_preview["content_hash"], manifest["content_hash_before_manifest"])
            self.assert_no_operation_temporaries(archived_project)

    def test_unsafe_storage_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            with self.assertRaises(create_project.ProjectSetupError):
                create_project.create_project(
                    root,
                    project_id="demo-project",
                    name="Demo Project",
                    created="2031-04-12",
                    projects_dir="../outside",
                )
            with self.assertRaises(create_project.ProjectSetupError):
                windows_absolute = "C:" + chr(92) + "outside"
                create_project.create_project(
                    root,
                    project_id="demo-project",
                    name="Demo Project",
                    created="2031-04-12",
                    projects_dir=windows_absolute,
                )

            (root / "config" / "osito.local.yaml").write_text(
                "workspace:\n  project_root: {unsafe: mapping}\n",
                encoding="utf-8",
            )
            with self.assertRaises(create_project.ProjectSetupError):
                create_project.create_project(
                    root,
                    project_id="demo-project",
                    name="Demo Project",
                    created="2031-04-12",
                )

    @unittest.skipUnless(os.name == "nt", "Windows case-insensitive path regression")
    def test_archive_rejects_case_variant_nested_roots_on_windows(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            self.create_fixture_project(root)
            with self.assertRaises(archive_project.ArchiveError):
                archive_project.archive_project(
                    root,
                    project_id="demo-project",
                    archive_dir="PROJECTS/archive",
                    archived_on="2031-05-01",
                )
            self.assertTrue((root / "projects" / "demo-project").is_dir())
            self.assertFalse((root / "projects" / "archive").exists())

    def test_template_directory_links_are_rejected_even_for_dry_run(self):
        for relative in (Path("templates"), Path("templates") / "project"):
            with self.subTest(path=relative), tempfile.TemporaryDirectory() as temporary:
                parent = Path(temporary)
                root = self.make_repository(parent)
                rejected_path = root / relative
                external = parent / f"external-{relative.name}"
                rejected_path.rename(external)
                self.make_directory_link(rejected_path, external)
                try:
                    with self.assertRaises(create_project.ProjectSetupError):
                        create_project.create_project(
                            root,
                            project_id="demo-project",
                            name="Demo Project",
                            created="2031-04-12",
                            dry_run=True,
                        )
                finally:
                    self.remove_directory_link(rejected_path)

    def test_archive_rejects_preexisting_reserved_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            created = create_project.create_project(
                root,
                project_id="demo-project",
                name="Demo Project",
                created="2031-04-12",
            )
            project = root / created["destination"]
            reserved = project / "ARCHIVE_MANIFEST.json"
            reserved.write_text("sentinel\n", encoding="utf-8")
            with self.assertRaises(archive_project.ArchiveError):
                archive_project.archive_project(
                    root,
                    project_id="demo-project",
                    archived_on="2031-05-01",
                )
            self.assertEqual("sentinel\n", reserved.read_text(encoding="utf-8"))
            self.assertFalse((root / "archive" / "demo-project").exists())

    def test_exclusive_manifest_api_preserves_existing_and_racing_destinations(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            destination = directory / "ARCHIVE_MANIFEST.json"
            destination.write_text("competitor\n", encoding="utf-8")
            with fs_safe.pin_root(directory) as directory_pin:
                with self.assertRaises(fs_safe.DestinationExistsError):
                    fs_safe.publish_text_exclusive(
                        directory_pin,
                        destination.name,
                        "replacement\n",
                    )
            self.assertEqual("competitor\n", destination.read_text(encoding="utf-8"))
            self.assert_no_operation_temporaries(directory)

            destination.unlink()

            def competing_publication(event: str, details: dict[str, object]) -> None:
                if (
                    event == "before_rename"
                    and details["destination_name"] == "ARCHIVE_MANIFEST.json"
                ):
                    destination.write_text("race winner\n", encoding="utf-8")

            with fs_safe.pin_root(directory) as directory_pin, mock.patch.object(
                fs_safe,
                "_test_hook",
                new=competing_publication,
            ):
                with self.assertRaises(fs_safe.DestinationExistsError):
                    fs_safe.publish_text_exclusive(
                        directory_pin,
                        destination.name,
                        "replacement\n",
                    )
            self.assertEqual("race winner\n", destination.read_text(encoding="utf-8"))
            self.assert_no_operation_temporaries(directory)

    def test_create_destination_race_preserves_empty_and_nonempty_competitors(self):
        for nonempty in (False, True):
            with self.subTest(nonempty=nonempty), tempfile.TemporaryDirectory() as temporary:
                root = self.make_repository(Path(temporary))
                competitor = root / "projects" / "demo-project"

                def destination_race(event: str, details: dict[str, object]) -> None:
                    if (
                        event == "before_rename"
                        and str(details["source_name"]).startswith(".osito-create-")
                        and details["destination_name"] == "demo-project"
                    ):
                        competitor.mkdir()
                        if nonempty:
                            (competitor / "competitor.txt").write_text(
                                "keep\n",
                                encoding="utf-8",
                            )

                with mock.patch.object(fs_safe, "_test_hook", new=destination_race):
                    with self.assertRaises(create_project.ProjectExistsError):
                        self.create_fixture_project(root)

                self.assertTrue(competitor.is_dir())
                self.assertFalse((competitor / "project.yaml").exists())
                if nonempty:
                    self.assertEqual(
                        "keep\n",
                        (competitor / "competitor.txt").read_text(encoding="utf-8"),
                    )
                else:
                    self.assertEqual([], list(competitor.iterdir()))
                self.assert_no_operation_temporaries(competitor.parent)

    def test_create_parent_relocation_fails_closed_and_cleans_temporary_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            holding = root / "projects-relocated"
            replacement = root / "projects"
            original_open = fs_safe.open_child_directory
            relocated = False

            def open_after_relocation(
                parent: fs_safe.PinnedDirectory,
                name: str,
                *,
                create: bool = False,
            ) -> fs_safe.PinnedDirectory:
                nonlocal relocated
                if create and name.startswith(".osito-create-") and not relocated:
                    with fs_safe.pin_root(root) as repository:
                        fs_safe.atomic_rename_no_replace(
                            repository,
                            "projects",
                            repository,
                            holding.name,
                            expected_identity=parent.identity,
                            directory=True,
                        )
                        replacement_pin = original_open(
                            repository,
                            "projects",
                            create=True,
                        )
                        replacement_pin.close()
                    relocated = True
                return original_open(parent, name, create=create)

            with mock.patch.object(
                fs_safe,
                "open_child_directory",
                new=open_after_relocation,
            ):
                with self.assertRaises(create_project.ProjectSetupError):
                    self.create_fixture_project(root)

            self.assertTrue(relocated)
            self.assertTrue(replacement.is_dir())
            self.assertEqual([], list(replacement.iterdir()))
            self.assertTrue(holding.is_dir())
            self.assertTrue((holding / "demo-project" / "project.yaml").is_file())
            self.assert_no_operation_temporaries(replacement, holding)

    def test_create_parent_link_swap_fails_closed_and_cleans_temporary_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            configured = root / "projects"
            holding = root / "projects-relocated"
            external = root.parent / "external-project-target"
            external.mkdir()
            original_open = fs_safe.open_child_directory
            swapped = False

            def open_after_swap(
                parent: fs_safe.PinnedDirectory,
                name: str,
                *,
                create: bool = False,
            ) -> fs_safe.PinnedDirectory:
                nonlocal swapped
                if create and name.startswith(".osito-create-") and not swapped:
                    with fs_safe.pin_root(root) as repository:
                        fs_safe.atomic_rename_no_replace(
                            repository,
                            "projects",
                            repository,
                            holding.name,
                            expected_identity=parent.identity,
                            directory=True,
                        )
                    self.make_directory_link(configured, external)
                    swapped = True
                return original_open(parent, name, create=create)

            try:
                with mock.patch.object(
                    fs_safe,
                    "open_child_directory",
                    new=open_after_swap,
                ):
                    with self.assertRaises(create_project.ProjectSetupError):
                        self.create_fixture_project(root)

                self.assertTrue(swapped)
                self.assertTrue(configured.is_symlink() or configured.is_junction())
                self.assertEqual([], list(external.iterdir()))
                self.assertTrue((holding / "demo-project" / "project.yaml").is_file())
                self.assert_no_operation_temporaries(external, holding)
            finally:
                self.remove_directory_link(configured)

    def test_create_final_destination_relocation_never_reports_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            destination = root / "projects" / "demo-project"
            holding = root / "projects" / "late-relocation"

            def relocate_before_success(event: str, _details: dict[str, object]) -> None:
                if event == "create_before_success":
                    destination.rename(holding)

            with mock.patch.object(fs_safe, "_test_hook", new=relocate_before_success):
                with self.assertRaises(create_project.ProjectSetupError) as caught:
                    self.create_fixture_project(root)

            self.assertIn("manually", str(caught.exception))
            self.assertFalse(destination.exists())
            self.assertTrue((holding / "project.yaml").is_file())
            self.assert_no_operation_temporaries(destination.parent)

    def test_archive_destination_race_preserves_empty_and_nonempty_competitors(self):
        for nonempty in (False, True):
            with self.subTest(nonempty=nonempty), tempfile.TemporaryDirectory() as temporary:
                root = self.make_repository(Path(temporary))
                self.create_fixture_project(root)
                preview = self.archive_preview(root)
                competitor = root / "archive" / "demo-project"

                def destination_race(event: str, details: dict[str, object]) -> None:
                    if (
                        event == "before_rename"
                        and details["directory"]
                        and details["source_name"] == "demo-project"
                        and details["destination_name"] == "demo-project"
                        and Path(details["source_parent"].path).name == "projects"
                    ):
                        competitor.mkdir()
                        if nonempty:
                            (competitor / "competitor.txt").write_text(
                                "keep\n",
                                encoding="utf-8",
                            )

                with mock.patch.object(fs_safe, "_test_hook", new=destination_race):
                    with self.assertRaises(archive_project.ArchiveError) as caught:
                        self.apply_archive(root, preview)

                self.assertIn("preserved", str(caught.exception))
                source = root / "projects" / "demo-project"
                self.assertTrue(source.is_dir())
                self.assertFalse((source / "ARCHIVE_MANIFEST.json").exists())
                self.assertTrue(competitor.is_dir())
                if nonempty:
                    self.assertEqual(
                        "keep\n",
                        (competitor / "competitor.txt").read_text(encoding="utf-8"),
                    )
                else:
                    self.assertEqual([], list(competitor.iterdir()))
                self.assert_no_operation_temporaries(source, competitor)

    def test_archive_destination_parent_relocation_rolls_back_without_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            self.create_fixture_project(root)
            preview = self.archive_preview(root)
            configured = root / "archive"
            holding = root / "archive-relocated"

            def relocate_destination(event: str, details: dict[str, object]) -> None:
                if event == "archive_parents_pinned":
                    configured.rename(holding)
                    configured.mkdir()

            with mock.patch.object(fs_safe, "_test_hook", new=relocate_destination):
                with self.assertRaises(archive_project.ArchiveError):
                    self.apply_archive(root, preview)

            source = root / "projects" / "demo-project"
            self.assertTrue(source.is_dir())
            self.assertFalse((source / "ARCHIVE_MANIFEST.json").exists())
            self.assertEqual([], list(configured.iterdir()))
            self.assertEqual([], list(holding.iterdir()))
            self.assert_no_operation_temporaries(source, configured, holding)

    def test_archive_destination_parent_link_swap_rolls_back_without_escape(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            self.create_fixture_project(root)
            preview = self.archive_preview(root)
            configured = root / "archive"
            holding = root / "archive-relocated"
            external = root.parent / "external-archive-target"
            external.mkdir()

            def swap_destination(event: str, details: dict[str, object]) -> None:
                if event == "archive_parents_pinned":
                    configured.rename(holding)
                    self.make_directory_link(configured, external)

            try:
                with mock.patch.object(fs_safe, "_test_hook", new=swap_destination):
                    with self.assertRaises(archive_project.ArchiveError):
                        self.apply_archive(root, preview)

                source = root / "projects" / "demo-project"
                self.assertTrue(source.is_dir())
                self.assertFalse((source / "ARCHIVE_MANIFEST.json").exists())
                self.assertEqual([], list(external.iterdir()))
                self.assertEqual([], list(holding.iterdir()))
                self.assert_no_operation_temporaries(source, external, holding)
            finally:
                self.remove_directory_link(configured)

    def test_archive_source_parent_relocation_never_reports_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            self.create_fixture_project(root)
            preview = self.archive_preview(root)
            configured = root / "projects"
            holding = root / "projects-relocated"
            original_open = fs_safe.open_child_directory
            relocated = False

            def open_after_source_relocation(
                parent: fs_safe.PinnedDirectory,
                name: str,
                *,
                create: bool = False,
            ) -> fs_safe.PinnedDirectory:
                nonlocal relocated
                if (
                    not create
                    and name == "demo-project"
                    and parent.path.name == "projects"
                    and not relocated
                ):
                    with fs_safe.pin_root(root) as repository:
                        fs_safe.atomic_rename_no_replace(
                            repository,
                            "projects",
                            repository,
                            holding.name,
                            expected_identity=parent.identity,
                            directory=True,
                        )
                        replacement_pin = original_open(
                            repository,
                            "projects",
                            create=True,
                        )
                        replacement_pin.close()
                    relocated = True
                return original_open(parent, name, create=create)

            with mock.patch.object(
                fs_safe,
                "open_child_directory",
                new=open_after_source_relocation,
            ):
                with self.assertRaises(archive_project.ArchiveError):
                    self.apply_archive(root, preview)

            self.assertTrue(relocated)
            restored = holding / "demo-project"
            self.assertTrue(restored.is_dir())
            self.assertFalse((configured / "demo-project").exists())
            self.assertFalse((root / "archive" / "demo-project").exists())
            self.assertFalse((restored / "ARCHIVE_MANIFEST.json").exists())
            self.assert_no_operation_temporaries(restored, configured, root / "archive")

    def test_manifest_parent_relocation_leaves_no_manifest_and_rolls_back(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            self.create_fixture_project(root)
            preview = self.archive_preview(root)
            configured = root / "archive"
            holding = root / "archive-relocated"

            def relocate_before_manifest(event: str, details: dict[str, object]) -> None:
                if event == "archive_before_manifest":
                    configured.rename(holding)
                    configured.mkdir()

            with mock.patch.object(fs_safe, "_test_hook", new=relocate_before_manifest):
                with self.assertRaises(archive_project.ArchiveError):
                    self.apply_archive(root, preview)

            source = root / "projects" / "demo-project"
            self.assertTrue(source.is_dir())
            self.assertFalse((source / "ARCHIVE_MANIFEST.json").exists())
            self.assertFalse((configured / "demo-project").exists())
            self.assertFalse((holding / "demo-project").exists())
            self.assert_no_operation_temporaries(source, configured, holding)

    def test_manifest_publication_failure_cleans_temp_and_restores_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            self.create_fixture_project(root)
            preview = self.archive_preview(root)

            def fail_manifest_rename(event: str, details: dict[str, object]) -> None:
                if (
                    event == "before_rename"
                    and details["destination_name"] == "ARCHIVE_MANIFEST.json"
                ):
                    raise fs_safe.FilesystemSafetyError(
                        "simulated manifest publication failure"
                    )

            with mock.patch.object(fs_safe, "_test_hook", new=fail_manifest_rename):
                with self.assertRaises(archive_project.ArchiveError):
                    self.apply_archive(root, preview)

            source = root / "projects" / "demo-project"
            self.assertTrue(source.is_dir())
            self.assertFalse((root / "archive" / "demo-project").exists())
            self.assertFalse((source / "ARCHIVE_MANIFEST.json").exists())
            self.assert_no_operation_temporaries(source, root / "archive")

    def test_manifest_removed_after_publication_leaves_archive_for_manual_inspection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            self.create_fixture_project(root)
            preview = self.archive_preview(root)
            manifest = root / "archive" / "demo-project" / "ARCHIVE_MANIFEST.json"

            def remove_published_manifest(event: str, details: dict[str, object]) -> None:
                if (
                    event == "after_rename"
                    and details["destination_name"] == "ARCHIVE_MANIFEST.json"
                ):
                    manifest.unlink()

            with mock.patch.object(fs_safe, "_test_hook", new=remove_published_manifest):
                with self.assertRaises(archive_project.ArchiveError) as caught:
                    self.apply_archive(root, preview)

            source = root / "projects" / "demo-project"
            archived = root / "archive" / "demo-project"
            self.assertFalse(source.exists())
            self.assertTrue((archived / "project.yaml").is_file())
            self.assertFalse((archived / "ARCHIVE_MANIFEST.json").exists())
            self.assertIn("manually", str(caught.exception))
            self.assert_no_operation_temporaries(archived)

    def test_foreign_manifest_replacement_requires_manual_inspection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            self.create_fixture_project(root)
            preview = self.archive_preview(root)
            manifest = root / "archive" / "demo-project" / "ARCHIVE_MANIFEST.json"

            def replace_published_manifest(event: str, details: dict[str, object]) -> None:
                if (
                    event == "after_rename"
                    and details["destination_name"] == "ARCHIVE_MANIFEST.json"
                ):
                    manifest.unlink()
                    manifest.write_text("foreign replacement\n", encoding="utf-8")

            with mock.patch.object(fs_safe, "_test_hook", new=replace_published_manifest):
                with self.assertRaises(archive_project.ArchiveError) as caught:
                    self.apply_archive(root, preview)

            self.assertIn("manually", str(caught.exception))
            self.assertFalse((root / "projects" / "demo-project").exists())
            self.assertEqual("foreign replacement\n", manifest.read_text(encoding="utf-8"))
            self.assert_no_operation_temporaries(manifest.parent)

    def test_archive_final_destination_relocation_never_reports_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            self.create_fixture_project(root)
            preview = self.archive_preview(root)
            destination = root / "archive" / "demo-project"
            holding = root / "archive" / "late-relocation"

            def relocate_before_success(event: str, _details: dict[str, object]) -> None:
                if event == "archive_before_success":
                    destination.rename(holding)

            with mock.patch.object(fs_safe, "_test_hook", new=relocate_before_success):
                with self.assertRaises(archive_project.ArchiveError) as caught:
                    self.apply_archive(root, preview)

            self.assertIn("manually", str(caught.exception))
            self.assertFalse(destination.exists())
            self.assertTrue((holding / "project.yaml").is_file())
            self.assertTrue((holding / "ARCHIVE_MANIFEST.json").is_file())
            self.assert_no_operation_temporaries(holding)

    def test_ambiguous_completed_archive_move_rolls_back_and_never_succeeds(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            self.create_fixture_project(root)
            preview = self.archive_preview(root)

            def ambiguous_after_move(event: str, details: dict[str, object]) -> None:
                if (
                    event == "after_rename"
                    and details["directory"]
                    and Path(details["source_parent"].path).name == "projects"
                ):
                    raise fs_safe.FilesystemSafetyError(
                        "simulated ambiguous rename completion"
                    )

            with mock.patch.object(fs_safe, "_test_hook", new=ambiguous_after_move):
                with self.assertRaises(archive_project.ArchiveError):
                    self.apply_archive(root, preview)

            source = root / "projects" / "demo-project"
            self.assertTrue(source.is_dir())
            self.assertFalse((root / "archive" / "demo-project").exists())
            self.assertFalse((source / "ARCHIVE_MANIFEST.json").exists())

    def test_ambiguous_move_with_blocked_rollback_requires_manual_inspection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            self.create_fixture_project(root)
            preview = self.archive_preview(root)
            competitor = root / "projects" / "demo-project"
            moved_once = False

            def fail_move_and_rollback(event: str, details: dict[str, object]) -> None:
                nonlocal moved_once
                if (
                    event == "after_rename"
                    and details["directory"]
                    and Path(details["source_parent"].path).name == "projects"
                ):
                    moved_once = True
                    raise fs_safe.FilesystemSafetyError(
                        "simulated ambiguous rename completion"
                    )
                if (
                    moved_once
                    and event == "before_rename"
                    and details["directory"]
                    and Path(details["source_parent"].path).name == "archive"
                ):
                    competitor.mkdir()
                    (competitor / "competitor.txt").write_text(
                        "preserve me\n",
                        encoding="utf-8",
                    )

            with mock.patch.object(fs_safe, "_test_hook", new=fail_move_and_rollback):
                with self.assertRaises(archive_project.ArchiveError) as caught:
                    self.apply_archive(root, preview)

            self.assertIn("manually", str(caught.exception))
            self.assertEqual(
                "preserve me\n",
                (competitor / "competitor.txt").read_text(encoding="utf-8"),
            )
            archived = root / "archive" / "demo-project"
            self.assertTrue(archived.is_dir())
            self.assertTrue((archived / "project.yaml").is_file())
            self.assertFalse((archived / "ARCHIVE_MANIFEST.json").exists())
            self.assert_no_operation_temporaries(competitor, archived)

    def test_unsupported_rename_backend_fails_closed_for_create_and_archive(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))

            def unsupported_directory_rename(event: str, details: dict[str, object]) -> None:
                if event == "before_rename" and details["directory"]:
                    raise fs_safe.UnsupportedFilesystemError(
                        "simulated unsupported no-replace backend"
                    )

            with mock.patch.object(
                fs_safe,
                "_test_hook",
                new=unsupported_directory_rename,
            ):
                with self.assertRaises(create_project.ProjectSetupError) as caught:
                    self.create_fixture_project(root)
            self.assertFalse((root / "projects" / "demo-project").exists())
            leftovers = list((root / "projects").glob(".osito-create-*"))
            self.assertEqual(1, len(leftovers))
            self.assertEqual(
                set(create_project.PROJECT_DIRECTORIES),
                {entry.name for entry in leftovers[0].iterdir()},
            )
            self.assertIn(leftovers[0].name, str(caught.exception.__cause__))

            self.create_fixture_project(root)
            preview = self.archive_preview(root)
            with mock.patch.object(
                fs_safe,
                "_test_hook",
                new=unsupported_directory_rename,
            ):
                with self.assertRaises(archive_project.ArchiveError):
                    self.apply_archive(root, preview)
            source = root / "projects" / "demo-project"
            self.assertTrue(source.is_dir())
            self.assertFalse((root / "archive" / "demo-project").exists())
            self.assertFalse((source / "ARCHIVE_MANIFEST.json").exists())
            self.assert_no_operation_temporaries(source, root / "archive")

    def test_archive_rejects_project_files_with_external_hardlinks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            created = create_project.create_project(
                root,
                project_id="demo-project",
                name="Demo Project",
                created="2031-04-12",
            )
            project = root / created["destination"]
            external = root / "external-hardlink-target.txt"
            external.write_text("shared content\n", encoding="utf-8")
            linked = project / "linked-evidence.txt"
            try:
                os.link(external, linked)
            except OSError as exc:
                self.skipTest(f"Hardlinks unavailable in this test environment: {exc}")

            with self.assertRaises(archive_project.ArchiveError):
                archive_project.archive_project(
                    root,
                    project_id="demo-project",
                    archived_on="2031-05-01",
                )
            self.assertTrue(project.is_dir())
            self.assertEqual("shared content\n", external.read_text(encoding="utf-8"))
            self.assertFalse((root / "archive" / "demo-project").exists())

    def test_tree_hash_is_deterministic_with_pinned_enumeration(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / "B.txt").write_text("second fixture\n", encoding="utf-8")
            (project / "a.txt").write_text("first fixture\n", encoding="utf-8")
            nested = project / "nested"
            nested.mkdir()
            (nested / "record.md").write_text("nested fixture\n", encoding="utf-8")

            first = archive_project._tree_hash(project)
            second = archive_project._tree_hash(project)
            self.assertEqual(first, second)
            self.assertEqual(3, first[1])

    def test_pin_root_rejects_an_intermediate_directory_link(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            target_parent = base / "target-parent"
            repository = target_parent / "repository"
            repository.mkdir(parents=True)
            linked_parent = base / "linked-parent"
            self.make_directory_link(linked_parent, target_parent)
            try:
                with self.assertRaises(fs_safe.FilesystemSafetyError):
                    with fs_safe.pin_root(linked_parent / "repository"):
                        self.fail("An intermediate directory link was followed.")
            finally:
                self.remove_directory_link(linked_parent)

    @unittest.skipUnless(os.name == "nt", "Windows junction regression")
    def test_archive_rejects_project_directory_junctions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            created = create_project.create_project(
                root,
                project_id="demo-project",
                name="Demo Project",
                created="2031-04-12",
            )
            project = root / created["destination"]
            external = root / "external-junction-target"
            external.mkdir()
            (external / "outside.txt").write_text("outside\n", encoding="utf-8")
            junction = project / "linked-directory"
            result = subprocess.run(
                ["cmd", "/d", "/c", "mklink", "/J", str(junction), str(external)],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                self.skipTest("Directory junctions unavailable in this Windows test environment.")
            try:
                with self.assertRaises(archive_project.ArchiveError):
                    archive_project.archive_project(
                        root,
                        project_id="demo-project",
                        archived_on="2031-05-01",
                    )
                self.assertTrue(project.is_dir())
                self.assertFalse((root / "archive" / "demo-project").exists())
                self.assertEqual("outside\n", (external / "outside.txt").read_text(encoding="utf-8"))
            finally:
                if junction.exists():
                    junction.rmdir()


if __name__ == "__main__":
    unittest.main()
