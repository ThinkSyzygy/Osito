# Contributing to Osito

Thank you for helping improve Osito. Contributions should make the framework safer, clearer, more portable, or more useful to engineering teams.

## Before opening an issue

- Search existing issues and documentation.
- Describe the user problem before proposing a specific implementation.
- State whether the change affects schemas, templates, scripts, prompts, examples, or documented behavior.
- Remove confidential, personal, proprietary, export-controlled, or licensed material from screenshots, logs, fixtures, and examples.
- For a suspected exposure, follow [Security](SECURITY.md) instead of opening a public issue.

## Contribution process

1. Create a focused branch.
2. Make the smallest coherent change.
3. Add or update tests when behavior changes.
4. Update affected documentation and examples.
5. Run local structural and sanitization checks.
6. Review the complete diff, including generated or hidden files.
7. Open a pull request explaining intent, risk, validation, and any unresolved concern.

## Pull-request expectations

A pull request should include:

- a concise problem statement;
- the design or documentation approach;
- files and workflows affected;
- tests and local checks run;
- compatibility or migration impact;
- privacy, licensing, security, and safety considerations;
- screenshots only when they contain fictional, publication-safe data;
- an explicit note for any check that could not be run.

Large architectural changes should include an implementation and migration plan. Avoid combining unrelated cleanup with functional changes.

## Tests

Run:

```sh
python -m unittest discover -s tests -p 'test_*.py'
```

Also run the local audit entrypoints under `scripts/audit/` before requesting publication review. Optional scanners may be absent; report that fact instead of installing software as part of a contribution.

Never claim that tests passed if they were not run. A passing test suite does not replace human engineering or confidentiality review.

## Privacy and fictional-example rules

All contributed examples must be explicitly fictional. Use invented organizations, people, dates, identifiers, requirements, dimensions, results, and decisions. Use `example.com` for email and web placeholders.

Do not contribute:

- client, employer, supplier, or prospective-client information;
- real project names, codenames, timelines, correspondence, or meeting notes;
- private addresses, accounts, contact details, resource identifiers, or local paths;
- actual product architecture, calculations, dimensions, test results, failures, or lessons learned;
- credentials, tokens, cookies, keys, connection strings, or authentication files;
- material copied from paid standards, client templates, employer documents, books, or uncertain sources.

Changing names is not sufficient when a combination of technical facts can re-identify a source.

## Licensing expectations

Contributors must have the right to submit their work under Apache License 2.0. Identify third-party material and its license in the pull request. Do not copy wording, templates, code, images, or data when ownership or compatibility is uncertain.

Prefer original explanations and links to authoritative public sources. Do not add third-party license text to the main project license unless required.

## Documentation standards

- Use plain language and define specialized terms.
- Keep procedures tool-neutral; isolate tool-specific adapters.
- Distinguish requirements from recommendations.
- Distinguish facts, assumptions, calculations, interpretations, and decisions.
- Use relative links for repository documentation.
- Provide POSIX and PowerShell commands when they differ.
- Avoid claims of compliance, certification, guaranteed safety, or autonomous engineering capability.

## Human review

AI assistance is allowed, but the contributor remains responsible for every submitted line. Review AI-generated content for technical correctness, fabricated citations, copied language, unsafe instructions, hidden data, and licensing problems.

All contributions must follow the [Code of Conduct](CODE_OF_CONDUCT.md), [Responsible AI use](docs/responsible-ai-use.md), and [Security and privacy](docs/security-and-privacy.md).
