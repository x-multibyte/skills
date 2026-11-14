---
name: agents-md-authoring
description: Use when generating or updating AGENTS.md/CLAUDE.md files.
version: 1.0.0
author: hermes-curator
license: MIT
metadata:
  hermes:
    tags: [documentation, project-context, agents-md, claude-md]
    related_skills: [codebase-doc-sync, hermes-agent-skill-authoring]
---

# AGENTS.md / CLAUDE.md authoring

## When to Use

- User asks to generate, write, or refresh AGENTS.md / CLAUDE.md for a repo (e.g. an /init flow).
- User asks what an agent should know before working in a repo, or "document the project for agents".
- A repo already has CLAUDE.md but needs an AGENTS.md operational layer (or vice versa).

Author or refresh the project-instruction file coding agents load every session. The deliverable is a working file backed by verified repo facts — never guessed commands or assumed conventions.

## Workflow

1. Inventory toolchain + manifest files first: package.json / pyproject.toml / *.csproj + *.sln / Makefile / Cargo.toml / go.mod / CI workflows / lockfiles. Read them and extract the EXACT commands (npm script names, Makefile targets, msbuild invocations).
2. Check what is actually installed on the host: `which msbuild xbuild mono dotnet wine` etc. A documented build command that needs an absent toolchain is a real constraint to note — e.g. the `dotnet` SDK cannot build non-SDK-style .NET Framework csproj (ToolsVersion 12.0 format).
3. Read existing docs (README, CLAUDE.md, HTML guides, docs/) but CROSS-CHECK claims against code — legacy repos carry stale docs. Example found in the wild: a setup guide claimed a server binds 127.0.0.1 while the code says `new TcpListener(IPAddress.Parse("0.0.0.0"), 6414)`.
4. Check git: `git ls-files` vs `.gitignore` interplay. A Dockerfile `COPY` of a gitignored build-output dir (bin/Debug) fails on fresh clone — a top-tier pitfall to record.
5. Observe conventions by grepping, don't assume: naming prefixes (e.g. `po*` send methods), comment/identifier language (Vietnamese codebase), commit message style via `git log --oneline`.
6. State tests/lint/CI existence explicitly: "No tests exist; nothing to run." Never invent a test command.

## Quality bar

- Under 100 lines — every line costs the agent context.
- Exact verified invocations only; never write "run the tests" if no test target exists.
- No generic advice ("write tests for new code", "follow best practices" — banned).
- Conventions must be OBSERVED, not assumed.
- Pitfalls section only for genuine trip-ups found; skip the section if none.
- Flat markdown: title + one-paragraph overview + focused sections (Dev environment / Build & test / Conventions / Pitfalls). No deep nesting.

## Pitfall patterns worth checking for

- gitignored files referenced by Dockerfile/scripts (fresh-clone breakage)
- docs that contradict code (bind addresses, ports, filenames)
- toolchain required by build but absent on the dev host
- generated/template files users must not hand-edit (embedded resources, lockfiles)
- plaintext credentials in data files (never commit real accounts)

## When a CLAUDE.md already exists

The new AGENTS.md should be the operational layer (commands, pitfalls, conventions) — not a duplicate of the architecture narrative. Reference the existing file for deep dives.

## Worked example

See `references/tsonline-server-example.md` for a full walk-through of authoring AGENTS.md for a legacy C# WinForms game server.
