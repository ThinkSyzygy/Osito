# Frequently Asked Questions

## Is Osito a PLM or PDM system?

No. It can organize engineering decisions, evidence, reviews, and links, but it does not replace controlled CAD, document management, configuration management, or enterprise lifecycle systems.

## Do I need Obsidian?

No. Osito uses ordinary text files. Any editor works. Note-taking applications may add navigation features but are optional.

## Do I need an AI service?

No. Core records, workflows, setup, validation, and local audits work without AI. AI is an optional assistant.

## Can AI approve changes?

No. AI may draft or check a proposal, but accountable humans approve project-state changes, risk acceptance, engineering conclusions, external messages, and publication.

## Is it safe to use with confidential projects?

Not by default. You must configure access control, storage, encryption, backups, project boundaries, model and connector policies, and organizational approval. Repository layout alone is not security.

## Does a passing audit prove the repository is safe to publish?

No. Automated scans miss semantic clues, proprietary combinations, re-identification risk, and uncertain licensing. Publication requires complete human review.

## Where should secrets go?

Use an approved secret manager, operating-system credential store, or environment injection mechanism. Never commit secrets or private denylists.

## Can projects live in separate repositories?

Yes. Separate repositories can strengthen access boundaries. Keep shared framework versions explicit and avoid copying confidential project examples into the framework.

## Should every record be a separate file?

Not necessarily. One-file-per-record improves identity and review at scale; registers can be simpler for small teams. Choose deliberately and preserve stable IDs, provenance, lifecycle, and authority.

## What happens when records conflict?

Do not silently choose. Record the conflict, identify the authority and evidence for each value, and route it to qualified review.

## Are meeting notes canonical project state?

They are canonical evidence of the meeting, not automatically current project state. Use a reviewed change set to update decisions, risks, actions, requirements, or phase status.

## Why are generated summaries noncanonical?

They may be stale, truncated, filtered, or wrong. Keeping canonical inputs separate makes summaries reproducible and repairable.

## Can I enable an email or cloud-drive integration?

Yes, after implementing and reviewing an adapter. No integration is authenticated or operational merely because it appears in the example configuration.

## What should I customize first?

Define workspace paths, information classifications, project boundaries, reviewer roles, stable ID conventions, and the minimum record types your team will maintain.

## How do I create a project?

Use:

```sh
python scripts/setup/create_project.py --root . --project-id demo-project --name "Demo Project" --fictional
```

The command uses fictional example values and labels the generated project accordingly. Review the generated files before real use.

## How do I run checks?

```sh
python scripts/validation/validate.py --root .
python -m unittest discover -s tests -p 'test_*.py'
python scripts/audit/sanitize.py --root .
```

Use an external denylist for migration or publication review.

## Does Osito certify engineering work?

No. Qualified engineers and the responsible organization remain accountable for methods, evidence, safety, quality, legal, and regulatory requirements.

## Is Osito stable?

No. It is alpha. Test upgrades in a sandbox and read migration notes before applying changes to operational work.

## Are the examples real?

No. All Osito examples are fictional, including names, organizations, dates, requirements, dimensions, test results, and decisions.
