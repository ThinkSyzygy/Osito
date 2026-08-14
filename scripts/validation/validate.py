#!/usr/bin/env python3
"""Deterministic, standard-library structural validation for Osito."""

from __future__ import annotations

import argparse
import ast
import collections
import dataclasses
import os
import re
import stat as stat_module
import sys
from pathlib import Path, PurePosixPath
from typing import Iterable, Sequence
from urllib.parse import unquote


EXIT_PASS = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2
FILE_ATTRIBUTE_REPARSE_POINT = getattr(
    stat_module,
    "FILE_ATTRIBUTE_REPARSE_POINT",
    0x00000400,
)

REQUIRED_FILES = {
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "PUBLICATION_CHECKLIST.md",
    "README.md",
    "SECURITY.md",
    "config/metadata-schema.md",
    "config/osito.example.yaml",
    "docs/security-and-privacy.md",
    "docs/responsible-ai-use.md",
    "reports/sanitization-summary.md",
    "scripts/audit/audit.ps1",
    "scripts/audit/audit.sh",
    "scripts/audit/sanitize.py",
    "scripts/maintenance/archive_project.py",
    "scripts/setup/create_project.ps1",
    "scripts/setup/create_project.py",
    "scripts/setup/create_project.sh",
    "scripts/validation/validate.py",
}
REQUIRED_DIRECTORIES = {
    "config",
    "docs",
    "examples",
    "framework",
    "prompts",
    "reports",
    "scripts",
    "scripts/audit",
    "scripts/maintenance",
    "scripts/setup",
    "scripts/validation",
    "templates",
    "tests",
}
EXPECTED_TOP_LEVEL = {
    ".editorconfig",
    ".git",
    ".gitattributes",
    ".github",
    ".gitignore",
    "AGENTS.md",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "NOTICE",
    "PUBLICATION_CHECKLIST.md",
    "README.md",
    "SECURITY.md",
    "archive",
    "config",
    "docs",
    "examples",
    "framework",
    "projects",
    "prompts",
    "reports",
    "scripts",
    "templates",
    "tests",
}
REQUIRED_TEMPLATE_FIELDS = {
    "created",
    "id",
    "owner",
    "project_id",
    "related_ids",
    "source_links",
    "status",
    "type",
    "updated",
}
REQUIRED_EXAMPLE_AREAS = {
    "actions",
    "archive",
    "assumptions",
    "calculations",
    "changes",
    "decisions",
    "lessons",
    "meetings",
    "requirements",
    "research",
    "reviews",
    "risks",
    "validation",
}
TEXT_EXTENSIONS = {
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".sh",
    ".toml",
    ".tsv",
    ".txt",
    ".yaml",
    ".yml",
}
TEXT_FILENAMES = {".gitattributes", ".gitignore", "LICENSE", "NOTICE"}
BINARY_MAGIC = (
    b"%PDF-",
    b"\x7fELF",
    b"MZ",
    b"PK\x03\x04",
    b"Rar!\x1a\x07",
    b"7z\xbc\xaf\x27\x1c",
    b"\x89PNG\r\n\x1a\n",
    b"\xff\xd8\xff",
    b"GIF87a",
    b"GIF89a",
    b"SQLite format 3\x00",
    b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",
)

PLACEHOLDER_RE = re.compile(r"\{\{([a-z][a-z0-9_]*)\}\}")
YAML_KEY_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$")
MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)\n]+)\)")
FICTIONAL_LABEL_RE = re.compile(
    r'(?im)(?:'
    r'^\s*["\']?fictional["\']?\s*:\s*true\s*,?\s*$'
    r'|^\s*>\s*\*\*fictional example:\*\*(?:\s|$)'
    r'|^\s*#{1,6}\s+fictional example(?:\s+data only)?[.:]?\s*$'
    r')'
)


@dataclasses.dataclass(frozen=True, order=True)
class Issue:
    rule_id: str
    path: str
    line: int | None = None
    detail: str = ""


class ValidationConfigurationError(ValueError):
    """Raised when validation cannot start."""


class EntryIdentityError(OSError):
    """Raised when an entry changes identity or becomes link-like during reading."""


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _is_reparse_point(observation: os.stat_result) -> bool:
    return bool(
        int(getattr(observation, "st_file_attributes", 0))
        & FILE_ATTRIBUTE_REPARSE_POINT
    )


def _structural_entry_rule(path: Path, observation: os.stat_result) -> str | None:
    """Classify link-like entries without following them."""
    if stat_module.S_ISLNK(observation.st_mode):
        return "SYMLINK"
    junction_check = getattr(path, "is_junction", None)
    if callable(junction_check) and junction_check():
        return "JUNCTION"
    if _is_reparse_point(observation):
        return "REPARSE_POINT"
    return None


def _same_identity(left: os.stat_result, right: os.stat_result) -> bool:
    return (int(left.st_dev), int(left.st_ino)) == (
        int(right.st_dev),
        int(right.st_ino),
    )


def _iter_entries(
    root: Path,
    traversal_errors: list[Path] | None = None,
) -> Iterable[tuple[Path, os.stat_result | None, bool, str | None]]:
    errors = traversal_errors if traversal_errors is not None else []

    def record_walk_error(error: OSError) -> None:
        filename = getattr(error, "filename", None)
        errors.append(Path(filename) if filename else root)

    try:
        root_observation = root.lstat()
        root_rule = _structural_entry_rule(root, root_observation)
    except OSError:
        errors.append(root)
        return
    if root_rule is not None or not stat_module.S_ISDIR(root_observation.st_mode):
        return

    for parent_text, directory_names, file_names in os.walk(
        root,
        topdown=True,
        onerror=record_walk_error,
        followlinks=False,
    ):
        parent = Path(parent_text)
        directory_names.sort()
        file_names.sort()
        for name in list(directory_names):
            path = parent / name
            try:
                observation = path.lstat()
                structural_rule = _structural_entry_rule(path, observation)
            except OSError:
                yield path, None, True, "UNREADABLE_ENTRY"
                directory_names.remove(name)
                continue
            if (
                structural_rule is not None
                or not stat_module.S_ISDIR(observation.st_mode)
                or name == ".git"
            ):
                directory_names.remove(name)
            yield path, observation, True, structural_rule
        for name in file_names:
            path = parent / name
            try:
                observation = path.lstat()
                structural_rule = _structural_entry_rule(path, observation)
            except OSError:
                yield path, None, False, "UNREADABLE_ENTRY"
                continue
            yield path, observation, False, structural_rule


def _binary_sample(sample: bytes) -> bool:
    if b"\x00" in sample or any(sample.startswith(magic) for magic in BINARY_MAGIC):
        return True
    try:
        sample.decode("utf-8")
    except UnicodeDecodeError:
        return True
    return False


def _is_binary(path: Path) -> bool:
    try:
        with path.open("rb") as stream:
            sample = stream.read(8192)
    except OSError:
        return True
    return _binary_sample(sample)


def _read_verified_file(path: Path, expected: os.stat_result) -> bytes:
    """Read a regular file only while its opened and named identities agree."""
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        if (
            not stat_module.S_ISREG(opened.st_mode)
            or _is_reparse_point(opened)
            or not _same_identity(expected, opened)
        ):
            raise EntryIdentityError("entry identity changed before reading")
        content = stream.read()
    after = path.lstat()
    after_rule = _structural_entry_rule(path, after)
    if (
        after_rule is not None
        or not stat_module.S_ISREG(after.st_mode)
        or not _same_identity(expected, after)
    ):
        raise EntryIdentityError("entry identity changed during reading")
    return content


def validate_simple_yaml(text: str) -> list[str]:
    """Validate the intentionally small YAML subset used by Osito examples."""
    errors: list[str] = []
    containers: list[tuple[int, str]] = []
    keys_by_parent: dict[tuple[str, ...], set[str]] = collections.defaultdict(set)
    previous_container_indent: int | None = None

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if "\t" in raw_line:
            errors.append(f"line {line_number}: tabs are not allowed")
            continue
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if indent % 2:
            errors.append(f"line {line_number}: indentation must use multiples of two spaces")
        stripped = raw_line.strip()
        while containers and containers[-1][0] >= indent:
            containers.pop()
        if stripped.startswith("- "):
            if previous_container_indent is None or indent <= previous_container_indent:
                errors.append(f"line {line_number}: list item has no containing key")
            value = stripped[2:].strip()
            if not value:
                errors.append(f"line {line_number}: empty list item")
            continue

        match = YAML_KEY_RE.fullmatch(stripped)
        if not match:
            errors.append(f"line {line_number}: expected key: value")
            continue
        key, value = match.groups()
        parent = tuple(name for _, name in containers)
        if key in keys_by_parent[parent]:
            errors.append(f"line {line_number}: duplicate key")
        keys_by_parent[parent].add(key)
        value = value.strip()
        if value:
            previous_container_indent = containers[-1][0] if containers else None
            if value[0] in {'"', "'"} and (len(value) < 2 or value[-1] != value[0]):
                errors.append(f"line {line_number}: unterminated quoted scalar")
            pairs = {"[": "]", "{": "}"}
            if value[0] in pairs and value[-1:] != pairs[value[0]]:
                errors.append(f"line {line_number}: unterminated inline collection")
        else:
            containers.append((indent, key))
            previous_container_indent = indent
    return errors


def parse_frontmatter(text: str) -> tuple[dict[str, str] | None, str | None]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, None
    try:
        closing = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration:
        return None, "frontmatter has no closing delimiter"
    yaml_text = "\n".join(lines[1:closing])
    yaml_errors = validate_simple_yaml(yaml_text)
    if yaml_errors:
        return None, "; ".join(yaml_errors[:3])
    fields: dict[str, str] = {}
    for raw_line in yaml_text.splitlines():
        if len(raw_line) - len(raw_line.lstrip(" ")) != 0:
            continue
        match = YAML_KEY_RE.fullmatch(raw_line.strip())
        if match:
            fields[match.group(1)] = match.group(2).strip().strip("\"'")
    return fields, None


def _markdown_target(raw_target: str) -> str | None:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    elif " " in target:
        target = target.split(" ", 1)[0]
    target = unquote(target)
    if not target or target.startswith("#"):
        return None
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target):
        return None
    target = target.split("#", 1)[0].split("?", 1)[0]
    return target or None


def _local_target_status(path: Path, root: Path, target: str) -> str:
    candidate = root / target.lstrip("/") if target.startswith("/") else path.parent / target
    try:
        resolved = candidate.resolve(strict=False)
        resolved.relative_to(root.resolve())
    except ValueError:
        return "outside"
    except OSError:
        return "missing"
    return "ok" if candidate.exists() else "missing"


def broken_markdown_links(path: Path, root: Path, text: str) -> list[Issue]:
    issues: list[Issue] = []
    for match in MARKDOWN_LINK_RE.finditer(text):
        target = _markdown_target(match.group(1))
        if target is None:
            continue
        line = text.count("\n", 0, match.start()) + 1
        status = _local_target_status(path, root, target)
        if status == "outside":
            issues.append(Issue("OUTSIDE_REPOSITORY_LINK", _relative(path, root), line))
        elif status == "missing":
            issues.append(Issue("BROKEN_RELATIVE_LINK", _relative(path, root), line))
    return issues


def frontmatter_source_link_issues(
    path: Path,
    root: Path,
    text: str,
    fields: dict[str, str],
) -> list[Issue]:
    raw_value = fields.get("source_links")
    if raw_value is None:
        return []
    line = next(
        (
            line_number
            for line_number, raw_line in enumerate(text.splitlines(), start=1)
            if raw_line.startswith("source_links:")
        ),
        None,
    )
    try:
        values = ast.literal_eval(raw_value)
    except (SyntaxError, ValueError):
        return [Issue("INVALID_SOURCE_LINKS", _relative(path, root), line)]
    if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
        return [Issue("INVALID_SOURCE_LINKS", _relative(path, root), line)]

    issues: list[Issue] = []
    for raw_target in values:
        if "{{" in raw_target or "}}" in raw_target:
            continue
        target = _markdown_target(raw_target)
        if target is None:
            continue
        path_like = (
            target.startswith((".", "/"))
            or "/" in target
            or "\\" in target
            or bool(PurePosixPath(target).suffix)
        )
        if not path_like:
            # Stable source-record identifiers are valid provenance values but
            # are not filesystem paths that this validator can resolve.
            continue
        status = _local_target_status(path, root, target)
        if status == "outside":
            issues.append(Issue("OUTSIDE_REPOSITORY_SOURCE_LINK", _relative(path, root), line))
        elif status == "missing":
            issues.append(Issue("BROKEN_SOURCE_LINK", _relative(path, root), line))
    return issues


def _contains_files(path: Path) -> bool:
    return any(
        observation is not None
        and not is_directory
        and structural_rule is None
        and stat_module.S_ISREG(observation.st_mode)
        for _, observation, is_directory, structural_rule in _iter_entries(path)
    )


def _empty_public_directories(base: Path) -> list[Path]:
    """Return ordinary directories containing no ordinary file descendants."""
    try:
        base_observation = base.lstat()
        base_rule = _structural_entry_rule(base, base_observation)
    except OSError:
        return []
    if base_rule is not None or not stat_module.S_ISDIR(base_observation.st_mode):
        return []

    contains_file: dict[Path, bool] = {base: False}
    for path, observation, is_directory, structural_rule in _iter_entries(base):
        if observation is None or structural_rule is not None:
            continue
        if is_directory:
            if stat_module.S_ISDIR(observation.st_mode):
                contains_file.setdefault(path, False)
            continue
        if not stat_module.S_ISREG(observation.st_mode):
            continue
        current = path.parent
        while current == base or base in current.parents:
            contains_file[current] = True
            if current == base:
                break
            current = current.parent
    return [path for path, has_file in contains_file.items() if path != base and not has_file]


def validate_repository(root: Path) -> list[Issue]:
    lexical_root = Path(os.path.abspath(os.fspath(root)))
    try:
        root_observation = lexical_root.lstat()
        root_rule = _structural_entry_rule(lexical_root, root_observation)
    except OSError as exc:
        raise ValidationConfigurationError(
            "Validation root could not be inspected safely."
        ) from exc
    if root_rule is not None or not stat_module.S_ISDIR(root_observation.st_mode):
        raise ValidationConfigurationError(
            "Validation root must be an ordinary directory, not a link or reparse point."
        )
    root = lexical_root.resolve()
    try:
        resolved_root_observation = root.lstat()
        resolved_root_rule = _structural_entry_rule(root, resolved_root_observation)
    except OSError as exc:
        raise ValidationConfigurationError(
            "Resolved validation root could not be inspected."
        ) from exc
    if (
        resolved_root_rule is not None
        or not stat_module.S_ISDIR(resolved_root_observation.st_mode)
        or not _same_identity(root_observation, resolved_root_observation)
    ):
        raise ValidationConfigurationError(
            "Validation root changed identity while validation started."
        )
    if not root.is_dir():
        raise ValidationConfigurationError("Validation root must be an existing directory.")
    issues: list[Issue] = []

    for relative in sorted(REQUIRED_FILES):
        if not (root / relative).is_file():
            issues.append(Issue("MISSING_REQUIRED_FILE", relative))
    for relative in sorted(REQUIRED_DIRECTORIES):
        if not (root / relative).is_dir():
            issues.append(Issue("MISSING_REQUIRED_DIRECTORY", relative))
    for child in sorted(root.iterdir(), key=lambda item: item.name.casefold()):
        if child.name not in EXPECTED_TOP_LEVEL:
            issues.append(Issue("UNEXPECTED_TOP_LEVEL", child.name))

    for family in ("framework", "prompts", "templates"):
        base = root / family
        if not base.is_dir():
            continue
        for directory in sorted(
            _empty_public_directories(base),
            key=lambda item: item.as_posix(),
        ):
            issues.append(Issue("EMPTY_PUBLIC_AREA", _relative(directory, root)))

    identifiers: dict[str, list[str]] = collections.defaultdict(list)
    verified_text_files: dict[str, str] = {}
    example_root = root / "examples" / "fictional-project"
    if not (example_root / "README.md").is_file():
        issues.append(Issue("MISSING_FICTIONAL_EXAMPLE_OVERVIEW", "examples/fictional-project/README.md"))
    if not (example_root / "project.yaml").is_file():
        issues.append(Issue("MISSING_FICTIONAL_EXAMPLE_METADATA", "examples/fictional-project/project.yaml"))
    for area in sorted(REQUIRED_EXAMPLE_AREAS):
        directory = example_root / area
        if not directory.is_dir() or not _contains_files(directory):
            issues.append(Issue("INCOMPLETE_FICTIONAL_EXAMPLE", f"examples/fictional-project/{area}"))

    traversal_errors: list[Path] = []
    for path, observation, is_directory, structural_rule in _iter_entries(
        root,
        traversal_errors,
    ):
        relative = _relative(path, root)
        if observation is None:
            issues.append(Issue(structural_rule or "UNREADABLE_ENTRY", relative))
            continue
        if structural_rule is not None:
            issues.append(Issue(structural_rule, relative))
            continue
        if is_directory:
            if path.name == ".git" and path.parent != root:
                issues.append(Issue("NESTED_GIT_REPOSITORY", relative))
            continue
        if path.name == ".gitmodules":
            issues.append(Issue("GIT_SUBMODULE_CONFIG", relative))
        if not stat_module.S_ISREG(observation.st_mode):
            issues.append(Issue("UNSUPPORTED_ENTRY", relative))
            continue
        if path.suffix.casefold() not in TEXT_EXTENSIONS and path.name not in TEXT_FILENAMES:
            issues.append(Issue("UNEXPECTED_FILE_TYPE", relative))
        try:
            raw_content = _read_verified_file(path, observation)
        except EntryIdentityError:
            issues.append(Issue("IDENTITY_CHANGED", relative))
            continue
        except OSError:
            issues.append(Issue("UNREADABLE_TEXT", relative))
            continue
        if _binary_sample(raw_content[:8192]):
            issues.append(Issue("BINARY_FILE", relative))
            continue
        try:
            text = raw_content.decode("utf-8")
        except UnicodeError:
            issues.append(Issue("UNREADABLE_TEXT", relative))
            continue
        if relative in {
            "scripts/audit/sanitize.py",
            "scripts/audit/audit.sh",
            "scripts/audit/audit.ps1",
        }:
            verified_text_files[relative] = text
        if path.suffix.casefold() in {".yaml", ".yml"}:
            for detail in validate_simple_yaml(text)[:5]:
                issues.append(Issue("INVALID_SIMPLE_YAML", relative, detail=detail))
        if path.suffix.casefold() != ".md":
            if path.is_relative_to(example_root) and not FICTIONAL_LABEL_RE.search(text):
                issues.append(Issue("MISSING_FICTIONAL_LABEL", relative))
            continue

        fields, frontmatter_error = parse_frontmatter(text)
        if frontmatter_error:
            issues.append(Issue("INVALID_FRONTMATTER", relative, detail=frontmatter_error))
        is_template = path.is_relative_to(root / "templates") and path.name.casefold() != "readme.md"
        if fields is not None and not is_template:
            issues.extend(frontmatter_source_link_issues(path, root, text, fields))
        if is_template:
            if not text.strip():
                issues.append(Issue("EMPTY_TEMPLATE", relative))
            if fields is None:
                issues.append(Issue("MISSING_TEMPLATE_FRONTMATTER", relative))
            else:
                for field in sorted(REQUIRED_TEMPLATE_FIELDS.difference(fields)):
                    issues.append(Issue("MISSING_TEMPLATE_FIELD", relative, detail=field))
            placeholders = PLACEHOLDER_RE.findall(text)
            if not placeholders:
                issues.append(Issue("MISSING_TEMPLATE_PLACEHOLDER", relative))
            remainder = PLACEHOLDER_RE.sub("", text)
            if "{{" in remainder or "}}" in remainder:
                issues.append(Issue("INVALID_TEMPLATE_PLACEHOLDER", relative))
        if fields and fields.get("id") and "{{" not in fields["id"]:
            identifiers[fields["id"]].append(relative)
        if path.is_relative_to(example_root) and not FICTIONAL_LABEL_RE.search(text):
            issues.append(Issue("MISSING_FICTIONAL_LABEL", relative))
        issues.extend(broken_markdown_links(path, root, text))

    for path in traversal_errors:
        candidate = path if path.is_absolute() else root / path
        try:
            relative = _relative(candidate, root)
        except ValueError:
            relative = "<outside-root>"
        issues.append(Issue("UNREADABLE_ENTRY", relative))

    for identifier, paths in sorted(identifiers.items()):
        if len(paths) > 1:
            for path in paths:
                issues.append(Issue("DUPLICATE_IDENTIFIER", path, detail="identifier repeated"))

    audit_relative = "scripts/audit/sanitize.py"
    audit_text = verified_text_files.get(audit_relative)
    if audit_text is None or "--denylist" not in audit_text:
        issues.append(Issue("MISSING_DENYLIST_INTERFACE", audit_relative))
    wrapper_relatives = {
        "scripts/audit/audit.sh",
        "scripts/audit/audit.ps1",
    }
    if not wrapper_relatives.issubset(verified_text_files):
        issues.append(Issue("MISSING_AUDIT_WRAPPER", "scripts/audit"))
    try:
        final_root_observation = lexical_root.lstat()
        final_root_rule = _structural_entry_rule(lexical_root, final_root_observation)
    except OSError as exc:
        raise ValidationConfigurationError(
            "Validation root changed during traversal."
        ) from exc
    if (
        final_root_rule is not None
        or not stat_module.S_ISDIR(final_root_observation.st_mode)
        or not _same_identity(root_observation, final_root_observation)
    ):
        raise ValidationConfigurationError(
            "Validation root changed identity during traversal."
        )
    return sorted(
        set(issues),
        key=lambda item: (item.rule_id, item.path, item.line or 0, item.detail),
    )


def format_issues(issues: Sequence[Issue]) -> str:
    if not issues:
        return "PASS: repository structure and public examples passed deterministic validation."
    lines = [f"FAILED: {len(issues)} validation issue(s)."]
    for issue in issues:
        location = issue.path + (f":{issue.line}" if issue.line is not None else "")
        detail = f" ({issue.detail})" if issue.detail else ""
        lines.append(f"- {issue.rule_id}: {location}{detail}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate the Osito repository structure.")
    parser.add_argument("--root", default=".", help="Osito repository root.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        issues = validate_repository(Path(args.root))
    except ValidationConfigurationError as exc:
        print(f"CONFIGURATION ERROR: {exc}", file=sys.stderr)
        return EXIT_USAGE
    print(format_issues(issues))
    return EXIT_FINDINGS if issues else EXIT_PASS


if __name__ == "__main__":
    raise SystemExit(main())
