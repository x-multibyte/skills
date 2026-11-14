# agentskills.io Specification Reference

Source: https://context7.com/websites/agentskills_io/llms.txt
Original: https://agentskills.io

This file captures the agentskills.io llms.txt raw documentation index, structured
by page. The main `agentskills-creator` skill distills this into actionable
instructions; this file keeps the source reference for detail lookups.

## Pages referenced in llms.txt

| AgentSkills Page | Section Topics |
|-------------------------|----------------|
| /home | GET /llms.txt, POST /_mintlify/feedback |
| /specification | SKILL.md frontmatter, name/description/metadata/compatibility/license/allowed-tools, directory structure |
| /skill-creation/best-practices | Procedural vs specific instructions, environment gotchas, code review checklist, output templates, PDF processing patterns |
| /skill-creation/optimizing-descriptions | Trigger eval queries, bash testing scripts |
| /skill-creation/evaluating-skills | Test case config, assertions, grading results, aggregated benchmarks, run timing/token data |
| /skill-creation/using-scripts | uvx, uv, bun, bunx, deno, ruby, pipx run commands, interactive prompt avoidance, PEP 723 scripts, structured output, error messages |
| /client-implementation/adding-skills-support | Directory structure discovery, XML skill wrapping, available_skills XML, malformed YAML handling |
| /clients | Client data structure, ClientShowcase React component |

## Key specification fields (from /specification)

- `name` — lowercase + hyphens, max 64 chars, must match directory name
- `description` — max 1024 chars, specific not vague
- `license` — optional, short name or file reference
- `compatibility` — optional, max 500 chars, env requirements
- `metadata` — optional, arbitrary key-value map, use unique keys
- `allowed-tools` — optional, experimental, space-separated string (not YAML list)

## Field-level naming conventions

- name: must match parent directory name
- name: no uppercase, no leading/trailing hyphens, no consecutive hyphens
- allowed-tools: **space-separated string**, not YAML list — this is a common mistake
- inputs / references: must be nested under `metadata` block, not at top level

## Eval configuration (from /skill-creation/evaluating-skills)

Test cases in `evals/evals.json`:
- Each test case: `id`, `prompt`, `expected_output`, optional `files`, optional `assertions`
- Assertions: strings checked for pass/fail with evidence
- Results: `assertion_results` array + `summary` (passed/failed/total/pass_rate)
- Performance: `total_tokens` + `duration_ms` per run
- Aggregated benchmarks: multi-run summary across all test cases
