#!/usr/bin/env python3
"""Create a new Osito project from the public project templates."""

from __future__ import annotations

import argparse
from contextlib import ExitStack
import datetime as dt
import json
import os
import re
import secrets
import sys
from pathlib import Path, PurePosixPath
from typing import Sequence


REPOSITORY_CODE_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_CODE_ROOT))

from scripts.common import filesystem_safety as fs_safe


PROJECT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{1,62}[A-Za-z0-9]$")
PLACEHOLDER_RE = re.compile(r"\{\{([a-z][a-z0-9_]*)\}\}")
CONFIG_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")
MAX_CONFIG_BYTES = 256 * 1024
MAX_TEMPLATE_BYTES = 1024 * 1024
PROJECT_DIRECTORIES = (
    "actions",
    "assumptions",
    "calculations",
    "changes",
    "decisions",
    "evidence",
    "generated",
    "lessons",
    "meetings",
    "requirements",
    "research",
    "reviews",
    "risks",
    "validation",
)


class ProjectSetupError(RuntimeError):
    """Raised when a project cannot be created safely."""


class ProjectExistsError(ProjectSetupError):
    """Raised when the requested project directory already exists."""


def _minimal_yaml_scalar(raw_value: str) -> str:
    value = raw_value.strip()
    double_quoted = re.fullmatch(r'"([^"\\]*)"\s*(?:#.*)?', value)
    single_quoted = re.fullmatch(r"'([^']*)'\s*(?:#.*)?", value)
    if double_quoted or single_quoted:
        parsed = (double_quoted or single_quoted).group(1)
    else:
        value = re.split(r"\s+#", value, maxsplit=1)[0].rstrip()
        if not value or value[0] in "[{&*!|>@`" or any(character in value for character in "[]{}"):
            raise ProjectSetupError("Configured workspace paths must use a simple YAML scalar.")
        parsed = value
    if not parsed or any(ord(character) < 32 for character in parsed):
        raise ProjectSetupError("Configured workspace paths must use a nonempty printable scalar.")
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
            raise ProjectSetupError("The minimal configuration reader does not accept tab indentation.")
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
                raise ProjectSetupError("The selected configuration contains an invalid workspace key.")
            if candidate_key == key:
                if found is not None:
                    raise ProjectSetupError("The selected configuration repeats a required workspace key.")
                found = _minimal_yaml_scalar(value)
    return found or default


def _safe_repository_parts(relative_value: str) -> tuple[str, ...]:
    normalized = relative_value.replace("\\", "/")
    candidate = PurePosixPath(normalized)
    if (
        candidate.is_absolute()
        or re.match(r"^[A-Za-z]:", normalized)
        or normalized.startswith("//")
        or ".." in candidate.parts
        or not candidate.parts
    ):
        raise ProjectSetupError("Configured project storage must be a safe repository-relative directory.")
    return tuple(candidate.parts)


def _safe_repository_directory(root: Path, relative_value: str) -> Path:
    parts = _safe_repository_parts(relative_value)
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
            raise ProjectSetupError("Configured project storage could not be inspected safely.") from exc
        if (
            current.is_symlink()
            or bool(checker and checker())
            or bool(
                getattr(observation, "st_file_attributes", 0)
                & fs_safe.FILE_ATTRIBUTE_REPARSE_POINT
            )
        ):
            raise ProjectSetupError(
                "Configured project storage must not traverse a link, junction, or reparse point."
            )
    return path


def _lexical_root(root: Path) -> Path:
    lexical = Path(os.path.abspath(os.fspath(root)))
    try:
        observation = lexical.stat(follow_symlinks=False)
    except OSError as exc:
        raise ProjectSetupError("Repository root does not exist or cannot be inspected.") from exc
    if not lexical.is_dir() or lexical.is_symlink():
        raise ProjectSetupError("Repository root must be an ordinary directory.")
    if getattr(observation, "st_file_attributes", 0) & fs_safe.FILE_ATTRIBUTE_REPARSE_POINT:
        raise ProjectSetupError("Repository root must not be a junction or reparse point.")
    return lexical


def _read_input_text(
    parent: fs_safe.PinnedDirectory,
    name: str,
    *,
    max_bytes: int,
    label: str,
) -> str:
    """Read one expected repository input without a pathname check/reopen gap."""

    try:
        metadata = fs_safe.inspect_child(parent, name)
        if metadata.kind != "file" or metadata.link_count != 1:
            raise fs_safe.FilesystemSafetyError("Expected a single-link regular file.")
        text, _identity = fs_safe.read_utf8_file(
            parent,
            name,
            max_bytes=max_bytes,
            expected_identity=metadata.identity,
        )
        return text
    except fs_safe.FilesystemSafetyError as exc:
        raise ProjectSetupError(f"{label} could not be read safely: {name}") from exc


def _load_creation_inputs(
    root: Path,
    *,
    projects_dir: str | None,
    values: dict[str, str],
) -> tuple[str, dict[str, bytes], tuple[str, ...]]:
    """Load configuration and templates through pinned repository directories."""

    try:
        with ExitStack() as stack:
            repository = stack.enter_context(fs_safe.pin_root(root))

            config_text: str | None = None
            if fs_safe.child_exists(repository, "config"):
                config_directory = fs_safe.open_child_directory(repository, "config")
                stack.callback(config_directory.close)
                if fs_safe.child_exists(config_directory, "osito.local.yaml"):
                    config_name = "osito.local.yaml"
                elif fs_safe.child_exists(config_directory, "osito.example.yaml"):
                    config_name = "osito.example.yaml"
                else:
                    config_name = None
                if config_name is not None:
                    config_text = _read_input_text(
                        config_directory,
                        config_name,
                        max_bytes=MAX_CONFIG_BYTES,
                        label="The selected configuration",
                    )
                fs_safe.revalidate_directory(config_directory)

            configured = projects_dir or _config_value(
                config_text,
                "workspace",
                "project_root",
                "projects",
            )

            templates_directory = fs_safe.open_child_directory(repository, "templates")
            stack.callback(templates_directory.close)
            project_templates = fs_safe.open_child_directory(
                templates_directory,
                "project",
            )
            stack.callback(project_templates.close)
            template_names = ("project-charter.md", "project-index.md")
            expected_files: dict[str, bytes] = {}
            for template_name in template_names:
                template_text = _read_input_text(
                    project_templates,
                    template_name,
                    max_bytes=MAX_TEMPLATE_BYTES,
                    label="Required project template",
                )
                expected_files[template_name] = _render_template(
                    template_text,
                    values,
                ).encode("utf-8")

            fs_safe.revalidate_directory(project_templates)
            fs_safe.revalidate_directory(templates_directory)
            fs_safe.revalidate_directory(repository)
            return configured, expected_files, template_names
    except ProjectSetupError:
        raise
    except fs_safe.FilesystemSafetyError as exc:
        raise ProjectSetupError(
            "Project configuration or templates could not be opened safely."
        ) from exc


def _render_template(text: str, values: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        return values.get(match.group(1), "TBD")

    return PLACEHOLDER_RE.sub(replace, text)


def _project_yaml(
    project_id: str,
    name: str,
    owner: str,
    created: str,
    classification: str,
    fictional: bool,
) -> str:
    def scalar(value: str) -> str:
        return json.dumps(value, ensure_ascii=False)

    return "\n".join(
        (
            'schema_version: "1.0"',
            f"project_id: {scalar(project_id)}",
            f"name: {scalar(name)}",
            'status: "active"',
            f"owner: {scalar(owner)}",
            f"created: {scalar(created)}",
            f"classification: {scalar(classification)}",
            f"fictional: {'true' if fictional else 'false'}",
            "human_approval_required: true",
            "",
        )
    )


def _cleanup_prepared_project(
    parent: fs_safe.PinnedDirectory,
    temporary: fs_safe.PinnedDirectory,
    temporary_name: str,
    expected_files: dict[str, bytes],
    file_identities: dict[str, fs_safe.FileIdentity],
    directory_identities: dict[str, fs_safe.FileIdentity],
) -> None:
    """Remove only entries created and identity-tracked by this invocation."""

    try:
        _verify_generated_project(
            temporary,
            expected_files,
            file_identities,
            directory_identities,
        )
    except fs_safe.FilesystemSafetyError as exc:
        raise ProjectSetupError(
            f"Temporary project cleanup is ambiguous; leave {temporary_name} for manual inspection."
        ) from exc

    failures: list[str] = []
    for filename, identity in file_identities.items():
        try:
            if fs_safe.child_exists(temporary, filename):
                fs_safe.remove_file(
                    temporary,
                    filename,
                    expected_identity=identity,
                    expected_content=expected_files[filename],
                )
        except fs_safe.FilesystemSafetyError as exc:
            failures.append(f"{filename}: {exc}")
    for dirname, identity in reversed(tuple(directory_identities.items())):
        try:
            if fs_safe.child_exists(temporary, dirname):
                fs_safe.remove_empty_directory(temporary, dirname, expected_identity=identity)
        except fs_safe.FilesystemSafetyError as exc:
            failures.append(f"{dirname}: {exc}")
    try:
        if fs_safe.child_exists(parent, temporary_name):
            fs_safe.remove_empty_directory(
                parent,
                temporary_name,
                expected_identity=temporary.identity,
            )
    except fs_safe.FilesystemSafetyError as exc:
        failures.append(f"{temporary_name}: {exc}")
    if failures:
        raise ProjectSetupError(
            "Project publication failed and verified temporary cleanup was incomplete. "
            "Inspect the configured project parent manually. Cleanup details: "
            + "; ".join(failures)
        )


def _verify_generated_project(
    project: fs_safe.PinnedDirectory,
    expected_files: dict[str, bytes],
    file_identities: dict[str, fs_safe.FileIdentity],
    directory_identities: dict[str, fs_safe.FileIdentity],
) -> None:
    expected_names = set(expected_files) | set(directory_identities)
    actual_names = set(fs_safe.list_child_names(project))
    if actual_names != expected_names:
        raise fs_safe.IdentityChangedError(
            "Generated project contains missing or unexpected root entries."
        )
    for dirname, expected_identity in directory_identities.items():
        child = fs_safe.open_child_directory(project, dirname)
        try:
            if child.identity != expected_identity:
                raise fs_safe.IdentityChangedError(
                    f"Generated project directory changed identity: {dirname}"
                )
            if fs_safe.list_child_names(child):
                raise fs_safe.IdentityChangedError(
                    f"Generated project directory is not empty: {dirname}"
                )
        finally:
            child.close()
    for filename, expected_bytes in expected_files.items():
        expected_identity = file_identities.get(filename)
        if expected_identity is None:
            raise fs_safe.IdentityChangedError(
                f"Generated project file identity was not recorded: {filename}"
            )
        actual, opened_identity = fs_safe.read_file(
            project,
            filename,
            expected_identity=expected_identity,
        )
        if actual != expected_bytes or opened_identity != expected_identity:
            raise fs_safe.IdentityChangedError(
                f"Generated project file changed content or identity: {filename}"
            )


def create_project(
    root: Path,
    *,
    project_id: str,
    name: str,
    owner: str = "Unassigned",
    created: str | None = None,
    classification: str = "internal",
    projects_dir: str | None = None,
    fictional: bool = False,
    dry_run: bool = False,
) -> dict[str, object]:
    root = _lexical_root(root)
    if not PROJECT_ID_RE.fullmatch(project_id):
        raise ProjectSetupError(
            "Project ID must use letters, numbers, or internal hyphens and be between 3 and 64 characters."
        )
    if not name.strip():
        raise ProjectSetupError("Project name must not be empty.")
    if classification not in {"public", "internal", "confidential", "restricted"}:
        raise ProjectSetupError("Classification must be public, internal, confidential, or restricted.")
    created_value = created or dt.date.today().isoformat()
    try:
        dt.date.fromisoformat(created_value)
    except ValueError as exc:
        raise ProjectSetupError("Created date must use YYYY-MM-DD.") from exc

    values = {
        "project_id": project_id,
        "project_title": name.strip(),
        "owner": owner.strip() or "Unassigned",
        "date": created_value,
    }
    configured, expected_files, template_names = _load_creation_inputs(
        root,
        projects_dir=projects_dir,
        values=values,
    )
    project_parts = _safe_repository_parts(configured)
    project_parent = _safe_repository_directory(root, configured)
    destination = project_parent / project_id
    if destination.exists() or destination.is_symlink():
        raise ProjectExistsError("The requested project already exists; no files were changed.")

    expected_files["project.yaml"] = _project_yaml(
        project_id,
        name.strip(),
        owner.strip() or "Unassigned",
        created_value,
        classification,
        fictional,
    ).encode("utf-8")

    relative_destination = destination.relative_to(root).as_posix()
    plan = {
        "project_id": project_id,
        "destination": relative_destination,
        "fictional": fictional,
        "directories": list(PROJECT_DIRECTORIES),
        "files": ["project.yaml", *sorted(template_names)],
    }
    if dry_run:
        plan["status"] = "dry_run"
        return plan

    try:
        with ExitStack() as stack:
            repository_pin = stack.enter_context(fs_safe.pin_root(root))
            project_pins = fs_safe.ensure_relative_directory(
                repository_pin,
                project_parts,
                create=True,
            )
            for pin in project_pins:
                stack.callback(pin.close)
            project_parent_pin = project_pins[-1]
            fs_safe.revalidate_directory(repository_pin)
            fs_safe.revalidate_directory(project_parent_pin)
            if fs_safe.child_exists(project_parent_pin, project_id):
                raise ProjectExistsError(
                    "The requested project already exists; no files were changed."
                )

            temporary_name = f".osito-create-{secrets.token_hex(12)}"
            temporary_pin = fs_safe.open_child_directory(
                project_parent_pin,
                temporary_name,
                create=True,
            )
            stack.callback(temporary_pin.close)
            file_identities: dict[str, fs_safe.FileIdentity] = {}
            directory_identities: dict[str, fs_safe.FileIdentity] = {}
            publication_complete = False

            try:
                for directory in PROJECT_DIRECTORIES:
                    child = fs_safe.open_child_directory(
                        temporary_pin,
                        directory,
                        create=True,
                    )
                    directory_identities[directory] = child.identity
                    child.close()
                for filename, content in expected_files.items():
                    file_identities[filename] = fs_safe.write_file_exclusive(
                        temporary_pin,
                        filename,
                        content,
                    )
                _verify_generated_project(
                    temporary_pin,
                    expected_files,
                    file_identities,
                    directory_identities,
                )
                fs_safe.invoke_test_hook(
                    "create_temp_built",
                    repository=repository_pin,
                    project_parent=project_parent_pin,
                    temporary=temporary_pin,
                    project_id=project_id,
                )
                fs_safe.atomic_rename_no_replace(
                    project_parent_pin,
                    temporary_name,
                    project_parent_pin,
                    project_id,
                    expected_identity=temporary_pin.identity,
                    directory=True,
                )
                publication_complete = True
                if fs_safe.child_exists(project_parent_pin, temporary_name):
                    raise fs_safe.IdentityChangedError(
                        "Temporary project name remained after publication."
                    )
                if (
                    fs_safe.child_identity(
                        project_parent_pin,
                        project_id,
                        directory=True,
                    )
                    != temporary_pin.identity
                ):
                    raise fs_safe.IdentityChangedError(
                        "Published project identity did not match the prepared project."
                    )
                _verify_generated_project(
                    temporary_pin,
                    expected_files,
                    file_identities,
                    directory_identities,
                )
                fs_safe.revalidate_directory(repository_pin)
                fs_safe.revalidate_directory(project_parent_pin)
                fs_safe.invoke_test_hook(
                    "create_before_success",
                    repository=repository_pin,
                    project_parent=project_parent_pin,
                    project=temporary_pin,
                    project_id=project_id,
                )
                fs_safe.revalidate_directory(repository_pin)
                fs_safe.revalidate_directory(project_parent_pin)
                _verify_generated_project(
                    temporary_pin,
                    expected_files,
                    file_identities,
                    directory_identities,
                )
                if fs_safe.child_exists(project_parent_pin, temporary_name) or (
                    fs_safe.child_identity(
                        project_parent_pin,
                        project_id,
                        directory=True,
                    )
                    != temporary_pin.identity
                ):
                    raise fs_safe.IdentityChangedError(
                        "Published project path changed during final verification."
                    )
            except Exception as exc:
                cleanup_error: Exception | None = None
                try:
                    temporary_present = fs_safe.child_exists(
                        project_parent_pin,
                        temporary_name,
                    )
                    destination_present = fs_safe.child_exists(
                        project_parent_pin,
                        project_id,
                    )
                    if temporary_present:
                        if (
                            fs_safe.child_identity(
                                project_parent_pin,
                                temporary_name,
                                directory=True,
                            )
                            != temporary_pin.identity
                        ):
                            raise ProjectSetupError(
                                "Temporary project identity is ambiguous; inspect the configured "
                                "project parent manually."
                            )
                    else:
                        inspection_path = (
                            relative_destination
                            if destination_present
                            else f"{project_parent.relative_to(root).as_posix()}/{temporary_name}"
                        )
                        raise ProjectSetupError(
                            "Project publication outcome is ambiguous; no final pathname was "
                            f"reclaimed. Inspect {inspection_path} manually."
                        )
                    _cleanup_prepared_project(
                        project_parent_pin,
                        temporary_pin,
                        temporary_name,
                        expected_files,
                        file_identities,
                        directory_identities,
                    )
                except Exception as recovery_exc:
                    cleanup_error = recovery_exc
                if cleanup_error is not None:
                    raise ProjectSetupError(
                        "Project publication failed and safe recovery could not be proven. "
                        f"Inspect {project_parent.relative_to(root).as_posix()} manually."
                    ) from cleanup_error
                if isinstance(exc, ProjectExistsError):
                    raise
                if isinstance(exc, fs_safe.DestinationExistsError):
                    raise ProjectExistsError(
                        "The requested project appeared during publication and was preserved."
                    ) from exc
                if isinstance(exc, ProjectSetupError):
                    raise
                raise ProjectSetupError(
                    "Project publication failed closed; verified temporary content was cleaned."
                ) from exc

            if not publication_complete:
                raise ProjectSetupError("Project publication did not reach a verified final state.")
    except ProjectSetupError:
        raise
    except (fs_safe.FilesystemSafetyError, OSError) as exc:
        raise ProjectSetupError(f"Filesystem safety check blocked project creation: {exc}") from exc

    plan["status"] = "created"
    return plan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a new project from Osito templates.")
    parser.add_argument("--root", default=".", help="Osito repository root.")
    parser.add_argument(
        "--project-id",
        required=True,
        help="Project identifier using letters, numbers, and optional internal hyphens.",
    )
    parser.add_argument("--name", required=True, help="Human-readable project name.")
    parser.add_argument("--owner", default="Unassigned", help="Initial accountable owner.")
    parser.add_argument("--created", help="Creation date in YYYY-MM-DD form.")
    parser.add_argument(
        "--classification",
        default="internal",
        choices=["public", "internal", "confidential", "restricted"],
    )
    parser.add_argument("--projects-dir", help="Override the configured repository-relative project root.")
    parser.add_argument(
        "--fictional",
        action="store_true",
        help="Label the created project as fictional example data.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print the plan without creating files.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = create_project(
            Path(args.root),
            project_id=args.project_id,
            name=args.name,
            owner=args.owner,
            created=args.created,
            classification=args.classification,
            projects_dir=args.projects_dir,
            fictional=args.fictional,
            dry_run=args.dry_run,
        )
    except ProjectExistsError as exc:
        print(f"CONFLICT: {exc}", file=sys.stderr)
        return 1
    except ProjectSetupError as exc:
        print(f"CONFIGURATION ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
