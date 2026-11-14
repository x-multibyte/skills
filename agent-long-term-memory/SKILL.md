---
name: agent-long-term-memory
description: "Configure, integrate, and manage long-term memory systems and cross-agent handoffs (e.g. ai-memory, MEMORY.md, custom providers)."
category: autonomous-ai-agents
---

# Agent Long-Term Memory Integration

AI agents (Hermes, Claude Code, Codex, etc.) traditionally operate in isolated, stateless sessions. This skill covers how to integrate, configure, and manage persistent, long-term memory systems and cross-agent handoffs.

## Concepts & Architecture

### Memory Types
1. **Episodic Memory**: Raw logs of prompts, tool calls, and assistant outputs. These tend to grow large and noisy.
2. **Semantic/Structured Memory**: Summarized or consolidated knowledge (e.g., wiki pages, rules, preferences) that is queryable (FTS5 or vector search) and injected before a turn.
3. **Session Handoffs**: A snapshot of "where things left off," loaded at the start of a session so a new agent can resume immediately.

### Integration Tradeoffs: MCP vs. Native Plugin

| Dimension | MCP Server Integration | Native Memory Provider Plugin |
|---|---|---|
| **Effort** | Low (configuration only) | Medium (requires plugin code) |
| **Auto-injection** | Manual (agent must call search tools) | Automatic (prefetch hooks inject context before turn) |
| **Lifecycle Events** | None (unless wrapper scripts are used) | Full (sync on turn, compress, session end) |
| **Use Case** | Quick startup, basic tool access | Deep integration, seamless agent experience |

---

## Key Workflows

### 1. Cross-Agent Handoffs
Cross-agent memory allows switching between different agents (e.g., from Claude Code to Codex, or Codex to Hermes) in the same working directory without losing context.
* **Mechanism**: The session-end hook of the current agent summarizes key accomplishments and next steps, writing it to a shared handoff store.
* **Resuming**: The session-start hook of the next agent reads this handoff and prepends it to the system prompt or first turn.

### 2. Managed Memory & Consolidation
* **Wiki-style memory**: Storing consolidated observations as markdown documents in a versioned repository (e.g. git) rather than raw chats.
* **Pinned vs. Decaying**:
  * **Pinned Memory**: Hard facts (architecture decisions, credentials, home lab IPs) that must never be modified or deleted by LLM consolidation.
  * **Decaying/Episodic Memory**: Consolidated session notes that can merge, shift, or clean up over time.

### 3. Homelab & Local Gateway Configurations
When integrating agent memory with a local gateway (e.g., 9Router) or homelab infrastructure:
* **Privacy**: Route consolidation LLM queries through local models (via 9Router) to ensure system architecture and asset details do not leave the local network.
* **Asset Mapping**: Keep a dedicated, pinned page of base URLs, DNS IPs (like Technitium DNS), and API tokens in the memory provider so the agent has immediate access without prompting.

---

## Linked Files

* [references/ai-memory-plugin.md](references/ai-memory-plugin.md) — Detailed integration guide for the `ai-memory` server and `ai-memory-hermes-plugin`.
