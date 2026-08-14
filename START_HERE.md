# Start Here

Osito is a structured local engineering workspace. It keeps project context in plain files so an AI assistant can help without losing the sources, decisions, open questions, and human reviews that make engineering work understandable later.

> You interact with the AI. The AI interacts with Osito.

You remain responsible for engineering decisions and approve consequential changes. Osito also works without AI; the manual path is linked below.

## Fastest way to begin

Open this folder with an AI agent that can safely read and edit a local working directory. Examples include coding or desktop agents, editor agent modes, and similar filesystem-aware tools. A normal web chat can discuss files you upload, but it does not automatically have access to this folder.

Tell the local agent:

`Read START_HERE.md and onboard me to Osito.`

The agent should read `AGENTS.md` and [`prompts/system/osito-onboarding.md`](prompts/system/osito-onboarding.md), then guide you instead of asking you to learn the repository first.

## What happens next

The agent will:

1. explain Osito briefly and inspect the local setup without changing it;
2. ask about six short questions needed for a useful first project;
3. recommend a fictional sandbox, with no confidential material or external connectors;
4. show the proposed project location, command, templates, and files before writing;
5. ask for your explicit approval, then use Osito's existing project-creation tool;
6. help with your first natural-language engineering task.

Git and Python support the local workflow, but the agent can check them and explain any action when it becomes relevant. It should not silently access other projects, mail, chat, cloud storage, or private repositories.

## A first conversation

**You:** `Read START_HERE.md and onboard me to Osito.`

**Agent:** Briefly explains Osito, asks the setup questions, recommends a fictional sandbox, runs a dry-run, and shows exactly what would change. It waits for approval before creating anything.

After setup:

**You:** `I need a requirement that the enclosure survive a one-meter drop. Help me capture it and decide how we should validate it.`

**Agent:** Selects the requirements and engineering-analysis workflows, finds only the approved project records, separates the proposed requirement from the validation method, and asks for approval before updating project state. The agent does not approve the requirement or test plan itself.

## No AI agent?

Follow the [manual getting-started guide](docs/getting-started.md). It shows the same setup underneath, including configuration, project creation, validation, and local auditing.
