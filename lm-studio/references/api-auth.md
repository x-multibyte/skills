# LM Studio API Authentication

## Default behavior

**By default, LM Studio does not require authentication** when started via `lms server start`. The toggle is stored in `~/.cache/lm-studio/.internal/permissions-store.json`:

```json
{
  "json": {
    "tokenMode": "disabled",  // <-- "disabled" = no auth required
    ...
  }
}
```

If you or someone toggled "Require Authentication" in the desktop GUI (Developer > Server Settings), `tokenMode` becomes `"required"` and the server rejects all API calls without a valid Bearer token.

## Creating an API token (GUI way)

1. Open LM Studio app
2. Go to **Developer** (sidebar)
3. Click **Server Settings**
4. Click **Manage Tokens**
5. Click **Create Token**, give it a name, select permissions
6. **Copy the token immediately** — shown only once

Use it as `Authorization: Bearer <token>` in API calls.

## Bypassing auth without the GUI

If you cannot access the GUI (headless/CLI-only), modify the permissions store directly:

```bash
python3 -c "
import json
PATH = f'{HOME}/.cache/lm-studio/.internal/permissions-store.json'
with open(PATH) as f: d = json.load(f)
d['json']['tokenMode'] = 'disabled'
with open(PATH, 'w') as f: json.dump(d, f, indent=2)
"
lms server stop
lms server start --port 1234
```

After the change, all API calls work without authentication.

> **Why not http-server-config.json?** The `http-server-config.json` file contains a `requireAuthentication` key, but the server overwrites this file on each restart — the toggle in `permissions-store.json` is authoritative.

## Internal key (NOT for API use)

`~/.cache/lm-studio/.internal/lms-key-2` is for `lms CLI` ↔ `server` internal communication only. Using it produces:

```
"Malformed LM Studio API token provided: <key>"
```
