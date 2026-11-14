---
name: hermes-tool-offboarding
description: "Use when removing a tool's integration from Hermes config."
---

# Offboarding a Tool Integration from Hermes

When a user replaces or abandons a tool previously wired into Hermes, removing just one piece leaves zombie cron jobs, orphan plugins, and stale env vars. Sweep ALL touchpoints before declaring done.

## Touchpoint checklist

1. **Cron jobs** — `cronjob action='list'`; remove any job whose prompt/script references the tool. Jobs may use `no_agent` scripts, so also check `~/.hermes/scripts/` for helpers referenced by `script:` fields.
2. **Plugins** — two config keys plus a directory:
   - `hermes config set plugins.enabled '[<surviving names>]'`
   - delete the `plugins.entries.<name>` block from `~/.hermes/config.yaml` (`--delete` if supported, else edit)
   - `rm -rf ~/.hermes/plugins/<name>/`
3. **Skills** — `~/.hermes/skills/<name>/`. Check for sibling skills from the same integration (`grep -ril <tool> ~/.hermes/skills --include SKILL.md`).
4. **Env vars / secrets** — `grep -n TOOL_* ~/.hermes/.env` and `grep -i <tool> ~/.hermes/config.yaml`.
5. **Shell rc files** — `grep <TOOL>_ ~/.zshrc ~/.zshenv ~/.zprofile`.
6. **launchd / background processes** — `~/Library/LaunchAgents/*tool*` plists.
7. **The repo/project itself** — ask the user whether to keep or delete; never assume.

## Pitfalls

- `hermes config set` nested-key `--delete` may not exist; verify by grepping config.yaml afterward.
- Deleting directories without explicit consent gets blocked by approval gates — batch all destructive steps into ONE confirmation question listing every path, then execute after consent.
- Gateway picks up plugin changes on restart; mention this if the user expects tools to vanish mid-session.
