from __future__ import annotations

from contextlib import ExitStack
import json
import os
from pathlib import Path
import runpy
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def load_script(relative_path: str) -> SimpleNamespace:
    script_path = REPOSITORY_ROOT.joinpath(relative_path)
    namespace = runpy.run_path(
        str(script_path),
        run_name=f"osito_cleanup_test_{script_path.stem}",
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


class ConservativeCleanupTests(unittest.TestCase):
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

    def create_fixture_project(self, root: Path) -> dict[str, object]:
        return create_project.create_project(
            root,
            project_id="demo-project",
            name="Demo Project",
            created="2031-04-12",
        )

    def archive_preview(self, root: Path) -> dict[str, object]:
        return archive_project.archive_project(
            root,
            project_id="demo-project",
            archived_on="2031-05-01",
            reason="Reviewed closeout",
        )

    def apply_archive(
        self,
        root: Path,
        preview: dict[str, object],
    ) -> dict[str, object]:
        return archive_project.archive_project(
            root,
            project_id="demo-project",
            archived_on="2031-05-01",
            reason="Reviewed closeout",
            apply=True,
            approval=archive_project.APPROVAL_PHRASE,
            reviewed_hash=str(preview["preview_manifest_hash"]),
            reviewer="Example Reviewer",
        )

    def assert_no_cleanup_quarantine(self, directory: Path) -> None:
        self.assertEqual([], list(directory.glob(".osito-cleanup-*")))

    def test_normal_cleanup_removes_only_verified_file_and_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with fs_safe.pin_root(directory) as parent:
                content = b"owned temporary\n"
                file_identity = fs_safe.write_file_exclusive(parent, "owned.tmp", content)
                child = fs_safe.open_child_directory(parent, "owned-dir", create=True)
                directory_identity = child.identity
                child.close()

                fs_safe.remove_file(
                    parent,
                    "owned.tmp",
                    expected_identity=file_identity,
                    expected_content=content,
                )
                fs_safe.remove_empty_directory(
                    parent,
                    "owned-dir",
                    expected_identity=directory_identity,
                )

            self.assertFalse((directory / "owned.tmp").exists())
            self.assertFalse((directory / "owned-dir").exists())
            self.assert_no_cleanup_quarantine(directory)

    def test_foreign_file_replacement_at_cleanup_boundary_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            candidate = directory / "candidate.tmp"
            moved_owned = directory / "owned-before-replacement.tmp"
            replaced = False

            def replace_before_remove(event: str, details: dict[str, object]) -> None:
                nonlocal replaced
                if event == "before_remove_file" and details["name"] == candidate.name:
                    candidate.rename(moved_owned)
                    candidate.write_bytes(b"foreign replacement\n")
                    replaced = True

            with fs_safe.pin_root(directory) as parent:
                expected = b"owned temporary\n"
                identity = fs_safe.write_file_exclusive(parent, candidate.name, expected)
                with mock.patch.object(fs_safe, "_test_hook", new=replace_before_remove):
                    with self.assertRaises(fs_safe.IdentityChangedError) as caught:
                        fs_safe.remove_file(
                            parent,
                            candidate.name,
                            expected_identity=identity,
                            expected_content=expected,
                        )

            self.assertTrue(replaced)
            self.assertEqual(b"foreign replacement\n", candidate.read_bytes())
            self.assertEqual(b"owned temporary\n", moved_owned.read_bytes())
            self.assertIn("manual inspection", str(caught.exception))
            self.assert_no_cleanup_quarantine(directory)

    def test_same_identity_file_with_changed_content_is_restored_not_deleted(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            candidate = directory / "candidate.tmp"
            identity_before = None

            def mutate_before_remove(event: str, details: dict[str, object]) -> None:
                if event == "before_remove_file" and details["name"] == candidate.name:
                    candidate.write_bytes(b"foreign in-place content\n")

            with fs_safe.pin_root(directory) as parent:
                expected = b"owned temporary\n"
                identity_before = fs_safe.write_file_exclusive(parent, candidate.name, expected)
                with mock.patch.object(fs_safe, "_test_hook", new=mutate_before_remove):
                    with self.assertRaises(fs_safe.IdentityChangedError):
                        fs_safe.remove_file(
                            parent,
                            candidate.name,
                            expected_identity=identity_before,
                            expected_content=expected,
                        )
                identity_after = fs_safe.child_identity(parent, candidate.name, directory=False)

            self.assertEqual(identity_before, identity_after)
            self.assertEqual(b"foreign in-place content\n", candidate.read_bytes())
            self.assert_no_cleanup_quarantine(directory)

    def test_foreign_replacement_is_preserved_even_when_identity_appears_equal(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            candidate = directory / "candidate.tmp"
            moved_owned = directory / "owned-before-replacement.tmp"

            def replace_before_remove(event: str, details: dict[str, object]) -> None:
                if event == "before_remove_file" and details["name"] == candidate.name:
                    candidate.rename(moved_owned)
                    candidate.write_bytes(b"foreign replacement\n")

            with fs_safe.pin_root(directory) as parent:
                expected = b"owned temporary\n"
                identity = fs_safe.write_file_exclusive(parent, candidate.name, expected)
                identity_reader = (
                    "_windows_identity" if os.name == "nt" else "_posix_identity"
                )
                original_inspect_child = fs_safe.inspect_child

                def inspect_as_reused_identity(parent, name):
                    metadata = original_inspect_child(parent, name)
                    return fs_safe.ChildMetadata(
                        identity=identity,
                        kind=metadata.kind,
                        link_count=metadata.link_count,
                    )

                with ExitStack() as stack:
                    stack.enter_context(
                        mock.patch.object(fs_safe, identity_reader, return_value=identity)
                    )
                    if os.name != "nt":
                        stack.enter_context(
                            mock.patch.object(
                                fs_safe,
                                "inspect_child",
                                side_effect=inspect_as_reused_identity,
                            )
                        )
                    stack.enter_context(
                        mock.patch.object(fs_safe, "_test_hook", new=replace_before_remove)
                    )
                    with self.assertRaises(fs_safe.IdentityChangedError) as caught:
                        fs_safe.remove_file(
                            parent,
                            candidate.name,
                            expected_identity=identity,
                            expected_content=expected,
                        )

            self.assertEqual(b"foreign replacement\n", candidate.read_bytes())
            self.assertEqual(expected, moved_owned.read_bytes())
            self.assertIn(candidate.name, str(caught.exception))
            self.assertIn("manually", str(caught.exception))
            self.assert_no_cleanup_quarantine(directory)

    def test_empty_and_nonempty_directory_replacements_are_preserved(self):
        for nonempty in (False, True):
            with self.subTest(nonempty=nonempty), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                candidate = directory / "candidate-dir"
                moved_owned = directory / "owned-before-replacement-dir"
                replaced = False

                def replace_before_remove(event: str, details: dict[str, object]) -> None:
                    nonlocal replaced
                    if (
                        event == "before_remove_empty_directory"
                        and details["name"] == candidate.name
                    ):
                        candidate.rename(moved_owned)
                        candidate.mkdir()
                        if nonempty:
                            (candidate / "foreign.txt").write_text(
                                "foreign replacement\n",
                                encoding="utf-8",
                            )
                        replaced = True

                with fs_safe.pin_root(directory) as parent:
                    child = fs_safe.open_child_directory(parent, candidate.name, create=True)
                    identity = child.identity
                    child.close()
                    with mock.patch.object(fs_safe, "_test_hook", new=replace_before_remove):
                        with self.assertRaises(fs_safe.IdentityChangedError):
                            fs_safe.remove_empty_directory(
                                parent,
                                candidate.name,
                                expected_identity=identity,
                            )

                self.assertTrue(replaced)
                self.assertTrue(candidate.is_dir())
                self.assertTrue(moved_owned.is_dir())
                if nonempty:
                    self.assertEqual(
                        "foreign replacement\n",
                        (candidate / "foreign.txt").read_text(encoding="utf-8"),
                    )
                else:
                    self.assertEqual([], list(candidate.iterdir()))
                self.assert_no_cleanup_quarantine(directory)

    def test_publication_temp_replacement_is_preserved_and_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            final = directory / "ARCHIVE_MANIFEST.json"
            moved_owned = directory / "owned-publish-temp.tmp"
            replacement_name = ""

            def interfere(event: str, details: dict[str, object]) -> None:
                nonlocal replacement_name
                if (
                    event == "before_rename"
                    and details["destination_name"] == final.name
                ):
                    raise fs_safe.FilesystemSafetyError("force publication cleanup")
                if event == "before_remove_file" and str(details["name"]).startswith(
                    ".osito-publish-"
                ):
                    replacement_name = str(details["name"])
                    candidate = directory / replacement_name
                    candidate.rename(moved_owned)
                    candidate.write_bytes(b"foreign publication temp\n")

            with fs_safe.pin_root(directory) as parent, mock.patch.object(
                fs_safe,
                "_test_hook",
                new=interfere,
            ):
                with self.assertRaises(fs_safe.IdentityChangedError) as caught:
                    fs_safe.publish_text_exclusive(parent, final.name, "owned manifest\n")

            self.assertTrue(replacement_name)
            self.assertFalse(final.exists())
            self.assertEqual(
                b"foreign publication temp\n",
                (directory / replacement_name).read_bytes(),
            )
            self.assertEqual(b"owned manifest\n", moved_owned.read_bytes())
            self.assertIn(replacement_name, str(caught.exception))
            self.assertIn("manual inspection", str(caught.exception))
            self.assert_no_cleanup_quarantine(directory)

    def test_project_content_mutation_after_publication_is_left_intact(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            destination = root / "projects" / "demo-project"

            def mutate_before_success(event: str, _details: dict[str, object]) -> None:
                if event == "create_before_success":
                    (destination / "project.yaml").write_text(
                        "foreign in-place project content\n",
                        encoding="utf-8",
                    )

            with mock.patch.object(fs_safe, "_test_hook", new=mutate_before_success):
                with self.assertRaises(create_project.ProjectSetupError) as caught:
                    self.create_fixture_project(root)

            self.assertTrue(destination.is_dir())
            self.assertEqual(
                "foreign in-place project content\n",
                (destination / "project.yaml").read_text(encoding="utf-8"),
            )
            self.assertIn("Inspect projects", str(caught.exception))

    def test_foreign_manifest_replacement_after_publication_is_left_intact(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            self.create_fixture_project(root)
            preview = self.archive_preview(root)
            destination = root / "archive" / "demo-project"
            manifest = destination / "ARCHIVE_MANIFEST.json"

            def replace_manifest(event: str, _details: dict[str, object]) -> None:
                if event == "archive_before_success":
                    manifest.unlink()
                    manifest.write_text("foreign manifest replacement\n", encoding="utf-8")

            with mock.patch.object(fs_safe, "_test_hook", new=replace_manifest):
                with self.assertRaises(archive_project.ArchiveError) as caught:
                    self.apply_archive(root, preview)

            self.assertFalse((root / "projects" / "demo-project").exists())
            self.assertTrue(destination.is_dir())
            self.assertEqual(
                "foreign manifest replacement\n",
                manifest.read_text(encoding="utf-8"),
            )
            self.assertIn("archive/demo-project/ARCHIVE_MANIFEST.json", str(caught.exception))
            self.assertIn("manually", str(caught.exception))

    def test_restored_same_manifest_is_not_deleted_after_post_publish_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            self.create_fixture_project(root)
            preview = self.archive_preview(root)
            destination = root / "archive" / "demo-project"
            manifest = destination / "ARCHIVE_MANIFEST.json"
            holding = destination / "manifest-held-temporarily.json"
            identities: list[object] = []

            def restore_then_fail(event: str, details: dict[str, object]) -> None:
                if event == "archive_before_success":
                    archive_pin = details["destination"]
                    identities.append(
                        fs_safe.child_identity(
                            archive_pin,
                            manifest.name,
                            directory=False,
                        )
                    )
                    manifest.rename(holding)
                    holding.rename(manifest)
                    identities.append(
                        fs_safe.child_identity(
                            archive_pin,
                            manifest.name,
                            directory=False,
                        )
                    )
                    raise fs_safe.FilesystemSafetyError(
                        "fail after a final pathname disappeared and was restored"
                    )

            with mock.patch.object(fs_safe, "_test_hook", new=restore_then_fail):
                with self.assertRaises(archive_project.ArchiveError) as caught:
                    self.apply_archive(root, preview)

            self.assertEqual(2, len(identities))
            self.assertEqual(identities[0], identities[1])
            self.assertFalse((root / "projects" / "demo-project").exists())
            self.assertTrue(manifest.is_file())
            parsed = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual("demo-project", parsed["project_id"])
            self.assertIn("archive/demo-project/ARCHIVE_MANIFEST.json", str(caught.exception))

    def test_post_manifest_archive_relocation_preserves_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.make_repository(Path(temporary))
            self.create_fixture_project(root)
            preview = self.archive_preview(root)
            destination = root / "archive" / "demo-project"
            holding = root / "archive" / "relocated-after-manifest"

            def relocate_after_manifest(event: str, _details: dict[str, object]) -> None:
                if event == "archive_before_success":
                    destination.rename(holding)

            with mock.patch.object(fs_safe, "_test_hook", new=relocate_after_manifest):
                with self.assertRaises(archive_project.ArchiveError) as caught:
                    self.apply_archive(root, preview)

            self.assertFalse((root / "projects" / "demo-project").exists())
            self.assertFalse(destination.exists())
            self.assertTrue(holding.is_dir())
            manifest = holding / "ARCHIVE_MANIFEST.json"
            self.assertTrue(manifest.is_file())
            self.assertEqual(
                "demo-project",
                json.loads(manifest.read_text(encoding="utf-8"))["project_id"],
            )
            self.assertIn("archive/demo-project/ARCHIVE_MANIFEST.json", str(caught.exception))
            self.assertIn("manually", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
