# Security Policy

Osito is an alpha framework for organizing engineering work. It is not a security boundary, secret manager, access-control system, or compliance certification.

## Reporting a security or privacy issue

Do not open a public issue for a suspected exposure.

If GitHub private vulnerability reporting is available for this repository, use it. Otherwise, use an existing private maintainer channel if one is available. If no private channel is available, retain the details until one can be arranged rather than posting sensitive information publicly.

GitHub private vulnerability reporting is optional for Osito v0.1. Its absence is not by itself a publication blocker, and this repository does not publish a placeholder security address.

Do not include live credentials, personal data, client data, or proprietary engineering information in an initial report. Provide the minimum information needed to establish impact, then coordinate a safer transfer method.

## Reportable issues

- Exposed credentials, tokens, keys, cookies, or connection strings
- Personal-data, client-data, or proprietary-information exposure
- Cross-project context leakage
- Unsafe automation or missing human-approval controls
- Malicious prompt content or instruction injection
- Dependency compromise or unsafe dependency guidance
- Sanitization scripts that miss a supported high-confidence pattern
- Examples or history that enable re-identification
- Build, archive, or export behavior that includes unintended files

## Include in a report

- affected version or commit;
- affected file or workflow, without reproducing sensitive content;
- impact and likely exposure boundary;
- minimal reproduction steps using fictional data;
- whether a credential may require rotation;
- suggested mitigation, if known.

## Maintainer response

Maintainers should:

1. acknowledge the report through a private channel;
2. limit further access or distribution;
3. preserve minimal evidence for investigation;
4. rotate credentials or revoke access when relevant;
5. remove sensitive material from the current tree and, when necessary, repository history;
6. review mirrors, forks, releases, caches, and generated artifacts;
7. rerun local audit and structural checks;
8. document a public-safe remediation summary.

## Supported versions

During alpha development, only the current default branch is expected to receive security fixes. This policy may change before a stable release.

## Responsible handling

Automated scanners cannot guarantee confidentiality. Do not upload a private repository to an external scanner without authorization. Keep denylist files and incident evidence outside the public repository. See [Security and privacy](docs/security-and-privacy.md).
