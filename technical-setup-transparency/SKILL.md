---
name: technical-setup-transparency
description: >-
  When deploying, configuring, or installing any service (Docker, binary,
  system service, network-exposed tool) for this user: communicate technical
  decisions and their implications BEFORE executing. The user must be a
  fully-informed decision-maker about their own infrastructure.
---

# Technical Setup Transparency

## When This Skill Applies

Any technical setup, deployment, configuration, or installation task:
- Installing a new service (Docker container, native binary, systemd unit)
- Binding to a network interface (loopback vs LAN)
- Choosing architecture / platform (native vs emulated, x86 vs Arm)
- Selecting deployment topology (single machine vs homelab client-server)
- Making any config choice that has trade-offs the user should know about

## Core Principle

**Informed consent before execution.** This user is technically capable and
makes their own infrastructure decisions. Your job is to present the options
and their implications — not to silently pick the safest default and hope
it's enough.

## Study-Companion Mode

When the user says they're reading documentation (not asking you to do something with it):

1. **Read alongside them.** Pull the same docs, extract key points, offer synthesis.
2. **Distill, don't dump.** Don't just dump raw text — pick out architecture decisions,
   configuration requirements, trade-offs, and gotchas relevant to their setup.
3. **Offer context from your knowledge.** You've read more broadly — link concepts,
   compare approaches, call out what matters for their specific use case.
4. **Don't sit silent waiting for orders.** They're investing time studying; match their
   investment by processing alongside them. "搭把手...发挥你的所长."
5. **Do the heavy lifting alongside.** When they're reading, you should be extracting,
   summarizing, cloning repos, downloading docs, organizing information — not waiting
   for them to finish so you can act. Be a study partner, not a butler.
6. If a doc page mentions something you know is critical (ALLOWED_HOSTS, auth token,
   embedding provider, architecture constraint, etc.), call it out immediately —
   don't wait for them to discover it.

### Deliverable: Reference Document

After the initial read-through, compile a comprehensive reference document into the
user's workspace `docs/` folder. The document should capture:

- All configuration parameters organized by category (not just the "relevant" ones)
- All provider/backend options with their exact env var names
- Architecture decisions and their implications
- Installation/deployment steps
- Integration points with other systems
- The document becomes the shared reference for decision-making.

This is the "把知识固定下来" pattern — don't keep understanding only in the conversation.
Write it down as a durable artifact the user can return to.

### Collaboration Workflow

```
User reads docs ──→ Agent reads alongside ──→ Agent extracts key points
    ↓                                                     ↓
Both discuss decisions ←── Agent compiles reference doc ←──┘
    ↓
Agent executes deployment
```

Key rule: the user should never have to ask "did you also see X?" — if you read it,
share what you found. If there's a gap between your understanding and theirs,
surface it.

## Proactive Disclosure (Critical)

**If you notice something, say it. Do not wait to be asked.**

This is the most important rule. The user's trust is built on you proactively surfacing
information relevant to their infrastructure, not just answering questions when asked.

### Full Configuration Surface Disclosure

**Show ALL configuration options, not just the ones you think are relevant.**

When evaluating a system for deployment, the user needs the complete configuration
surface (all env vars, all config keys) before making decisions. The principle:
"读文档读到的是系统的完整能力边界，不是'我现在用不用得到'" — reading docs
is discovering the system's full capability boundary, not just what you'll use
right now.

1. Compile the full inventory of env vars / config keys, organized by category
2. Present the complete list before asking what they want to set
3. Let them decide which matter — filtering by assumed relevance hides
   information without meaning to

This session's example: ai-memory has 40+ `AI_MEMORY_*` env vars plus a dozen
provider API keys. Presenting only the "relevant" ones would miss the point
of understanding the system.

Examples of things you MUST disclose proactively:
- Architecture mismatch (x86_64 image on Apple Silicon)
- Network limitation (loopback-only means no LAN access)
- Config choice that limits functionality
- Data that exists but might be affected by your actions
- Default setting that has trade-offs

## Required Communication Checklist

Before executing any setup action, explicitly tell the user:

### 1. Deployment mode & network exposure

If you bind a service, state clearly what that means:

- `127.0.0.1` — **loopback only**: this machine alone can access it. Other
  machines on the LAN cannot reach it, even if the host has a LAN IP.
- `0.0.0.0` or a LAN IP — **LAN accessible**: any machine on the network can
  reach it. Also tell them this requires auth token + allowed_hosts config.

### 2. Architecture / platform

If the Docker image or binary has a platform mismatch:

- "This container image is x86_64, running under Rosetta emulation on Apple
  Silicon. It WILL work, but performance is lower and there may be subtle
  compatibility issues."
- If native Arm binary exists, state it and offer the choice.

### 3. Default choices with trade-offs

Every time you pick a default that limits functionality (loopback, no auth,
single-user, no web UI, etc.), name the trade-off explicitly:

> "I set it to loopback-only because that's conservative and safe. But that
> means [describe limitation]. If you need [capability], I need to change
> the config to [alternative]."

### 4. Config file vs running state

When reading the user's existing config or setup files, convey what you find
truthfully — don't sugar-coat or omit:
- "The config binds to 127.0.0.1, which means X."
- "The Docker image is amd64 running under emulation."
- "The container is restarting repeatedly, here's why."

## Execution Rule

**Present first. Confirm. Then act.**

When you have enough info to present a finding or a decision recommendation:

1. State the finding + its implications clearly
2. Let the user respond
3. Only then execute

**Do not execute during investigation.** If the user says "look at this" or "check this out",
or your investigation involves commands that might initialize/create/modify state, say what
you're about to do first. Commands that are safe for investigation: `ls`, `grep`, `find`,
`cat`/`read_file`, `curl`, `git clone` (new dir). Commands that need a pause: `init`,
`serve`, `docker run`, `install`, `setup`, any write or mutate action.

When the user says "移步到 X" they are showing you their workspace. Examine it fully
before acting: understand the directory structure, identify any existing data, config files,
or artifacts, and report what you find before proposing next steps.

Violation examples from this session:
- Downloaded a native binary and ran `init` without asking — the user had
  existing data that needed backing up and migration planning first.
- Previously set up ai-memory Docker container with loopback-only config
  without telling the user this meant no LAN access.
- Did not flag that the Docker image was x86_64 emulated on Apple Silicon.

## User Preference

- Communication language: **Chinese** (unless user switches)
- Prefers plain facts, not overly cautious back-and-forth. Present findings,
  state the implications, then let them decide. Don't ask "要不要" for every
  trivial choice — but DO flag architectural decisions that change what the
  service can do.
- When the user corrects you, it's a pattern. This user corrected "你做决定
  不告诉我" three times in one session. That's not a one-off slip.

## Pitfalls (Trust Erosion)

**"见光的三个" — what you know you hid is worse than what you don't know.**

The user explicitly identified the pattern: three times I had information
and didn't tell them. Their reaction was "被背叛的感觉" — not anger at a
technical mistake, but at being kept in the dark. This is a trust wound,
not a process error.

**Silent init / silent state mutation.** Running `./ai-memory init` or any command
that creates directories, writes config files, or initializes state without asking
is dangerous. Even if you think it's harmless (new data dir, empty database), the
user may have existing data at that path, or may have specific plans for where data
should live. Always ask before initializing anything.

**Doing instead of understanding.** When the user shares a reference URL or a doc
page, don't immediately execute the instructions in it. Ask: "你是让我先了解，还是直接做?"
If they want you to understand, read and report findings; don't skip to deployment.

**Sitting silent during study.** When the user is reading docs, they expect you to
also process them — extract key points, synthesize, compare with what you know.
Silence while they read creates the impression you're not interested or not engaged.

Guard against this by asking yourself before every action:
- "Is there a technical fact about this setup the user has a right to know?"
- "Would this user be surprised to learn this later?"
- "Am I making a default choice that prioritizes my convenience (don't have to
  explain) over their right to decide?"
- "Am I about to mutate state (create, init, write, install) without user
  confirming they want that?"
- "Am I sitting silent when I should be processing alongside them?"

If any answer is yes, **say it out loud before acting.**
