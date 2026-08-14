#!/usr/bin/env python3
"""Local, dependency-free privacy and repository audit for Osito.

The scanner reports rule identifiers and locations, never matched values. It is
deliberately conservative: a clean result is a review aid, not a confidentiality
guarantee.
"""

from __future__ import annotations

import argparse
import collections
import dataclasses
import ipaddress
import json
import math
import os
import re
import stat as stat_module
import sys
from pathlib import Path, PurePosixPath
from typing import Iterable, Sequence
from urllib.parse import urlsplit


EXIT_PASS = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2

DEFAULT_MAX_FILE_BYTES = 1_000_000
MAX_TEXT_SCAN_BYTES = 2_000_000
PATTERN_DEFINITION_MARKER = "osito-audit: allow-pattern-definition"
DETECTOR_SOURCE = "scripts/audit/sanitize.py"
FILE_ATTRIBUTE_REPARSE_POINT = getattr(
    stat_module,
    "FILE_ATTRIBUTE_REPARSE_POINT",
    0x00000400,
)

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
TEXT_FILENAMES = {
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "NOTICE",
    "README.md",
    "SECURITY.md",
}
ARCHIVE_EXTENSIONS = {
    ".7z",
    ".bz2",
    ".gz",
    ".rar",
    ".tar",
    ".tgz",
    ".xz",
    ".zip",
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
ALLOWED_HIDDEN_PARTS = {
    ".editorconfig",
    ".git",
    ".gitattributes",
    ".github",
    ".gitignore",
}

# Pattern-definition lines in this file carry a narrowly scoped marker so the
# detector does not report its own example syntax. The marker is ignored in all
# other files and never suppresses external-denylist matching.
EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@([A-Z0-9.-]+\.[A-Z]{2,})\b")  # osito-audit: allow-pattern-definition
PHONE_RE = re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]\d{3}[\s.-]\d{4}(?!\d)")  # osito-audit: allow-pattern-definition
ADDRESS_RE = re.compile(r"(?i)\b\d{1,6}\s+[A-Z0-9][A-Z0-9 .'-]{1,50}\s(?:street|st|avenue|ave|road|rd|boulevard|blvd|lane|ln|drive|dr|court|ct|way|parkway|pkwy)\b")  # osito-audit: allow-pattern-definition
WINDOWS_ABSOLUTE_RE = re.compile(r"(?i)(?<![A-Z0-9_])[A-Z]:[\\/](?:[^<>:\"|?*\r\n]+[\\/]?)+")  # osito-audit: allow-pattern-definition
UNIX_ABSOLUTE_RE = re.compile(r"(?<![A-Za-z0-9_.:/])/(?!/)(?:[A-Za-z0-9._~-]+/)+[A-Za-z0-9._~/-]+")  # osito-audit: allow-pattern-definition
URL_RE = re.compile(r"(?i)\bhttps?://[^\s`\"'<>)\]]+")  # osito-audit: allow-pattern-definition
RESOURCE_ID_RE = re.compile(r"(?i)\b(?:account|policy|resource|workspace|vault|drive|chat|mail|calendar)[_-]?id\s*[:=]\s*[\"']?[A-Z0-9][A-Z0-9_-]{7,}")  # osito-audit: allow-pattern-definition
ACCOUNT_NUMBER_RE = re.compile(r"(?i)\b(?:account|policy)[ _-]?(?:number|no|id)\s*[:=]\s*[\"']?[A-Z0-9][A-Z0-9 -]{7,}")  # osito-audit: allow-pattern-definition
PRIVATE_KEY_RE = re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----")  # osito-audit: allow-pattern-definition
GENERIC_CREDENTIAL_RE = re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|password)\s*[:=]\s*[\"']?[A-Z0-9_./+=-]{16,}")  # osito-audit: allow-pattern-definition
OPENAI_TOKEN_RE = re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")  # osito-audit: allow-pattern-definition
GITHUB_TOKEN_RE = re.compile(r"\bgh(?:p|o|u|s|r)_[A-Za-z0-9]{20,}\b")  # osito-audit: allow-pattern-definition
SLACK_TOKEN_RE = re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{12,}\b")  # osito-audit: allow-pattern-definition
AWS_ACCESS_KEY_RE = re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")  # osito-audit: allow-pattern-definition
GOOGLE_KEY_RE = re.compile(r"\bAIza[A-Za-z0-9_-]{30,}\b")  # osito-audit: allow-pattern-definition
CONNECTION_URI_RE = re.compile(r"(?i)\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqps?)://[^\s:@/]+:[^\s@/]+@")  # osito-audit: allow-pattern-definition
CONNECTION_KV_RE = re.compile(r"(?i)\b(?:server|host)\s*=\s*[^;\s]+;[^\r\n]{0,200}\b(?:password|pwd)\s*=\s*[^;\s]+")  # osito-audit: allow-pattern-definition
ENTROPY_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9])[A-Za-z0-9+/=_-]{28,}(?![A-Za-z0-9])")  # osito-audit: allow-pattern-definition

CONTENT_PATTERNS = (
    ("PRIVATE_KEY", PRIVATE_KEY_RE),
    ("GENERIC_CREDENTIAL", GENERIC_CREDENTIAL_RE),
    ("OPENAI_TOKEN", OPENAI_TOKEN_RE),
    ("GITHUB_TOKEN", GITHUB_TOKEN_RE),
    ("SLACK_TOKEN", SLACK_TOKEN_RE),
    ("AWS_ACCESS_KEY", AWS_ACCESS_KEY_RE),
    ("GOOGLE_API_KEY", GOOGLE_KEY_RE),
    ("CONNECTION_STRING", CONNECTION_URI_RE),
    ("CONNECTION_STRING", CONNECTION_KV_RE),
    ("RESOURCE_IDENTIFIER", RESOURCE_ID_RE),
    ("ACCOUNT_OR_POLICY_IDENTIFIER", ACCOUNT_NUMBER_RE),
    ("WINDOWS_ABSOLUTE_PATH", WINDOWS_ABSOLUTE_RE),
    ("UNIX_ABSOLUTE_PATH", UNIX_ABSOLUTE_RE),
)

BINARY_MAGIC = (
    b"\x00",
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


@dataclasses.dataclass(frozen=True, order=True)
class Finding:
    rule_id: str
    path: str
    line: int | None = None
    detail: str = ""

    def as_dict(self) -> dict[str, object]:
        value: dict[str, object] = {
            "rule_id": self.rule_id,
            "path": self.path,
        }
        if self.line is not None:
            value["line"] = self.line
        if self.detail:
            value["detail"] = self.detail
        return value


class AuditConfigurationError(ValueError):
    """Raised for invalid audit roots or options."""


def _portable_relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (OSError, ValueError):
        return False


def load_denylist(path: Path | None) -> tuple[str, ...]:
    if path is None:
        return ()
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise AuditConfigurationError("The external denylist could not be read as UTF-8 text.") from exc
    terms: list[str] = []
    for line in raw.splitlines():
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        folded = value.casefold()
        if folded not in terms:
            terms.append(folded)
    if not terms:
        raise AuditConfigurationError("The external denylist contains no usable terms.")
    return tuple(terms)


def _denylist_offset(text: str, term: str) -> int:
    """Return a case-insensitive literal match without matching inside words."""
    folded = text.casefold()
    start = 0
    require_left_boundary = bool(term) and term[0].isalnum()
    require_right_boundary = bool(term) and term[-1].isalnum()
    while True:
        offset = folded.find(term, start)
        if offset < 0:
            return -1
        end = offset + len(term)
        left_ok = (
            not require_left_boundary
            or offset == 0
            or not (folded[offset - 1].isalnum() or folded[offset - 1] == "_")
        )
        right_ok = (
            not require_right_boundary
            or end == len(folded)
            or not (folded[end].isalnum() or folded[end] == "_")
        )
        if left_ok and right_ok:
            return offset
        start = offset + 1


def _pattern_definition_line(relative_path: str, line: str) -> bool:
    return relative_path == DETECTOR_SOURCE and PATTERN_DEFINITION_MARKER in line


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, max(offset, 0)) + 1


def _shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = collections.Counter(value)
    length = len(value)
    return -sum((count / length) * math.log2(count / length) for count in counts.values())


def _looks_high_entropy(value: str) -> bool:
    if len(value) < 28 or len(value) > 512:
        return False
    # Unlabelled random tokens normally mix digits with letters. Requiring a
    # digit avoids treating long Markdown paths and source-code identifiers as
    # secrets; labelled and provider-specific credentials are checked above.
    if not any(char.isdigit() for char in value):
        return False
    classes = sum(
        (
            any(char.islower() for char in value),
            any(char.isupper() for char in value),
            any(char.isdigit() for char in value),
            any(char in "+/=_-" for char in value),
        )
    )
    if classes < 3:
        return False
    if re.fullmatch(r"[0-9a-fA-F]{32,128}", value):
        return False
    return _shannon_entropy(value) >= 4.2


def _private_url(value: str) -> bool:
    candidate = value.rstrip(".,;:")
    try:
        parsed = urlsplit(candidate)
    except ValueError:
        return True
    host = (parsed.hostname or "").casefold()
    if not host or parsed.username or parsed.password:
        return True
    if host in {"localhost"} or host.endswith((".internal", ".local", ".localhost", ".lan", ".corp")):
        return True
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        return True
    if "." not in host and host != "localhost":
        return True
    query = (parsed.query + "&" + parsed.fragment).casefold()
    return any(name in query for name in ("access_token=", "auth=", "key=", "secret=", "signature="))


def _is_binary(sample: bytes) -> bool:
    if any(sample.startswith(magic) for magic in BINARY_MAGIC if magic != b"\x00"):
        return True
    if b"\x00" in sample:
        return True
    try:
        sample.decode("utf-8")
    except UnicodeDecodeError:
        return True
    return False


def _name_contains_sensitive_value(relative_path: str, deny_terms: Sequence[str]) -> bool:
    if any(_denylist_offset(relative_path, term) >= 0 for term in deny_terms):
        return True
    name = PurePosixPath(relative_path).name
    if EMAIL_RE.search(name) or PHONE_RE.search(name) or ADDRESS_RE.search(name):
        return True
    if any(pattern.search(name) for _, pattern in CONTENT_PATTERNS):
        return True
    if any(_private_url(match.group(0)) for match in URL_RE.finditer(name)):
        return True
    return any(_looks_high_entropy(match.group(0)) for match in ENTROPY_TOKEN_RE.finditer(name))


def _display_path(relative_path: str, deny_terms: Sequence[str]) -> str:
    return "<redacted-path>" if _name_contains_sensitive_value(relative_path, deny_terms) else relative_path


def _content_findings(
    text: str,
    relative_path: str,
    display_path: str,
    deny_terms: Sequence[str],
) -> list[Finding]:
    findings: list[Finding] = []
    for term in deny_terms:
        offset = _denylist_offset(text, term)
        if offset >= 0:
            findings.append(Finding("DENYLIST_CONTENT", display_path, _line_number(text, offset)))

    lines = text.splitlines()
    for line_index, line in enumerate(lines, start=1):
        if _pattern_definition_line(relative_path, line):
            continue
        for match in EMAIL_RE.finditer(line):
            if match.group(1).casefold() not in {"example.com", "example.org"}:
                findings.append(Finding("EMAIL_ADDRESS", display_path, line_index))
        if PHONE_RE.search(line):
            findings.append(Finding("PHONE_NUMBER", display_path, line_index))
        if ADDRESS_RE.search(line):
            findings.append(Finding("STREET_ADDRESS", display_path, line_index))
        for rule_id, pattern in CONTENT_PATTERNS:
            candidate_line = line
            if rule_id == "UNIX_ABSOLUTE_PATH":
                if line_index == 1 and line.startswith("#!"):
                    continue
                candidate_line = candidate_line.replace("/dev/null", "")
            if pattern.search(candidate_line):
                findings.append(Finding(rule_id, display_path, line_index))
        if any(_private_url(match.group(0)) for match in URL_RE.finditer(line)):
            findings.append(Finding("PRIVATE_URL", display_path, line_index))
        if any(_looks_high_entropy(match.group(0)) for match in ENTROPY_TOKEN_RE.finditer(line)):
            findings.append(Finding("HIGH_ENTROPY_STRING", display_path, line_index))
    return findings


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
    traversal_errors: list[Path],
) -> Iterable[tuple[Path, os.stat_result | None, bool, str | None]]:
    """Yield entries without following links or entering the root Git database."""
    def record_walk_error(error: OSError) -> None:
        filename = getattr(error, "filename", None)
        traversal_errors.append(Path(filename) if filename else root)

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


def run_audit(
    root: Path,
    *,
    denylist_path: Path | None = None,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
) -> list[Finding]:
    lexical_root = Path(os.path.abspath(os.fspath(root)))
    try:
        root_observation = lexical_root.lstat()
        root_rule = _structural_entry_rule(lexical_root, root_observation)
    except OSError as exc:
        raise AuditConfigurationError("The audit root could not be inspected safely.") from exc
    if root_rule is not None or not stat_module.S_ISDIR(root_observation.st_mode):
        raise AuditConfigurationError(
            "The audit root must be an ordinary directory, not a link or reparse point."
        )
    root = lexical_root.resolve()
    try:
        resolved_root_observation = root.lstat()
        resolved_root_rule = _structural_entry_rule(root, resolved_root_observation)
    except OSError as exc:
        raise AuditConfigurationError("The resolved audit root could not be inspected.") from exc
    if (
        resolved_root_rule is not None
        or not stat_module.S_ISDIR(resolved_root_observation.st_mode)
        or not _same_identity(root_observation, resolved_root_observation)
    ):
        raise AuditConfigurationError("The audit root changed identity while the audit started.")
    if not root.is_dir():
        raise AuditConfigurationError("The audit root must be an existing directory.")
    if max_file_bytes <= 0:
        raise AuditConfigurationError("The maximum file size must be a positive integer.")
    deny_terms = load_denylist(denylist_path)
    findings: list[Finding] = []

    try:
        root_children = sorted(root.iterdir(), key=lambda item: item.name.casefold())
    except OSError as exc:
        raise AuditConfigurationError("The audit root could not be enumerated.") from exc
    for child in root_children:
        if child.name not in EXPECTED_TOP_LEVEL:
            relative = child.name
            findings.append(Finding("UNEXPECTED_TOP_LEVEL", _display_path(relative, deny_terms)))

    seen_inodes: dict[tuple[int, int], str] = {}
    traversal_errors: list[Path] = []
    for path, observation, is_directory, structural_rule in _iter_entries(
        root,
        traversal_errors,
    ):
        relative = _portable_relative(path, root)
        display = _display_path(relative, deny_terms)
        parts = PurePosixPath(relative).parts
        name = PurePosixPath(relative).name

        if any(_denylist_offset(relative, term) >= 0 for term in deny_terms):
            findings.append(Finding("DENYLIST_NAME", "<redacted-path>"))
        if EMAIL_RE.search(name):
            findings.append(Finding("EMAIL_IN_NAME", "<redacted-path>"))
        if PHONE_RE.search(name):
            findings.append(Finding("PHONE_IN_NAME", "<redacted-path>"))
        if ADDRESS_RE.search(name):
            findings.append(Finding("ADDRESS_IN_NAME", "<redacted-path>"))
        if any(pattern.search(name) for _, pattern in CONTENT_PATTERNS):
            findings.append(Finding("SENSITIVE_VALUE_IN_NAME", "<redacted-path>"))
        if any(_looks_high_entropy(match.group(0)) for match in ENTROPY_TOKEN_RE.finditer(name)):
            findings.append(Finding("HIGH_ENTROPY_NAME", "<redacted-path>"))

        if observation is None:
            findings.append(Finding(structural_rule or "UNREADABLE_ENTRY", display))
            continue
        if structural_rule is not None:
            findings.append(Finding(structural_rule, display))
            continue
        if any(part.startswith(".") and part not in ALLOWED_HIDDEN_PARTS for part in parts):
            findings.append(Finding("HIDDEN_ENTRY", display))
        if is_directory:
            if path.name == ".git" and path.parent != root:
                findings.append(Finding("NESTED_GIT_REPOSITORY", display))
            continue
        if path.name == ".gitmodules":
            findings.append(Finding("GIT_SUBMODULE_CONFIG", display))
        if not stat_module.S_ISREG(observation.st_mode):
            findings.append(Finding("UNSUPPORTED_ENTRY", display))
            continue
        inode_key = (int(observation.st_dev), int(observation.st_ino))
        if observation.st_nlink > 1:
            prior = seen_inodes.get(inode_key)
            detail = "multiple filesystem links"
            findings.append(Finding("HARDLINK", display, detail=detail))
            if prior is None:
                seen_inodes[inode_key] = display
        else:
            seen_inodes[inode_key] = display
        if observation.st_size > max_file_bytes:
            findings.append(Finding("LARGE_FILE", display, detail=f"bytes={observation.st_size}"))

        suffix = path.suffix.casefold()
        if suffix in ARCHIVE_EXTENSIONS:
            findings.append(Finding("ARCHIVE_FILE", display))
        if suffix not in TEXT_EXTENSIONS and path.name not in TEXT_FILENAMES:
            findings.append(Finding("UNEXPECTED_FILE_TYPE", display))

        try:
            with path.open("rb") as stream:
                opened = os.fstat(stream.fileno())
                if (
                    not stat_module.S_ISREG(opened.st_mode)
                    or _is_reparse_point(opened)
                    or not _same_identity(observation, opened)
                ):
                    findings.append(Finding("IDENTITY_CHANGED", display))
                    continue
                sample = stream.read(min(MAX_TEXT_SCAN_BYTES, max(max_file_bytes + 1, 8192)))
        except OSError:
            findings.append(Finding("UNREADABLE_FILE", display))
            continue
        try:
            after = path.lstat()
            after_rule = _structural_entry_rule(path, after)
        except OSError:
            findings.append(Finding("UNREADABLE_ENTRY", display))
            continue
        if (
            after_rule is not None
            or not stat_module.S_ISREG(after.st_mode)
            or not _same_identity(observation, after)
        ):
            findings.append(Finding(after_rule or "IDENTITY_CHANGED", display))
            continue
        if _is_binary(sample):
            findings.append(Finding("BINARY_FILE", display))
            continue
        if observation.st_size > len(sample):
            findings.append(Finding("CONTENT_SCAN_TRUNCATED", display))
        text = sample.decode("utf-8")
        findings.extend(_content_findings(text, relative, display, deny_terms))

    for path in traversal_errors:
        candidate = path if path.is_absolute() else root / path
        try:
            relative = _portable_relative(candidate, root)
            display = _display_path(relative, deny_terms)
        except ValueError:
            display = "<redacted-path>"
        findings.append(Finding("UNREADABLE_ENTRY", display))

    try:
        final_root_observation = lexical_root.lstat()
        final_root_rule = _structural_entry_rule(lexical_root, final_root_observation)
    except OSError as exc:
        raise AuditConfigurationError("The audit root changed during traversal.") from exc
    if (
        final_root_rule is not None
        or not stat_module.S_ISDIR(final_root_observation.st_mode)
        or not _same_identity(root_observation, final_root_observation)
    ):
        raise AuditConfigurationError("The audit root changed identity during traversal.")

    return sorted(
        set(findings),
        key=lambda item: (item.rule_id, item.path, item.line or 0, item.detail),
    )


def format_findings(findings: Sequence[Finding], *, as_json: bool = False) -> str:
    counts = collections.Counter(finding.rule_id for finding in findings)
    if as_json:
        return json.dumps(
            {
                "status": "pass" if not findings else "findings",
                "finding_count": len(findings),
                "counts_by_rule": dict(sorted(counts.items())),
                "findings": [finding.as_dict() for finding in findings],
                "limitations": "Automated checks cannot guarantee confidentiality or publication safety.",
            },
            indent=2,
            sort_keys=True,
        )
    if not findings:
        return "PASS: no automated audit findings. Manual review is still required."
    lines = [f"FINDINGS: {len(findings)} automated finding(s)."]
    for finding in findings:
        location = finding.path
        if finding.line is not None:
            location += f":{finding.line}"
        detail = f" ({finding.detail})" if finding.detail else ""
        lines.append(f"- {finding.rule_id}: {location}{detail}")
    lines.append("Matched values are intentionally omitted. Manual review is still required.")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run local privacy, secret, and repository-structure checks.",
    )
    parser.add_argument("--root", default=".", help="Repository root to inspect.")
    parser.add_argument(
        "--denylist",
        help="Path to an external UTF-8 denylist. Keep this file outside the repository.",
    )
    parser.add_argument(
        "--max-file-bytes",
        type=int,
        default=DEFAULT_MAX_FILE_BYTES,
        help=f"Report files larger than this value (default: {DEFAULT_MAX_FILE_BYTES}).",
    )
    parser.add_argument("--json", action="store_true", help="Emit redacted JSON output.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        findings = run_audit(
            Path(args.root),
            denylist_path=Path(args.denylist) if args.denylist else None,
            max_file_bytes=args.max_file_bytes,
        )
    except AuditConfigurationError as exc:
        print(f"CONFIGURATION ERROR: {exc}", file=sys.stderr)
        return EXIT_USAGE
    print(format_findings(findings, as_json=args.json))
    return EXIT_FINDINGS if findings else EXIT_PASS


if __name__ == "__main__":
    raise SystemExit(main())
