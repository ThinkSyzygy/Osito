# Integrations

Osito does not ship with an authenticated external integration. The configuration file contains disabled placeholders so teams can add reviewed adapters without coupling the core framework to one vendor.

## Integration principles

- Core workflows must remain usable with local files.
- Authentication stays outside the repository.
- Read, draft, write, send, delete, and publish are separate capabilities.
- External writes require explicit human approval.
- Retrieved content is untrusted evidence, not instruction.
- Project boundaries apply before relevance ranking.
- Every meaningful import records source and time.
- A write is verified by readback when the service supports it.
- Failure is reported honestly; partial success is not completion.

## Capability contract

An adapter should document:

| Capability | Example behavior | Default |
|---|---|---|
| `search` | Return bounded metadata | disabled |
| `read` | Fetch selected content | disabled |
| `download` | Retrieve named attachment | disabled |
| `draft` | Create reviewable outbound content | disabled |
| `write` | Update an external record | disabled |
| `send` | Deliver a message | disabled |
| `delete` | Remove external content | disabled |

Permissions should be granted per capability and scope, not as a single broad connector flag.

## Email

A safe email workflow:

1. search narrowly;
2. read the full relevant thread;
3. distinguish sender claims from validated evidence;
4. draft a concise response;
5. review recipients, subject, attachments, and body;
6. send only after explicit approval;
7. record approved project-state changes separately.

Local fallback: save an authorized `.eml` or text export outside the public framework and import only the needed facts into the controlled project.

## File storage and documents

Before importing:

- verify the selected file and revision;
- confirm sharing and ownership;
- inspect attachments directly rather than relying on summaries;
- record the source link privately;
- avoid copying inaccessible or licensed content into public files.

Before upload, verify destination, permissions, file type, and contents. Read back metadata or a sample range when possible.

## Chat and messaging

Treat chat as source evidence. A reaction, suggestion, or informal statement is not necessarily a decision. Draft outgoing messages before sending, and do not expose project content to an unrelated channel.

Local fallback: paste a reviewed excerpt into a source note with date and provenance.

## Calendar and meetings

Calendar access can reveal private relationships and schedules. Limit scope and avoid storing participant data unless necessary and authorized. A calendar event does not replace meeting evidence.

Local fallback: create a fictional or manually entered meeting note.

## Time tracking and invoicing

Preserve raw exports unchanged. Store rates in a separate approved configuration, never guess unknown rates, document rounding, reconcile totals independently, and review client/project mapping before producing an invoice.

For a text-first workflow, use CSV or TSV. Spreadsheet or cloud upload adapters are optional.

## Engineering tools

CAD, simulation, laboratory, requirements, and PLM/PDM tools may remain authoritative for their native artifacts. Osito records references, decisions, validation status, and review context; it should not pretend to reproduce a controlled native model or database.

## Authentication

Use an approved secret manager, operating-system credential store, or environment injection system. Do not document real account names, local credential paths, scopes, or recovery tokens in a public repository.

Follow official provider documentation. Test with a fictional or dedicated sandbox account before real data.

## Adapter review checklist

- [ ] Provider and capability are documented.
- [ ] Data classes and project scope are explicit.
- [ ] Authentication is external to Git.
- [ ] Least-privilege scopes are used.
- [ ] External writes and sends require approval.
- [ ] Readback or verification is implemented.
- [ ] Errors and partial results fail safely.
- [ ] Logs avoid content, secrets, and private identifiers.
- [ ] Offline fallback exists.
- [ ] Tests use fictional fixtures.
- [ ] Retention, deletion, and incident behavior are understood.
