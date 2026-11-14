---
name: shell-path-diagnostics
description: Use when a CLI command is not found or not working.
version: 1.0.0
author: roy
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [shell, zsh, path, composer, cli, devops, laravel, troubleshooting]
    category: devops
    requires_toolsets: [terminal]
---

# Shell PATH and CLI install diagnostics

## When to Use

- A globally installed CLI answers "command not found", or "装了但命令不生效"
- The command works in your shell but not in the user's terminal, or only in some shells
- A `~/.zshrc` line is suspected of mangling PATH (duplicate or garbage entries)
- You need to know where a package manager puts its executables, and why that directory is off PATH

## Rule 1 - bound the investigation
Triage in ONE batch and stop at the first confirmed answer. Answer the question that was asked; do not go looking for the historical root cause.

Stop as soon as you know: (a) the binary exists on disk, (b) it runs, (c) the shell can resolve it. Then report plus one command the user can run to confirm.

Do NOT, unless the user explicitly asks for root-cause forensics:
- parse shell history to reconstruct what they typed
- date-forensics on wrapper/proxy files
- build isolated reproduction environments
- keep testing variations after the answer is already confirmed

Over-investigating this class of question ends with the user halting the session ("stop", 太麻烦, and similar). Treat that halt as the expected cost of the extra probes, not as bad luck. When the cause genuinely cannot be shown from evidence, say so plainly instead of manufacturing one.

## Procedure
Run the packaged probe first - one call, bounded output:

    sh scripts/diagnose-cli.sh <command>

It prints shell, resolution (`which -a`, `type`), a run check, the manager bin dirs that hold a same-named file, PATH entries mentioning managers, glued `#compdef` lines, and `zsh -n` rc syntax. Then, only for what it leaves open:

1. Not on PATH at all - compare the install layer's bin dir against PATH (table in `references/global-cli-install-layer.md`). Composer: `composer global config bin-dir --absolute`. Also check `echo $COMPOSER_HOME` / `composer global config home` for a divergence that sends a "successful" install somewhere off PATH.
2. Resolves in your shell but not in the user's terminal - you CANNOT validate a PATH or rc change from inside the running shell: PATH is inherited from the parent process, so old and new defects are indistinguishable. Re-test in a clean environment:

       env -i HOME="$HOME" TERM=xterm-256color /bin/zsh -lic 'which <cmd>; <cmd> --version'

3. rc file suspected - `zsh -n ~/.zshrc` for syntax, then the glued-line pitfall below.

## Pitfalls
- Glued completion block: a `X completion >> ~/.zshrc` append without a leading newline fuses onto the previous line, e.g. `export PATH="$HOME/.mimo.../bin:$PATH"#compdef mimo`. zsh accepts it silently (with `interactivecomments`, `#` only starts a comment at word start), exports a junk variable, and appends a `#compdef`-suffixed garbage entry to PATH. Detect with `grep -n '#compdef' ~/.zshrc` and by looking for any PATH entry containing `#`. Fix by inserting the newline; verify with `zsh -n ~/.zshrc` plus a clean-env shell.
- A garbage PATH entry pointing at a nonexistent directory is cosmetic: it never breaks command lookup. Fix it, but state explicitly that it was NOT the cause - otherwise the user walks away believing a solved non-issue was the bug.
- `command not found` is a fresh PATH-search failure: no file of that name existed in any PATH directory at that moment. Check wrapper mtimes before blaming PATH. An untouched wrapper keeps its install-date mtime, so a timestamp equal to a recent install means it was (re)created then - solid evidence for "the file was absent", which is usually the real answer.
- Package managers re-sync their wrappers on install/require: a missing `~/.composer/vendor/bin/<cmd>` is repaired by re-running `composer global require <pkg>` (it may print "Nothing to install, update or remove" and still re-write the proxy). Reinstall the package; do not try to patch PATH around it.
- Never test an install-layer theory against the user's real global install. Isolate it: `env COMPOSER_HOME=/tmp/probe composer global require <pkg>`.
- Run multi-line Python through execute_code, not a shell heredoc - heredocs trip the gateway safety filter and get refused before they run.

## Reporting
Plain text, facts only: what was verified and with which command, the one real defect found (if any), and the single command the user should run to confirm. Label unverified causes as inference. Do not dump raw PATH strings or reconstructed history at the user, and do not narrate the probes you discarded.

## Support files
- `references/global-cli-install-layer.md` - bin directory per package manager, composer global proxy mechanics, Laravel installer quirks.
- `scripts/diagnose-cli.sh` - one-shot bounded probe for a not-found/unusable CLI.
