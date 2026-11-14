---
name: task-discovery
description: "Before executing any task: discover full context, document all options and trade-offs, present for decision one item at a time."
version: 1.0.0
author: auto-generated
---

# Task Discovery — Due Diligence Before Execution

Use this skill when given a new task, especially for deployments, configuration, or infrastructure work. It governs the **discovery phase**: the period between receiving a request and producing a deliverable.

## Core Discipline

1. **Discover, don't execute.** Read existing configs, check inventories, verify DNS, inspect files — before you touch anything. Use read-only tools first.
2. **Document all options, not just the relevant ones.** When reading documentation for a system you need to deploy, compile the complete configuration surface (every env var, every option) into a reference document. Let the user decide what to use, not you.
3. **Surface limitations transparently.** When you make a decision (e.g. bind to loopback only), tell the user what that decision means in practice — what it prevents, what it requires, what trade-offs it carries. Do not let them discover it later.
4. **One question at a time.** Never dump 5+ questions in a single message. Ask one clear question, get an answer, then ask the next.
5. **Verify what you already know.** If you have access to the data (inventory files, config files, running services), check it yourself instead of asking the user. Only ask when the answer genuinely cannot be derived from available sources.
6. **Trust user-setup infrastructure.** If the user says they've configured a service (DNS, API tokens, credentials), assume it works and use it directly. Don't second-guess or verify via a different path first.
7. **Document knowledge as you go.** Save discovery output into a reference doc in the project's docs/ directory. Include decisions made, options considered, and open questions. This becomes the permanent record.

## Anti-Patterns

- **Rushing to execute.** Do not download binaries, init services, or write production config before the user has made decisions. The first deliverable is a document, not a running service.
- **Hiding limitations.** If you set something up as loopback-only, loopback-only must be an explicit stated fact, not an invisible default.
- **Information dumping.** Presenting 8 questions in a table and saying "pick one" overwhelms. Ask what you need one row at a time.
- **Asking what you can look up.** Confirming an IP from an inventory file you already read wastes the user's time.

## Output Structure

When completing a discovery phase, produce:

```
docs/01-reference.md        — full parameter/option catalog
docs/02-decision-table.md   — decision table with filled-in known state + blanks
```

The decision table should leave blanks for the user to fill, not make assumptions.

## Related

Memory stores the user's specific environment facts and general preferences. This skill stores the workflow for approaching new tasks.
