#!/bin/sh
# Bounded one-shot triage for "<cmd> is installed but not found / not working".
# Usage: sh diagnose-cli.sh <command>
# Prints facts only. Read them, report, stop.

cmd="$1"
if [ -z "$cmd" ]; then
  echo "usage: diagnose-cli.sh <command>" >&2
  exit 2
fi

O="$HOME"

printf '== shell ==\nSHELL=%s  ZSH_VERSION=%s\n\n' "$SHELL" "${ZSH_VERSION:-n/a}"

printf '== resolution ==\n'
command -v "$cmd" 2>/dev/null || echo "NOT on PATH"
which -a "$cmd" 2>/dev/null
type "$cmd" 2>/dev/null
alias "$cmd" 2>/dev/null

printf '\n== runs? ==\n'
"$cmd" --version 2>&1 | head -3
if "$cmd" --version >/dev/null 2>&1; then echo "runs OK"; else echo "RUN FAILED"; fi

printf '\n== same-named file in known bin dirs ==\n'
found=0
for d in "$O/.composer/vendor/bin" "$O/.config/composer/vendor/bin" "$O/.local/bin" \
         "$O/.cargo/bin" "$O/.bun/bin" "$O/Library/pnpm" "$O/Library/pnpm/bin" \
         "$O/Library/Python/3.9/bin" "$O/Library/Python/3.10/bin" \
         "$O/.mimocode/bin" "$O/.nps" "/opt/homebrew/bin" "/usr/local/bin"; do
  if [ -e "$d/$cmd" ]; then ls -l "$d/$cmd"; found=1; fi
done
[ "$found" -eq 0 ] && echo "(none - the file does not exist anywhere obvious)"

printf '\n== manager config ==\n'
if command -v composer >/dev/null 2>&1; then
  printf 'COMPOSER_HOME=%s\n' "${COMPOSER_HOME:-unset}"
  printf 'bin-dir: %s\n' "$(composer global config bin-dir --absolute 2>/dev/null | tail -1)"
fi
command -v npm >/dev/null 2>&1 && printf 'npm prefix -g: %s\n' "$(npm prefix -g 2>/dev/null)"

printf '\n== PATH entries mentioning managers ==\n'
echo "$PATH" | tr ':' '\n' | grep -n -E 'composer|\.local/bin|cargo|npm|bun|pnpm' || echo "(none)"

printf '\n== suspicious PATH entries (glued rc line) ==\n'
echo "$PATH" | tr ':' '\n' | grep -n '#' && echo ">>> a PATH entry contains '#': an rc line was glued together, fix the newline" || echo "(clean)"

printf '\n== rc files ==\n'
for f in "$O/.zshrc" "$O/.zprofile" "$O/.zshenv" "$O/.bash_profile"; do
  [ -f "$f" ] || continue
  hits=$(grep -c '#compdef' "$f" 2>/dev/null)
  printf '%s: #compdef occurrences=%s\n' "$f" "$hits"
  grep -n '#compdef' "$f" 2>/dev/null | head -3
  grep -nE '"#|\)"#|bin#' "$f" 2>/dev/null | head -3
done

printf '\n== rc syntax ==\n'
if command -v zsh >/dev/null 2>&1; then
  if zsh -n "$O/.zshrc" 2>&1; then echo "zshrc syntax OK"; fi
fi

printf '\n== clean-env shell (what a new terminal tab gets) ==\n'
env -i HOME="$O" TERM=xterm-256color /bin/zsh -lic "which $cmd; $cmd --version" 2>&1 | tail -4
