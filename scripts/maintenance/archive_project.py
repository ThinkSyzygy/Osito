#!/usr/bin/env python3
"""Preview or apply a reversible, repository-local project archive move."""

from __future__ import annotations

import argparse
from contextlib import ExitStack
from datetime import date
import hashlib
import json
from pathlib import Path, PurePosixPath
import os
import re
import sys
from typing import Sequence


REPOSITORY_CODE_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_CODE_ROOT))

from scripts.common import filesystem_safety as fs_safe


APPROVAL_PHRASE = "ARCHIVE"
PROJECT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{1,62}[A-Za-z0-9]$")
CONFIG_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")
MAX_CONFIG_BYTES = 256 * 1024


class ArchiveError(RuntimeError):
    """Raised when archive safety checks fail."""


def _minimal_yaml_scalar(raw_value: str) -> str:
    value = raw_value.strip()
    double_quoted = re.fullmatch(r'"([^"\\]*)"\s*(?:#.*)?', value)
    single_quoted = re.fullmatch(r"'([^']*)'\s*(?:#.*)?", value)
    if double_quoted or single_quoted:
        parsed = (double_quoted or single_quoted).group(1)
    else:
        value = re.split(r"\s+#", value, maxsplit=1)[0].rstrip()
        if not value or value[0] in "[{&*!|>@`" or any(character in value for character in "[]{}"):
            raise ArchiveError("Configured workspace paths must use a simple YAML scalar.")
        parsed = value
    if not parsed or any(ord(character) < 32 for character in parsed):
        raise ArchiveError("Configured workspace paths must use a nonempty printable scalar.")
    return parsed


def _config_value(config_text: str | None, section: str, key: str, default: str) -> str:
    if config_text is None:
        return default
    current_section = ""
    found: str | None = None
    for raw_line in config_text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if "\t" in raw_line:
            raise ArchiveError("The minimal configuration reader does not accept tab indentation.")
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        stripped = raw_line.strip()
        if indent == 0:
            section_match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_-]*):\s*(?:#.*)?", stripped)
            current_section = section_match.group(1) if section_match else ""
            continue
        if current_section == section and indent == 2 and ":" in stripped:
            candidate_key, value = stripped.split(":", 1)
            candidate_key = candidate_key.strip()
            if not CONFIG_KEY_RE.fullmatch(candidate_key):
                raise ArchiveError("The selected configuration contains an invalid workspace key.")
            if candidate_key == key:
                if found is not None:
                    raise ArchiveError("The selected configuration repeats a required workspace key.")
                found = _minimal_yaml_scalar(value)
    return found or default


def _load_config_text(root: Path) -> str | None:
    """Read the selected workspace configuration through pinned directories once."""

    try:
        with ExitStack() as stack:
            repository = stack.enter_context(fs_safe.pin_root(root))
            if not fs_safe.child_exists(repository, "config"):
                return None
            config_directory = fs_safe.open_child_directory(repository, "config")
            stack.callback(config_directory.close)
            if fs_safe.child_exists(config_directory, "osito.local.yaml"):
                config_name = "osito.local.yaml"
            elif fs_safe.child_exists(config_directory, "osito.example.yaml"):
                config_name = "osito.example.yaml"
            else:
                return None
            metadata = fs_safe.inspect_child(config_directory, config_name)
            if metadata.kind != "file" or metadata.link_count != 1:
                raise fs_safe.FilesystemSafetyError("Expected a single-link regular config file.")
            text, _identity = fs_safe.read_utf8_file(
                config_directory,
                config_name,
                max_bytes=MAX_CONFIG_BYTES,
                expected_identity=metadata.identity,
            )
            fs_safe.revalidate_directory(config_directory)
            fs_safe.revalidate_directory(repository)
            return text
    except fs_safe.FilesystemSafetyError as exc:
        raise ArchiveError("The selected configuration could not be read safely.") from exc


def _safe_directory_parts(value: str, label: str) -> tuple[str, ...]:
    normalized = value.replace("\\", "/")
    relative = PurePosixPath(normalized)
    if (
        relative.is_absolute()
        or re.match(r"^[A-Za-z]:", normalized)
        or normalized.startswith("//")
        or ".." in relative.parts
        or not relative.parts
    ):
        raise ArchiveError(f"{label} must be a safe repository-relative directory.")
    return tuple(relative.parts)


def _safe_directory(root: Path, value: str, label: str) -> Path:
    parts = _safe_directory_parts(value, label)
    path = root.joinpath(*parts)
    current = root
    for part in parts:
        current = current / part
        checker = getattr(current, "is_junction", None)
        try:
            observation = current.stat(follow_symlinks=False)
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise ArchiveError(f"{label} could not be inspected safely.") from exc
        if (
            current.is_symlink()
            or bool(checker and checker())
            or bool(
                getattr(observation, "st_file_attributes", 0)
                & fs_safe.FILE_ATTRIBUTE_REPARSE_POINT
            )
        ):
            raise ArchiveError(f"{label} must not traverse a link, junction, or reparse point.")
    return path


def _lexical_root(root: Path) -> Path:
    lexical = Path(os.path.abspath(os.fspath(root)))
    try:
        observation = lexical.stat(follow_symlinks=False)
    except OSError as exc:
        raise ArchiveError("Repository root does not exist or cannot be inspected.") from exc
    if not lexical.is_dir() or lexical.is_symlink():
        raise ArchiveError("Repository root must be an ordinary directory.")
    if getattr(observation, "st_file_attributes", 0) & fs_safe.FILE_ATTRIBUTE_REPARSE_POINT:
        raise ArchiveError("Repository root must not be a junction or reparse point.")
    return lexical


def _tree_hash(
    project: Path,
    *,
    excluded_relative_paths: frozenset[str] = frozenset(),
) -> tuple[str, int]:
    try:
        with fs_safe.pin_root(project) as project_pin:
            return _tree_hash_pinned(
                project_pin,
                excluded_relative_paths=excluded_relative_paths,
            )
    except fs_safe.FilesystemSafetyError as exc:
        raise ArchiveError(f"The project tree could not be inspected safely: {exc}") from exc


def _tree_hash_pinned(
    project: fs_safe.PinnedDirectory,
    *,
    excluded_relative_paths: frozenset[str] = frozenset(),
) -> tuple[str, int]:
    """Hash a project by enumerating and opening every entry through pinned handles."""

    digest = hashlib.sha256()
    count = 0

    def visit(directory: fs_safe.PinnedDirectory, prefix: str) -> None:
        nonlocal count
        for name in fs_safe.list_child_names(directory):
            relative = f"{prefix}/{name}" if prefix else name
            if relative in excluded_relative_paths:
                continue
            metadata = fs_safe.inspect_child(directory, name)
            if metadata.kind == "directory":
                digest.update(b"D\0")
                digest.update(relative.encode("utf-8"))
                digest.update(b"\0")
                child = fs_safe.open_child_directory(directory, name)
                try:
                    if child.identity != metadata.identity:
                        raise fs_safe.IdentityChangedError(
                            f"Project directory changed identity during inspection: {relative}"
                        )
                    visit(child, relative)
                finally:
                    child.close()
                continue
            if metadata.kind != "file" or metadata.link_count != 1:
                raise fs_safe.FilesystemSafetyError(
                    f"Project entry is not a single-link regular file: {relative}"
                )
            digest.update(b"F\0")
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            content, opened_identity = fs_safe.read_file(
                directory,
                name,
                expected_identity=metadata.identity,
            )
            if opened_identity != metadata.identity:
                raise fs_safe.IdentityChangedError(
                    f"Project file changed identity during inspection: {relative}"
                )
            digest.update(content)
            digest.update(b"\0")
            count += 1

    try:
        visit(project, "")
    except fs_safe.FilesystemSafetyError as exc:
        raise ArchiveError(f"The project tree could not be inspected safely: {exc}") from exc
    return digest.hexdigest(), count


def _preview_manifest(
    *,
    project_id: str,
    source: str,
    destination: str,
    file_count: int,
    content_hash: str,
    archived_on: str,
    reason: str,
) -> dict[str, object]:
    return {
        "manifest_version": "1.0",
        "project_id": project_id,
        "archived_on": archived_on,
        "source": source,
        "destination": destination,
        "file_count": file_count,
        "content_hash": content_hash,
        "reason": reason.strip() or "Not provided",
    }


def _manifest_hash(manifest: dict[str, object]) -> str:
    canonical = json.dumps(
        manifest,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _verify_published_manifest(
    directory: fs_safe.PinnedDirectory,
    name: str,
    expected_text: str,
    expected_identity: fs_safe.FileIdentity,
) -> None:
    """Verify manifest identity and content through its pinned archive directory."""

    try:
        actual, identity = fs_safe.read_file(
            directory,
            name,
            expected_identity=expected_identity,
        )
    except fs_safe.FilesystemSafetyError as exc:
        raise ArchiveError("The archive manifest could not be verified after publication.") from exc
    if identity != expected_identity or actual != expected_text.encode("utf-8"):
        raise ArchiveError("The archive manifest changed after publication.")


def archive_project(
    root: Path,
    *,
    project_id: str,
    projects_dir: str | None = None,
    archive_dir: str | None = None,
    apply: bool = False,
    approval: str | None = None,
    reviewed_hash: str | None = None,
    reviewer: str = "",
    reason: str = "",
    archived_on: str | None = None,
) -> dict[str, object]:
    root = _lexical_root(root)
    if not PROJECT_ID_RE.fullmatch(project_id):
        raise ArchiveError(
            "Project ID must use letters, numbers, or internal hyphens and be between 3 and 64 characters."
        )
    config_text = _load_config_text(root)
    project_value = projects_dir or _config_value(
        config_text,
        "workspace",
        "project_root",
        "projects",
    )
    archive_value = archive_dir or _config_value(
        config_text,
        "workspace",
        "archive_root",
        "archive",
    )
    project_parts = _safe_directory_parts(project_value, "Project root")
    archive_parts = _safe_directory_parts(archive_value, "Archive root")
    project_root = _safe_directory(root, project_value, "Project root")
    archive_root = _safe_directory(root, archive_value, "Archive root")
    source = project_root / project_id
    destination = archive_root / project_id
    if not source.is_dir() or source.is_symlink():
        raise ArchiveError("The requested project does not exist as a regular directory.")
    if destination.exists() or destination.is_symlink():
        raise ArchiveError("The archive destination already exists; no overwrite is allowed.")
    reserved_manifest = source / "ARCHIVE_MANIFEST.json"
    if reserved_manifest.exists() or reserved_manifest.is_symlink():
        raise ArchiveError(
            "The project already contains the reserved ARCHIVE_MANIFEST.json path; no archive was attempted."
        )
    case_insensitive_paths = os.name == "nt" or sys.platform == "darwin"
    project_comparison = tuple(
        part.casefold() if case_insensitive_paths else part
        for part in project_parts
    )
    archive_comparison = tuple(
        part.casefold() if case_insensitive_paths else part
        for part in archive_parts
    )
    if (
        project_comparison == archive_comparison
        or project_comparison == archive_comparison[: len(project_comparison)]
        or archive_comparison == project_comparison[: len(archive_comparison)]
    ):
        raise ArchiveError("Project and archive roots must be separate, non-nested directories.")

    content_hash, file_count = _tree_hash(source)
    date_value = archived_on or date.today().isoformat()
    try:
        date.fromisoformat(date_value)
    except ValueError as exc:
        raise ArchiveError("Archive date must use YYYY-MM-DD.") from exc
    source_value = source.relative_to(root).as_posix()
    destination_value = destination.relative_to(root).as_posix()
    preview_manifest = _preview_manifest(
        project_id=project_id,
        source=source_value,
        destination=destination_value,
        file_count=file_count,
        content_hash=content_hash,
        archived_on=date_value,
        reason=reason,
    )
    preview_manifest_hash = _manifest_hash(preview_manifest)
    result: dict[str, object] = {
        "project_id": project_id,
        "source": source_value,
        "destination": destination_value,
        "file_count": file_count,
        "content_hash": content_hash,
        "archived_on": date_value,
        "reason_recorded": bool(reason.strip()),
        "preview_manifest": preview_manifest,
        "preview_manifest_hash": preview_manifest_hash,
    }
    if not apply:
        result["status"] = "preview"
        result["next_step"] = (
            f"After review, repeat with --apply --approve {APPROVAL_PHRASE} "
            f"--reviewed-hash {preview_manifest_hash} --reviewer <reviewer>."
        )
        return result
    if approval != APPROVAL_PHRASE:
        raise ArchiveError("Apply requires the exact approval phrase shown by the dry run.")
    reviewer_value = reviewer.strip()
    if not reviewer_value:
        raise ArchiveError("Apply requires an explicitly supplied reviewer.")
    if len(reviewer_value) > 160 or any(ord(character) < 32 for character in reviewer_value):
        raise ArchiveError("Reviewer must be printable text no longer than 160 characters.")
    if reviewed_hash != preview_manifest_hash:
        raise ArchiveError("The reviewed hash does not match the current preview manifest.")

    manifest = {
        "manifest_version": "1.0",
        "project_id": project_id,
        "archived_on": date_value,
        "source": result["source"],
        "destination": result["destination"],
        "file_count_before_manifest": file_count,
        "content_hash_before_manifest": content_hash,
        "reason": reason.strip() or "Not provided",
        "preview_manifest_hash": preview_manifest_hash,
        "reviewed_hash": reviewed_hash,
        "reviewer": reviewer_value,
        "human_approval": True,
        "restore_instruction": "Move this directory back only after checking that the original project path is absent.",
    }
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"

    try:
        with ExitStack() as stack:
            repository_pin = stack.enter_context(fs_safe.pin_root(root))
            project_pins = fs_safe.ensure_relative_directory(
                repository_pin,
                project_parts,
                create=False,
            )
            for pin in project_pins:
                stack.callback(pin.close)
            archive_pins = fs_safe.ensure_relative_directory(
                repository_pin,
                archive_parts,
                create=True,
            )
            for pin in archive_pins:
                stack.callback(pin.close)
            source_parent = project_pins[-1]
            destination_parent = archive_pins[-1]
            fs_safe.revalidate_directory(repository_pin)
            fs_safe.revalidate_directory(source_parent)
            fs_safe.revalidate_directory(destination_parent)

            if fs_safe.child_exists(destination_parent, project_id):
                raise ArchiveError(
                    "The archive destination already exists; no overwrite is allowed."
                )
            source_pin = fs_safe.open_child_directory(source_parent, project_id)
            stack.callback(source_pin.close)
            source_identity = source_pin.identity
            if fs_safe.child_exists(source_pin, "ARCHIVE_MANIFEST.json"):
                raise ArchiveError(
                    "The project contains the reserved manifest path; no archive was attempted."
                )
            current_hash, current_file_count = _tree_hash_pinned(source_pin)
            if current_hash != content_hash or current_file_count != file_count:
                raise ArchiveError(
                    "The project changed after preview verification; generate and review a new preview."
                )

            fs_safe.invoke_test_hook(
                "archive_parents_pinned",
                repository=repository_pin,
                source_parent=source_parent,
                destination_parent=destination_parent,
                source=source_pin,
                project_id=project_id,
            )
            published_manifest_identity: fs_safe.FileIdentity | None = None
            operation_complete = False
            try:
                fs_safe.atomic_rename_no_replace(
                    source_parent,
                    project_id,
                    destination_parent,
                    project_id,
                    expected_identity=source_identity,
                    directory=True,
                )
                if fs_safe.child_exists(source_parent, project_id):
                    raise fs_safe.IdentityChangedError(
                        "The expected source entry remained after the archive move."
                    )
                if (
                    fs_safe.child_identity(
                        destination_parent,
                        project_id,
                        directory=True,
                    )
                    != source_identity
                ):
                    raise fs_safe.IdentityChangedError(
                        "The archive destination did not contain the reviewed directory."
                    )
                fs_safe.revalidate_directory(repository_pin)
                fs_safe.revalidate_directory(source_parent)
                fs_safe.revalidate_directory(destination_parent)
                moved_hash, moved_file_count = _tree_hash_pinned(source_pin)
                if moved_hash != content_hash or moved_file_count != file_count:
                    raise ArchiveError("The moved project did not match the reviewed content.")

                fs_safe.invoke_test_hook(
                    "archive_before_manifest",
                    repository=repository_pin,
                    source_parent=source_parent,
                    destination_parent=destination_parent,
                    destination=source_pin,
                    project_id=project_id,
                )
                fs_safe.revalidate_directory(repository_pin)
                fs_safe.revalidate_directory(source_parent)
                fs_safe.revalidate_directory(destination_parent)
                if (
                    fs_safe.child_identity(
                        destination_parent,
                        project_id,
                        directory=True,
                    )
                    != source_identity
                ):
                    raise fs_safe.IdentityChangedError(
                        "Archive destination identity changed before manifest publication."
                    )
                published_manifest_identity = fs_safe.publish_text_exclusive(
                    source_pin,
                    "ARCHIVE_MANIFEST.json",
                    manifest_text,
                )
                _verify_published_manifest(
                    source_pin,
                    "ARCHIVE_MANIFEST.json",
                    manifest_text,
                    published_manifest_identity,
                )
                final_hash, final_file_count = _tree_hash_pinned(
                    source_pin,
                    excluded_relative_paths=frozenset({"ARCHIVE_MANIFEST.json"}),
                )
                if final_hash != content_hash or final_file_count != file_count:
                    raise ArchiveError("The archived project changed during manifest publication.")
                fs_safe.revalidate_directory(repository_pin)
                fs_safe.revalidate_directory(source_parent)
                fs_safe.revalidate_directory(destination_parent)
                if fs_safe.child_exists(source_parent, project_id) or (
                    fs_safe.child_identity(
                        destination_parent,
                        project_id,
                        directory=True,
                    )
                    != source_identity
                ):
                    raise fs_safe.IdentityChangedError(
                        "Archive path identity verification failed before success."
                    )
                fs_safe.invoke_test_hook(
                    "archive_before_success",
                    repository=repository_pin,
                    source_parent=source_parent,
                    destination_parent=destination_parent,
                    destination=source_pin,
                    project_id=project_id,
                )
                fs_safe.revalidate_directory(repository_pin)
                fs_safe.revalidate_directory(source_parent)
                fs_safe.revalidate_directory(destination_parent)
                _verify_published_manifest(
                    source_pin,
                    "ARCHIVE_MANIFEST.json",
                    manifest_text,
                    published_manifest_identity,
                )
                final_hash, final_file_count = _tree_hash_pinned(
                    source_pin,
                    excluded_relative_paths=frozenset({"ARCHIVE_MANIFEST.json"}),
                )
                if final_hash != content_hash or final_file_count != file_count:
                    raise ArchiveError("Final archived content verification failed.")
                if fs_safe.child_exists(source_parent, project_id) or (
                    fs_safe.child_identity(
                        destination_parent,
                        project_id,
                        directory=True,
                    )
                    != source_identity
                ):
                    raise fs_safe.IdentityChangedError(
                        "Archived project path changed during final verification."
                    )
                operation_complete = True
            except Exception as exc:
                if published_manifest_identity is not None or isinstance(
                    exc,
                    fs_safe.PublicationOutcomeError,
                ):
                    raise ArchiveError(
                        "Archive verification failed after manifest publication. No final pathname "
                        "was deleted or rolled back; inspect "
                        f"{destination_value}/ARCHIVE_MANIFEST.json manually."
                    ) from exc
                recovery_error: Exception | None = None
                try:
                    rollback_performed = False
                    if fs_safe.child_exists(source_pin, "ARCHIVE_MANIFEST.json"):
                        raise ArchiveError(
                            "A manifest exists after an incomplete publication. It was left "
                            f"untouched for manual inspection at {destination_value}/"
                            "ARCHIVE_MANIFEST.json."
                        )

                    source_present = fs_safe.child_exists(source_parent, project_id)
                    destination_present = fs_safe.child_exists(
                        destination_parent,
                        project_id,
                    )
                    if source_present:
                        if (
                            fs_safe.child_identity(
                                source_parent,
                                project_id,
                                directory=True,
                            )
                            != source_identity
                        ):
                            raise ArchiveError("The source path now names an unexpected object.")
                    elif destination_present and (
                        fs_safe.child_identity(
                            destination_parent,
                            project_id,
                            directory=True,
                        )
                        == source_identity
                    ):
                        rollback_hash, rollback_count = _tree_hash_pinned(source_pin)
                        if rollback_hash != content_hash or rollback_count != file_count:
                            raise ArchiveError(
                                "The moved directory no longer matches the reviewed content."
                            )
                        fs_safe.atomic_rename_no_replace(
                            destination_parent,
                            project_id,
                            source_parent,
                            project_id,
                            expected_identity=source_identity,
                            directory=True,
                        )
                        rollback_performed = True
                    else:
                        raise ArchiveError(
                            "Neither pinned parent contains the reviewed project unambiguously."
                        )

                    if (
                        not fs_safe.child_exists(source_parent, project_id)
                        or (
                            rollback_performed
                            and fs_safe.child_exists(destination_parent, project_id)
                        )
                        or fs_safe.child_identity(
                            source_parent,
                            project_id,
                            directory=True,
                        )
                        != source_identity
                    ):
                        raise ArchiveError("Automatic rollback could not be verified.")
                    restored_hash, restored_count = _tree_hash_pinned(source_pin)
                    if restored_hash != content_hash or restored_count != file_count:
                        raise ArchiveError("Restored project content did not match the reviewed content.")
                    fs_safe.revalidate_directory(repository_pin)
                    fs_safe.revalidate_directory(source_parent)
                    fs_safe.revalidate_directory(destination_parent)
                except Exception as rollback_exc:
                    recovery_error = rollback_exc

                if recovery_error is not None:
                    raise ArchiveError(
                        "Archive operation failed and safe recovery is ambiguous or incomplete. "
                        f"Inspect both {source_value} and {destination_value} manually; "
                        "no success is reported and no new manifest is asserted."
                    ) from recovery_error
                if isinstance(exc, ArchiveError):
                    raise
                if isinstance(exc, fs_safe.DestinationExistsError):
                    raise ArchiveError(
                        "The archive destination appeared during the no-replace move and was preserved."
                    ) from exc
                raise ArchiveError(
                    "Archive operation failed closed; the reviewed project was verified at the "
                    "pinned source parent and no manifest remains."
                ) from exc

            if not operation_complete:
                raise ArchiveError("Archive operation did not reach a verified final state.")
    except ArchiveError:
        raise
    except (fs_safe.FilesystemSafetyError, OSError) as exc:
        raise ArchiveError(f"Filesystem safety check blocked archive application: {exc}") from exc

    result["status"] = "archived"
    result["manifest"] = f"{destination_value}/ARCHIVE_MANIFEST.json"
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preview or apply an Osito project archive move.")
    parser.add_argument("--root", default=".", help="Osito repository root.")
    parser.add_argument(
        "--project-id",
        required=True,
        help="Project identifier using letters, numbers, and optional internal hyphens.",
    )
    parser.add_argument("--projects-dir", help="Override the configured project root.")
    parser.add_argument("--archive-dir", help="Override the configured archive root.")
    parser.add_argument("--reason", default="", help="Human-readable archive rationale.")
    parser.add_argument("--archived-on", help="Archive date in YYYY-MM-DD form.")
    parser.add_argument("--apply", action="store_true", help="Apply the reviewed move.")
    parser.add_argument("--approve", help="Exact approval phrase required with --apply.")
    parser.add_argument("--reviewed-hash", help="SHA-256 hash printed by the reviewed preview.")
    parser.add_argument("--reviewer", help="Name or identifier of the human reviewer.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = archive_project(
            Path(args.root),
            project_id=args.project_id,
            projects_dir=args.projects_dir,
            archive_dir=args.archive_dir,
            apply=args.apply,
            approval=args.approve,
            reviewed_hash=args.reviewed_hash,
            reviewer=args.reviewer or "",
            reason=args.reason,
            archived_on=args.archived_on,
        )
    except ArchiveError as exc:
        print(f"ARCHIVE BLOCKED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
