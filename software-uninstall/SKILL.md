---
name: software-uninstall
description: Use when uninstalling CLI tools. Purges files and configs.
version: 1.0.0
author: roy
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [devops, uninstall, cleanup, bash, macos, cli, idempotency]
    category: devops
    requires_toolsets: [terminal]
---

# Software and CLI Clean Uninstall

## When to Use

- The user requests to uninstall, remove, or purge a CLI tool, developer agent, background service, or package.
- Writing cleanup or uninstall scripts for system tools.
- Cleaning up residual configurations, logs, caches, and global package manager symlinks.

## Standing Rules

- Pre-flight check first: every cleanup/uninstall script must inspect PATH, binary locations, config/cache directories, and running processes at the beginning. If the target is absent, exit 0 immediately to ensure idempotency and zero wasted cycles.
- Safety credential backup: if the tool stores credentials or configuration (e.g. `~/.<tool>/config.toml`, keys, tokens), archive the directory to `/tmp/<tool>_backup_$(date +%Y%m%d%H%M%S).tar.gz` before removing.
- Report real execution output: do not just display a plan or shell script; execute the script and verify that running it a second time exits 0 cleanly.

## Procedure

1. Discovery and Inventory:
   - Identify active processes: check `ps aux` and `pgrep` (see process regex pitfall below).
   - Find binaries and symlinks: check `which -a <cmd>`, `type -a <cmd>`, `/usr/local/bin`, `/opt/homebrew/bin`, and all NVM Node version bins (`~/.nvm/versions/node/*/bin`).
   - Identify package manager sources: check npm (`npm list -g --depth=0` across NVM and Homebrew npm), pip/pipx, Homebrew formulas/casks.
   - Locate persistent directories:
     - Configuration: `~/.<tool>`, `~/.config/<tool>`
     - macOS Application Support: `~/Library/Application Support/<tool>` or `@<scope>`
     - macOS Preferences: `~/Library/Preferences/${domain}.plist`
     - Logs and Caches: `~/Library/Logs/<tool>`, `~/Library/Caches/<tool>`
     - Temporary / Downloads: installer DMGs, zips in `~/Downloads`

2. Generate Idempotent Script:
   - Write a self-contained shell script (see `templates/uninstall-template.sh`).
   - Phase 0: Pre-flight check. Exit 0 if all components are absent.
   - Phase 1: Graceful process shutdown (SIGTERM -> sleep -> SIGKILL).
   - Phase 2: Safety archive of config / secrets to `/tmp/`.
   - Phase 3: Package manager uninstalls and binary symlink removals.
   - Phase 4: Removal of config, data, logs, and preference files.
   - Phase 5: Verification check.

3. Run and Validate:
   - Execute the script.
   - Run the script a second time to verify the pre-flight check triggers and returns exit code 0.
   - Confirm via `which <cmd>` that resolution fails as expected.

## Pitfalls

- `pgrep -f` substring traps: naive substring matching like `pgrep -f "dsh"` matches completely unrelated processes that contain `dsh` anywhere in their arguments (e.g. `--handshake-fd` in Chrome, Electron apps, or text editors). Always constrain process patterns with boundary delimiters: `pgrep -f "(^|/)<binary>($|[[:space:]])"`.
- Multi-runtime NVM isolation: global npm packages installed under one Node version in NVM do not show up when switching node versions. Check all version directories under `~/.nvm/versions/node/*/bin` and `~/.nvm/versions/node/*/lib/node_modules/`.
- Companion tool shadowing: tools often install companion CLI utilities or TUI frontends (e.g. `<tool>-tui`, `<tool>-desktop`) under different package names or via Homebrew npm rather than user NVM. Always search for companion binaries matching `<tool>-*` or `@<vendor>/*`.
- macOS Preference caching (`cfprefsd`): removing a `.plist` file directly from `~/Library/Preferences` can be re-written by macOS memory cache if the app or daemon is still cached. Terminate the app before removing the plist, or use `defaults delete <domain>`.
