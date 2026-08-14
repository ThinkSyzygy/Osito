# Osito

> An open-source operating framework for AI-assisted engineering teams.

Osito is a text-first starter system for engineers who need project records, technical evidence, reviews, and AI-agent work to remain understandable and auditable over time. It addresses a common failure mode in growing engineering efforts: decisions, assumptions, test evidence, meeting actions, and AI-generated material become scattered across tools and lose their authority, context, or owner.

## What Osito is

Osito is a configurable repository structure, set of workflows, templates, prompts, and local checks. It helps an individual engineer or small team:

- establish clear sources of truth;
- separate current state from historical evidence and generated views;
- track requirements, decisions, risks, assumptions, actions, tests, and changes;
- turn meeting notes into reviewable proposed updates;
- prepare design, manufacturing, calculation, and phase-readiness reviews;
- give AI agents bounded instructions and context;
- maintain project archives without losing provenance.

Osito is tool-neutral. Plain files and Git are sufficient. Markdown knowledge tools, AI coding agents, office tools, and external connectors are optional.

## What Osito is not

Osito is not a SaaS product, a PLM or PDM replacement, an autonomous engineer, a compliance-certified quality system, or a guarantee of design quality. It does not remove the need for access control, backups, qualified engineering judgment, regulatory review, or legal and security processes.

## Intended users

- Individual engineers organizing several technical workstreams
- Small hardware, product-development, or research teams
- Consultants who need strict project boundaries
- Teams introducing AI assistance without giving up human approval
- Maintainers building an internal engineering operating system from text files

## Core principles

1. **Current state has an explicit home.** Approved records outrank summaries and generated output.
2. **Evidence and interpretation are distinct.** Source notes and test artifacts are not silently promoted into conclusions.
3. **Human approval controls consequential changes.** AI may propose; accountable people decide.
4. **Context is bounded.** Project information does not cross boundaries by convenience.
5. **Provenance is part of the record.** Important claims identify their source and status.
6. **Generated views are disposable.** Dashboards and compiled context can be rebuilt from canonical records.
7. **Uncertainty stays visible.** Missing evidence is not a pass, and assumptions are not facts.
8. **Local checks support review.** Automation finds mistakes but cannot certify confidentiality or engineering correctness.

Read more in [Philosophy](docs/philosophy.md) and [Architecture](docs/architecture.md).

## Primary workflows

- Project initialization and configuration
- Requirement capture and validation planning
- Meeting ingestion with review-before-apply
- Decision, risk, assumption, and action management
- Prototype and test planning
- Design and manufacturing reviews
- Engineering change control
- Phase-readiness assessment
- Tolerance and calculation review
- Research and lessons-learned capture
- Project archival and maintenance
- Local structure, privacy, and sanitization checks

## Repository map

```text
config/      Example configuration and metadata conventions
docs/        Concepts, setup, operation, safety, and maintenance
framework/   Reusable engineering workflows and methods
prompts/     Tool-neutral AI prompt patterns
templates/   Blank project and record templates
examples/    A fully fictional worked project
scripts/     Local setup, validation, audit, and maintenance tools
tests/       Structural, sanitization, and example checks
reports/     Public-safe generated review summaries
```

Your configured workspace may add `projects/`, `archive/`, and a generated-output directory. Those working directories do not need to live in this framework repository.

## Quick start

1. Read [Installation](docs/installation.md) and [Security and privacy](docs/security-and-privacy.md).
2. Copy `config/osito.example.yaml` to a local configuration file.
3. Choose a workspace that has appropriate access controls.
4. Copy the project templates into a new, fictional sandbox project.
5. Run the local checks described in [Getting started](docs/getting-started.md).
6. Review the fictional example before adapting workflows to real work.

POSIX shell:

```sh
cp config/osito.example.yaml config/osito.local.yaml
python scripts/setup/create_project.py --root . --project-id demo-project --name "Demo Project" --fictional
python scripts/validation/validate.py --root .
python -m unittest discover -s tests -p 'test_*.py'
./scripts/audit/audit.sh
```

PowerShell:

```powershell
Copy-Item config/osito.example.yaml config/osito.local.yaml
python scripts/setup/create_project.py --root . --project-id demo-project --name "Demo Project" --fictional
python scripts/validation/validate.py --root .
python -m unittest discover -s tests -p 'test_*.py'
./scripts/audit/audit.ps1
```

`config/osito.local.yaml` is intended for local configuration and should remain untracked when it contains organization-specific paths or settings.

## Example usage

The repository includes a fictional project that demonstrates how a team can record a requirement, link it to a risk and validation method, capture a meeting, review proposed actions, document a decision, and archive the completed work. Every person, organization, date, requirement, dimension, result, and decision in the examples is invented.

Start with [Overview](docs/overview.md), then follow [Getting started](docs/getting-started.md).

## Security and privacy warning

Do not point an AI agent at a confidential repository unless you have verified the model, connector, retention, network, access-control, and organizational policies that apply. Repository structure is not a security boundary. Keep secrets outside tracked files, minimize access, separate projects, review exports, and use the local audit tools before sharing.

Automated scans can miss sensitive facts, combinations of facts, licensed material, and re-identification clues. Human review is mandatory before publication or external sharing. See [Security and privacy](docs/security-and-privacy.md).

## Responsible AI warning

AI output may be incomplete, fabricated, stale, unsafe, or technically plausible but wrong. Qualified people must review engineering conclusions, calculations, requirements, risk acceptance, test interpretation, and release decisions. Osito does not authorize an AI agent to approve its own work or to make legal, safety, quality, or regulatory decisions.

See [Responsible AI use](docs/responsible-ai-use.md).

## Maturity

Osito is **alpha software and documentation**. Interfaces, templates, schemas, and workflows may change. Use it first in a fictional or low-risk sandbox, maintain backups, and review changes before adopting it for operational engineering work.

Maintainers preparing a release should use the [Publication checklist](PUBLICATION_CHECKLIST.md). GitHub private vulnerability reporting is recommended when available, but it is optional.

## Customize Osito

Begin with the example configuration, then adapt record types, lifecycle states, review gates, templates, and optional integrations. Preserve the core invariants: explicit authority, provenance, bounded context, human approval, reversible change, and honest validation.

See [Configuration](docs/configuration.md), [Implementation guide](docs/implementation-guide.md), and [Customization guide](docs/customization-guide.md).

## Local checks

Run the repository tests after changing templates, schemas, examples, scripts, or links:

```sh
python scripts/validation/validate.py --root .
python -m unittest discover -s tests -p 'test_*.py'
python scripts/audit/sanitize.py --root .
```

Use `./scripts/audit/audit.sh --denylist "$DENYLIST_PATH"` on POSIX or `./scripts/audit/audit.ps1 -Denylist $DenylistPath` in PowerShell before sharing or publication. Supply sensitive terms through an external denylist; never commit a real denylist containing private names or identifiers.

Checks reduce risk but do not prove that a repository is confidential-data-free, correctly licensed, or technically correct.

Osito v0.1 assumes a local workspace used by an individual or trusted small team, with other writers stopped during setup, archive, validation, and audit operations. The bundled tools are not a sandbox and do not defend against a malicious process or user that can modify the same working tree.

## Contributing

Read [Contributing](CONTRIBUTING.md), follow the [Code of Conduct](CODE_OF_CONDUCT.md), and include tests or documentation updates for meaningful behavior changes. Contributions must use fictional examples and must not include employer, client, supplier, personal, or proprietary material.

## License

Osito is licensed under the [Apache License 2.0](LICENSE).
