# Migration Guide

Migration is an information-governance project, not a bulk file copy. The safest approach inventories the source, defines authority, reconstructs the destination, and validates both privacy and usefulness.

## 1. Establish boundaries

Before reading source content:

- identify source and destination roots;
- confirm the destination is outside the source;
- define permitted write locations;
- confirm the destination does not already contain unrelated work;
- prohibit copying source Git history;
- define confidentiality, ownership, licensing, and publication rules;
- decide who approves ambiguous material.

Keep temporary reports and private denylists outside any public destination.

## 2. Capture source state

Record a read-only snapshot:

- repository root, branch, commit, status, remotes, and submodules when Git is used;
- relative file inventory, type, size, and hash;
- documented exclusions such as caches.

Repeat the snapshot after migration. Do not attempt destructive restoration if unexpected source changes appear; stop and investigate.

## 3. Inventory and classify

Classify each source item:

- `RECONSTRUCT_FROM_CONCEPT`
- `SAFE_TEXT_AFTER_LINE_REVIEW`
- `EXCLUDE`
- `UNCERTAIN_EXCLUDE`

Default to reconstruction. Use direct text only after line-by-line safety, ownership, and licensing review. Exclude binary, archival, application-state, correspondence, and uncertain licensed material by default.

## 4. Build a private denylist

Outside the destination, collect sensitive:

- organizations, people, projects, products, and codenames;
- domains, emails, phone and address fragments;
- vendors, suppliers, and account identifiers;
- internal acronyms and distinctive phrases;
- resource IDs and private URLs.

Do not print the denylist in public reports or commit it.

## 5. Design the destination

Map reusable concepts to a clean structure:

- governance and agent instructions;
- configuration and metadata;
- workflows and templates;
- fictional examples;
- local validation and audit;
- maintenance and publication guidance.

Do not preserve a private directory or filename merely because it is familiar.

## 6. Reconstruct

Write public material from scratch:

- express general purpose and inputs;
- remove identities and source-specific chronology;
- replace real technical data with simple fictional examples;
- replace proprietary implementation with an independently designed interface;
- replace licensed content with a citation, link, or instruction to obtain it;
- keep useful workflow depth.

Changing names is not reconstruction when technical combinations remain recognizable.

## 7. Migrate operational records privately

For an internal deployment, transform records into the configured metadata schema. Preserve stable source references in a private mapping, not in a public framework.

Use:

- dry-run transformation;
- per-record disposition;
- explicit conflict lists;
- source and target hashes;
- human review;
- reversible cutover;
- post-cutover reconciliation.

Do not infer current state from the newest-looking or most polished file.

## 8. Validate the destination

Run:

```sh
python scripts/validation/validate.py --root .
python -m unittest discover -s tests -p 'test_*.py'
python scripts/audit/sanitize.py --root . --denylist "$DENYLIST_PATH"
```

Perform separate manual reviews for:

1. identities and entities;
2. proprietary engineering information;
3. secrets and repository security;
4. copyright and licensing;
5. usefulness;
6. public readiness;
7. adversarial re-identification.

Automated scanning is not sufficient.

## 9. Cut over

For an internal workspace:

- freeze or record the source checkpoint;
- apply only approved migration records;
- retain legacy history with an authority notice;
- switch generated views to the new canonical source;
- validate counts, links, provenance, and boundaries;
- test rollback before declaring completion.

## 10. Publish separately, if authorized

Use independent Git history for a public framework. Review author metadata, full history, visibility, contacts, links, and repository settings. Keep the repository private until [Publication checklist](../PUBLICATION_CHECKLIST.md) is complete.

Migration success does not establish that public release is safe.
