---
name: php-dev-env
description: "Troubleshoot PHP development environment issues on macOS (Homebrew PHP, Xdebug, Composer, Laravel). Covers config, CLI quirks, and false-positive diagnostics."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [php, xdebug, laravel, homebrew, debugging, development-environment]
    related_skills: [systematic-debugging]
---

# PHP Development Environment Troubleshooting

## Overview

macOS Homebrew PHP setups have a set of predictable failure modes. This skill captures common environment debugging patterns.

## Xdebug

### "Xdebug has detected a possible infinite loop" — False Positive During Laravel Seeding

**Symptom:** Running `php artisan migrate:fresh --seed` (or any heavy factory + ORM workflow) fails with:

```
Xdebug has detected a possible infinite loop, and aborted your script
with a stack depth of '512' frames

at vendor/laravel/framework/src/Illuminate/Database/Grammar.php:256
```

**Root cause:** Xdebug's default `max_nesting_level=512` is too low. Laravel factory `afterCreating` callbacks + ORM query compilation (`wrapSegments`, `Collection::map` closures, `Grammar::getValue` recursion) create legitimate nesting well above 512 frames. The error at `Grammar.php:256` (`isExpression()`) is **not** an infinite loop — it's the deepest observable frame in a deep but terminating call chain.

**Fix:** Increase `xdebug.max_nesting_level` in the PHP ini config.

```ini
; /opt/homebrew/etc/php/8.4/conf.d/99-xdebug.ini
zend_extension = xdebug
xdebug.max_nesting_level = 2048
```

**Verification:**
```bash
php -r 'echo ini_get("xdebug.max_nesting_level");'
```

Run the seeding command again without special flags to confirm.

**Pitfalls:**
- Do NOT set this to `-1` (unlimited) — that disables Xdebug's infinite loop protection entirely. `2048` is a safe ceiling.
- If the error persists at `2048`, double the value once more. If it still triggers at `4096+`, you likely have an actual infinite loop and should profile the stack with `xdebug_start_trace()`.
- This only affects `cli` mode with Xdebug enabled. The `develop` Xdebug mode (common on Homebrew PHP) always loads the nesting check.
- Running with `php -d xdebug.max_nesting_level=-1` is a quick bypass for a single command but skips the protection entirely.

## Composer

*(Future additions)*

## Laravel CLI

*(Future additions)*
