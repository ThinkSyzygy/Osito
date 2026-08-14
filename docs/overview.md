# Overview

Osito is an open-source operating framework for AI-assisted engineering teams. It provides a practical way to organize technical work in ordinary text files while keeping authority, evidence, uncertainty, and human approval visible.

## The problem

Engineering teams rarely lack documents. They lack reliable answers to questions such as:

- Which record represents the current decision?
- What evidence supports this conclusion?
- Is this value measured, specified, calculated, or assumed?
- Did a meeting change project state, or merely discuss a possibility?
- Which risks block the next gate?
- Is an AI-generated summary fresh and bounded to the correct project?
- Can a new team member reproduce the reasoning?

Chat, email, notes, spreadsheets, CAD, and AI tools each hold fragments. Osito does not replace those tools. It gives their important outputs a controlled, traceable home.

## The framework

Osito combines four layers:

1. **Repository architecture** defines where projects, evidence, templates, workflows, archives, and generated views belong.
2. **Operational records** capture requirements, decisions, risks, assumptions, actions, validation, tests, changes, and phase status.
3. **Review workflows** convert new information into proposed changes and require human disposition before consequential updates.
4. **Local tooling** creates projects, validates structure, and scans for common publication and privacy risks.

AI-agent instructions sit above these layers as adapters. They describe how an agent should use the same workflows without becoming a separate source of truth.

## A typical information path

```text
source evidence
    -> proposed interpretation
    -> deterministic checks
    -> human review
    -> approved current record
    -> generated summary or dashboard
```

This path prevents a polished summary from silently outranking an approved record or an unreviewed model response from becoming a project decision.

## What a team can do

With the included material, a team can:

- configure a workspace;
- initialize a project;
- capture requirements and validation plans;
- ingest meeting notes through a review queue;
- record design decisions and engineering changes;
- maintain risks, assumptions, and actions;
- plan prototypes and tests;
- conduct generic design, manufacturing, tolerance, and calculation reviews;
- capture research and lessons learned;
- prepare readiness reviews;
- archive completed work;
- run local structural and sanitization checks.

## Tool neutrality

Osito uses Markdown, YAML, JSON, TSV, and Python-based local tools. Git is recommended for history and review. A Markdown editor is enough for normal use. Note-taking applications, AI coding agents, email systems, cloud drives, chat systems, calendars, and spreadsheets are optional.

No external integration is enabled or authenticated by this repository. See [Integrations](integrations.md).

## Limits

Osito requires configuration and maintenance. It does not provide access control, secure storage, backup hosting, regulatory compliance, engineering certification, or qualified review. AI output can be wrong, and automated scans can miss confidential or copyrighted material.

Start with [Getting started](getting-started.md), then review [Architecture](architecture.md) and [Responsible AI use](responsible-ai-use.md).

All examples in Osito are fictional.
