#!/usr/bin/env python3
"""
Technitium DNS Server API Client

Credentials are read in this priority order:
  1. Hermes config: `hermes config set tds.base_url <url>` / `hermes config set tds.token <token>`
  2. Environment:   TDS_BASE / TDS_TOKEN
  3. Defaults:      http://localhost:5380 / (empty)

  # Set once via Hermes config (recommended):
  hermes config set tds.base_url http://dns.example.com:5380
  hermes config set tds.token your-api-token

Actions:
  login [user] [pass]              -> get session token (prints token)
  logout                           -> invalidate session
  session                          -> get current session info
  profile                          -> get user profile

  dashboard                        -> get dashboard stats (JSON)

  zones list                       -> list authoritative zones
  zones create <name> <type>       -> create zone (Primary/Secondary/Stub/Forwarder)
  zones delete <name>              -> delete zone
  zones enable|disable <name>      -> enable/disable zone
  zones options|perm get <name>    -> get zone options/permissions
  zones sign|unsign <name>         -> sign/unsign zone with DNSSEC
  zones ds-info <name>             -> get DS info for zone
  zones dnssec-props <name>        -> get DNSSEC properties

  records get <zone> [--list-zone]  -> get records for a zone
  records add <zone> <type> ...     -> add a record (see docs for type-specific params)
  records update <zone> <type> ...  -> update a record
  records delete <zone> <type> ...  -> delete a record

  cache list [domain]              -> list cached zones
  cache flush                      -> flush entire DNS cache
  cache delete <domain>            -> delete cached zone

  allowed list                     -> list allowed zones
  allowed add <domain>             -> allow a domain
  allowed delete <domain>          -> remove from allowed
  allowed flush                    -> flush allowed zones
  allowed import <csv-domains>     -> batch import allowed zones

  blocked list                     -> list blocked zones
  blocked add <domain>             -> block a domain
  blocked delete <domain>          -> remove from blocked
  blocked flush                    -> flush blocked zones
  blocked import <csv-domains>     -> batch import blocked zones

  resolve <domain> [type=A]        -> resolve a query
                                    [--server=<ns>] [--protocol=Udp|Tcp|Tls|Https|Quic]

  settings get                     -> get all DNS settings
  settings set <key>=<value> ...   -> set DNS settings (key=value pairs)

  apps list                        -> list installed apps
  apps store                       -> list store apps
  apps install <name>              -> install app (use with --url or pipe zip)
  apps uninstall <name>            -> uninstall app
  apps config get <name>           -> get app config
  apps config set <name> <config>  -> set app config

  logs list                        -> list log files
  logs query <app> <classPath>     -> query logs
                                    [--start=..] [--end=..] [--page=1] [--per-page=10]

  admin users list                 -> list users
  admin users create <user> <pass> -> create user
  admin users delete <user>        -> delete user
  admin users details <user>       -> get user details
  admin groups list                -> list groups
  admin groups create <name>       -> create group
  admin groups delete <name>       -> delete group
  admin sessions                   -> list active sessions
  admin permissions                -> list all permissions
  admin cluster state              -> get cluster state
"""

import os
import sys
import json
import re
import urllib.request
import urllib.parse
import urllib.error


def api_url(base: str) -> str:
    return base.rstrip("/")


def request(base: str, token: str, path: str, params: dict = None, method: str = None) -> dict:
    url = f"{api_url(base)}{path}"
    if params:
        # remove None values
        params = {k: v for k, v in params.items() if v is not None}
        url += "?" + urllib.parse.urlencode(params)

    req = urllib.request.Request(url, method=method or "GET")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read().decode()
            return json.loads(data)
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"status": "error", "errorMessage": f"HTTP {e.code}: {body}"}
    except Exception as e:
        return {"status": "error", "errorMessage": str(e)}


def login_action(base: str, token: str, args: list) -> None:
    """Login and print token. token arg is used as password when it looks like one."""
    user = args[0] if len(args) > 0 else "admin"
    passwd = args[1] if len(args) > 1 else "admin"
    resp = request(base, "", "/api/user/login", {"user": user, "pass": passwd, "includeInfo": "true"})
    if resp.get("status") == "ok":
        print(resp["token"])
        print(json.dumps(resp.get("info", {}), indent=2))
    else:
        print(json.dumps(resp, indent=2), file=sys.stderr)
        sys.exit(1)


def logout_action(base: str, token: str, args: list) -> None:
    resp = request(base, token, "/api/user/logout")
    print(json.dumps(resp, indent=2))


def session_action(base: str, token: str, args: list) -> None:
    resp = request(base, token, "/api/user/session/get")
    print(json.dumps(resp, indent=2))


def profile_action(base: str, token: str, args: list) -> None:
    resp = request(base, token, "/api/user/profile/get")
    print(json.dumps(resp, indent=2))


def dashboard_action(base: str, token: str, args: list) -> None:
    resp = request(base, token, "/api/dashboard/metrics/json")
    print(json.dumps(resp, indent=2))


# --- Zones ---

def zones_list(base: str, token: str, args: list) -> None:
    resp = request(base, token, "/api/zones/list")
    print(json.dumps(resp, indent=2))


def zones_create(base: str, token: str, args: list) -> None:
    if len(args) < 2:
        print("Usage: zones create <name> <type> [options...]", file=sys.stderr)
        sys.exit(1)
    params = {"zone": args[0], "type": args[1]}
    for opt in args[2:]:
        if "=" in opt:
            k, v = opt.split("=", 1)
            params[k] = v
    resp = request(base, token, "/api/zones/create", params)
    print(json.dumps(resp, indent=2))


def zones_delete(base: str, token: str, args: list) -> None:
    if not args:
        print("Usage: zones delete <name>", file=sys.stderr)
        sys.exit(1)
    resp = request(base, token, "/api/zones/delete", {"zone": args[0]})
    print(json.dumps(resp, indent=2))


def zones_enable(base: str, token: str, args: list) -> None:
    if not args:
        print("Usage: zones enable <name>", file=sys.stderr)
        sys.exit(1)
    resp = request(base, token, "/api/zones/enable", {"zone": args[0]})
    print(json.dumps(resp, indent=2))


def zones_disable(base: str, token: str, args: list) -> None:
    if not args:
        print("Usage: zones disable <name>", file=sys.stderr)
        sys.exit(1)
    resp = request(base, token, "/api/zones/disable", {"zone": args[0]})
    print(json.dumps(resp, indent=2))


def zones_options_get(base: str, token: str, args: list) -> None:
    if not args:
        print("Usage: zones options get <name>", file=sys.stderr)
        sys.exit(1)
    resp = request(base, token, "/api/zones/options/get", {"zone": args[0]})
    print(json.dumps(resp, indent=2))


def zones_permissions_get(base: str, token: str, args: list) -> None:
    if not args:
        print("Usage: zones perm get <name>", file=sys.stderr)
        sys.exit(1)
    resp = request(base, token, "/api/zones/permissions/get", {"zone": args[0]})
    print(json.dumps(resp, indent=2))


def zones_sign(base: str, token: str, args: list) -> None:
    if not args:
        print("Usage: zones sign <name>", file=sys.stderr)
        sys.exit(1)
    resp = request(base, token, "/api/zones/sign", {"zone": args[0]})
    print(json.dumps(resp, indent=2))


def zones_unsign(base: str, token: str, args: list) -> None:
    if not args:
        print("Usage: zones unsign <name>", file=sys.stderr)
        sys.exit(1)
    resp = request(base, token, "/api/zones/unsign", {"zone": args[0]})
    print(json.dumps(resp, indent=2))


def zones_convert(base: str, token: str, args: list) -> None:
    """zones convert <name> <type>"""
    if len(args) < 2:
        print("Usage: zones convert <name> <type>", file=sys.stderr)
        print("  type: Primary, Secondary, Stub, Forwarder, SecondaryForwarder, Catalog, SecondaryCatalog", file=sys.stderr)
        sys.exit(1)
    resp = request(base, token, "/api/zones/convert", {"zone": args[0], "type": args[1]})
    print(json.dumps(resp, indent=2))


def zones_options_set(base: str, token: str, args: list) -> None:
    if not args:
        print("Usage: zones options set <name> <key=value>...", file=sys.stderr)
        sys.exit(1)
    params = {"zone": args[0]}
    for opt in args[1:]:
        if "=" in opt:
            k, v = opt.split("=", 1)
            params[k] = v
    resp = request(base, token, "/api/zones/options/set", params)
    print(json.dumps(resp, indent=2))


def zones_ds_info(base: str, token: str, args: list) -> None:
    if not args:
        print("Usage: zones ds-info <name>", file=sys.stderr)
        sys.exit(1)
    resp = request(base, token, "/api/zones/dsInfo", {"zone": args[0]})
    print(json.dumps(resp, indent=2))


def zones_dnssec_props(base: str, token: str, args: list) -> None:
    if not args:
        print("Usage: zones dnssec-props <name>", file=sys.stderr)
        sys.exit(1)
    resp = request(base, token, "/api/zones/dnssec/properties", {"zone": args[0]})
    print(json.dumps(resp, indent=2))


# --- Records ---

def records_get(base: str, token: str, args: list) -> None:
    """records get <zone> [--list-zone] [--node=...]"""
    if not args:
        print("Usage: records get <zone> [--list-zone] [--domain=<sub>]", file=sys.stderr)
        sys.exit(1)
    params = {"domain": args[0], "listZone": "false"}
    for opt in args[1:]:
        if opt == "--list-zone":
            params["listZone"] = "true"
        elif opt.startswith("--domain="):
            params["domain"] = opt.split("=", 1)[1]
    resp = request(base, token, "/api/zones/records/get", params)
    print(json.dumps(resp, indent=2))


def records_add(base: str, token: str, args: list) -> None:
    """records add <zone> <type> <key=value> ..."""
    if len(args) < 2:
        print("Usage: records add <zone> <type> <key=value>...", file=sys.stderr)
        sys.exit(1)
    params = {"domain": args[0], "type": args[1]}
    for opt in args[2:]:
        if "=" in opt:
            k, v = opt.split("=", 1)
            params[k] = v
    resp = request(base, token, "/api/zones/records/add", params)
    print(json.dumps(resp, indent=2))


def records_update(base: str, token: str, args: list) -> None:
    if len(args) < 2:
        print("Usage: records update <zone> <type> <key=value>...", file=sys.stderr)
        sys.exit(1)
    params = {"domain": args[0], "type": args[1]}
    for opt in args[2:]:
        if "=" in opt:
            k, v = opt.split("=", 1)
            params[k] = v
    resp = request(base, token, "/api/zones/records/update", params)
    print(json.dumps(resp, indent=2))


def records_delete(base: str, token: str, args: list) -> None:
    if len(args) < 2:
        print("Usage: records delete <zone> <type> <key=value>...", file=sys.stderr)
        sys.exit(1)
    params = {"domain": args[0], "type": args[1]}
    for opt in args[2:]:
        if "=" in opt:
            k, v = opt.split("=", 1)
            params[k] = v
    resp = request(base, token, "/api/zones/records/delete", params)
    print(json.dumps(resp, indent=2))


# --- Cache ---

def cache_list(base: str, token: str, args: list) -> None:
    domain = args[0] if args else ""
    resp = request(base, token, "/api/cache/list", {"domain": domain})
    print(json.dumps(resp, indent=2))


def cache_flush(base: str, token: str, args: list) -> None:
    resp = request(base, token, "/api/cache/flush")
    print(json.dumps(resp, indent=2))


def cache_delete(base: str, token: str, args: list) -> None:
    if not args:
        print("Usage: cache delete <domain>", file=sys.stderr)
        sys.exit(1)
    resp = request(base, token, "/api/cache/delete", {"domain": args[0]})
    print(json.dumps(resp, indent=2))


# --- Allowed ---

def allowed_list(base: str, token: str, args: list) -> None:
    domain = args[0] if args else ""
    resp = request(base, token, "/api/allowed/list", {"domain": domain})
    print(json.dumps(resp, indent=2))


def allowed_add(base: str, token: str, args: list) -> None:
    if not args:
        print("Usage: allowed add <domain>", file=sys.stderr)
        sys.exit(1)
    resp = request(base, token, "/api/allowed/add", {"domain": args[0]})
    print(json.dumps(resp, indent=2))


def allowed_delete(base: str, token: str, args: list) -> None:
    if not args:
        print("Usage: allowed delete <domain>", file=sys.stderr)
        sys.exit(1)
    resp = request(base, token, "/api/allowed/delete", {"domain": args[0]})
    print(json.dumps(resp, indent=2))


def allowed_flush(base: str, token: str, args: list) -> None:
    resp = request(base, token, "/api/allowed/flush")
    print(json.dumps(resp, indent=2))


def allowed_import(base: str, token: str, args: list) -> None:
    if not args:
        print("Usage: allowed import <comma-separated-domains>", file=sys.stderr)
        sys.exit(1)
    resp = request(base, token, "/api/allowed/import", {"allowedZones": args[0]})
    print(json.dumps(resp, indent=2))


# --- Blocked ---

def blocked_list(base: str, token: str, args: list) -> None:
    domain = args[0] if args else ""
    resp = request(base, token, "/api/blocked/list", {"domain": domain})
    print(json.dumps(resp, indent=2))


def blocked_add(base: str, token: str, args: list) -> None:
    if not args:
        print("Usage: blocked add <domain>", file=sys.stderr)
        sys.exit(1)
    resp = request(base, token, "/api/blocked/add", {"domain": args[0]})
    print(json.dumps(resp, indent=2))


def blocked_delete(base: str, token: str, args: list) -> None:
    if not args:
        print("Usage: blocked delete <domain>", file=sys.stderr)
        sys.exit(1)
    resp = request(base, token, "/api/blocked/delete", {"domain": args[0]})
    print(json.dumps(resp, indent=2))


def blocked_flush(base: str, token: str, args: list) -> None:
    resp = request(base, token, "/api/blocked/flush")
    print(json.dumps(resp, indent=2))


def blocked_import(base: str, token: str, args: list) -> None:
    if not args:
        print("Usage: blocked import <comma-separated-domains>", file=sys.stderr)
        sys.exit(1)
    resp = request(base, token, "/api/blocked/import", {"blockedZones": args[0]})
    print(json.dumps(resp, indent=2))


# --- Resolve ---

def resolve_action(base: str, token: str, args: list) -> None:
    """resolve <domain> [type=A] [--server=this-server] [--protocol=Udp]"""
    if not args:
        print("Usage: resolve <domain> [type] [--server=...] [--protocol=...]", file=sys.stderr)
        sys.exit(1)
    params = {"domain": args[0], "type": args[1] if len(args) > 1 and not args[1].startswith("--") else "A"}
    for opt in args[1:]:
        if opt.startswith("--"):
            if "=" in opt:
                k, v = opt.lstrip("--").split("=", 1)
                params[k] = v
    resp = request(base, token, "/api/dnsClient/resolve", params)
    print(json.dumps(resp, indent=2))


# --- Settings ---

def settings_get(base: str, token: str, args: list) -> None:
    resp = request(base, token, "/api/settings/get")
    print(json.dumps(resp, indent=2))


def settings_set(base: str, token: str, args: list) -> None:
    if not args:
        print("Usage: settings set <key>=<value> ...", file=sys.stderr)
        sys.exit(1)
    params = {}
    for opt in args:
        if "=" in opt:
            k, v = opt.split("=", 1)
            params[k] = v
    resp = request(base, token, "/api/settings/set", params)
    print(json.dumps(resp, indent=2))


# --- Apps ---

def apps_list(base: str, token: str, args: list) -> None:
    resp = request(base, token, "/api/apps/list")
    print(json.dumps(resp, indent=2))


def apps_store(base: str, token: str, args: list) -> None:
    resp = request(base, token, "/api/apps/listStoreApps")
    print(json.dumps(resp, indent=2))


def apps_install(base: str, token: str, args: list) -> None:
    if not args:
        print("Usage: apps install <name> [--url=<download_url>]", file=sys.stderr)
        sys.exit(1)
    name = args[0]
    url_opt = next((a.split("=", 1)[1] for a in args[1:] if a.startswith("--url=")), None)
    if url_opt:
        resp = request(base, token, "/api/apps/downloadAndInstall", {"name": name, "url": url_opt})
    else:
        resp = request(base, token, "/api/apps/install", {"name": name})
    print(json.dumps(resp, indent=2))


def apps_uninstall(base: str, token: str, args: list) -> None:
    if not args:
        print("Usage: apps uninstall <name>", file=sys.stderr)
        sys.exit(1)
    resp = request(base, token, "/api/apps/uninstall", {"name": args[0]})
    print(json.dumps(resp, indent=2))


def apps_config_get(base: str, token: str, args: list) -> None:
    if not args:
        print("Usage: apps config get <name>", file=sys.stderr)
        sys.exit(1)
    resp = request(base, token, "/api/apps/config/get", {"name": args[0]})
    print(json.dumps(resp, indent=2))


def apps_config_set(base: str, token: str, args: list) -> None:
    if len(args) < 2:
        print("Usage: apps config set <name> <config-data>", file=sys.stderr)
        sys.exit(1)
    resp = request(base, token, "/api/apps/config/set", {"name": args[0], "config": args[1]})
    print(json.dumps(resp, indent=2))


# --- Logs ---

def logs_list(base: str, token: str, args: list) -> None:
    resp = request(base, token, "/api/logs/list")
    print(json.dumps(resp, indent=2))


def logs_query(base: str, token: str, args: list) -> None:
    if len(args) < 2:
        print("Usage: logs query <app> <classPath> [--page=1] [--per-page=10] [--start=...] [--end=...]",
              file=sys.stderr)
        sys.exit(1)
    params = {"name": args[0], "classPath": args[1]}
    for opt in args[2:]:
        if opt.startswith("--"):
            if "=" in opt:
                k, v = opt.lstrip("--").replace("-", "", 1).replace("-", "").replace("-", "")
                # Normalize: --page -> pageNumber, --per-page -> entriesPerPage
                if k == "page":
                    k = "pageNumber"
                elif k == "per-page" or k == "perPage":
                    k = "entriesPerPage"
                elif k == "start":
                    k = "start"
                elif k == "end":
                    k = "end"
                params[k] = v
    resp = request(base, token, "/api/logs/query", params)
    print(json.dumps(resp, indent=2))


# --- Admin ---

def admin_users_list(base: str, token: str, args: list) -> None:
    resp = request(base, token, "/api/admin/users/list")
    print(json.dumps(resp, indent=2))


def admin_users_create(base: str, token: str, args: list) -> None:
    if len(args) < 2:
        print("Usage: admin users create <username> <password> [groups=...]", file=sys.stderr)
        sys.exit(1)
    params = {"user": args[0], "password": args[1]}
    for opt in args[2:]:
        if "=" in opt:
            k, v = opt.split("=", 1)
            params[k] = v
    resp = request(base, token, "/api/admin/users/create", params)
    print(json.dumps(resp, indent=2))


def admin_users_delete(base: str, token: str, args: list) -> None:
    if not args:
        print("Usage: admin users delete <username>", file=sys.stderr)
        sys.exit(1)
    resp = request(base, token, "/api/admin/users/delete", {"user": args[0]})
    print(json.dumps(resp, indent=2))


def admin_users_details(base: str, token: str, args: list) -> None:
    if not args:
        print("Usage: admin users details <username>", file=sys.stderr)
        sys.exit(1)
    resp = request(base, token, "/api/admin/users/get", {"user": args[0]})
    print(json.dumps(resp, indent=2))


def admin_groups_list(base: str, token: str, args: list) -> None:
    resp = request(base, token, "/api/admin/groups/list")
    print(json.dumps(resp, indent=2))


def admin_groups_create(base: str, token: str, args: list) -> None:
    if not args:
        print("Usage: admin groups create <name>", file=sys.stderr)
        sys.exit(1)
    resp = request(base, token, "/api/admin/groups/create", {"group": args[0]})
    print(json.dumps(resp, indent=2))


def admin_groups_delete(base: str, token: str, args: list) -> None:
    if not args:
        print("Usage: admin groups delete <name>", file=sys.stderr)
        sys.exit(1)
    resp = request(base, token, "/api/admin/groups/delete", {"group": args[0]})
    print(json.dumps(resp, indent=2))


def admin_sessions(base: str, token: str, args: list) -> None:
    resp = request(base, token, "/api/admin/sessions/list")
    print(json.dumps(resp, indent=2))


def admin_permissions(base: str, token: str, args: list) -> None:
    resp = request(base, token, "/api/admin/permissions/list")
    print(json.dumps(resp, indent=2))


def admin_cluster_state(base: str, token: str, args: list) -> None:
    resp = request(base, token, "/api/admin/cluster/get")
    print(json.dumps(resp, indent=2))


# --- Main dispatch ---

COMMANDS = {
    "login": login_action,
    "logout": logout_action,
    "session": session_action,
    "profile": profile_action,
    "dashboard": dashboard_action,
    "zones": {
        "list": zones_list,
        "create": zones_create,
        "delete": zones_delete,
        "enable": zones_enable,
        "disable": zones_disable,
        "convert": zones_convert,
        "options": {"get": zones_options_get, "set": zones_options_set},
        "perm": {"get": zones_permissions_get},
        "sign": zones_sign,
        "unsign": zones_unsign,
        "convert": zones_convert,
        "ds-info": zones_ds_info,
        "dnssec-props": zones_dnssec_props,
    },
    "records": {
        "get": records_get,
        "add": records_add,
        "update": records_update,
        "delete": records_delete,
    },
    "cache": {
        "list": cache_list,
        "flush": cache_flush,
        "delete": cache_delete,
    },
    "allowed": {
        "list": allowed_list,
        "add": allowed_add,
        "delete": allowed_delete,
        "flush": allowed_flush,
        "import": allowed_import,
    },
    "blocked": {
        "list": blocked_list,
        "add": blocked_add,
        "delete": blocked_delete,
        "flush": blocked_flush,
        "import": blocked_import,
    },
    "resolve": resolve_action,
    "settings": {
        "get": settings_get,
        "set": settings_set,
    },
    "apps": {
        "list": apps_list,
        "store": apps_store,
        "install": apps_install,
        "uninstall": apps_uninstall,
        "config": {
            "get": apps_config_get,
            "set": apps_config_set,
        },
    },
    "logs": {
        "list": logs_list,
        "query": logs_query,
    },
    "admin": {
        "users": {
            "list": admin_users_list,
            "create": admin_users_create,
            "delete": admin_users_delete,
            "details": admin_users_details,
        },
        "groups": {
            "list": admin_groups_list,
            "create": admin_groups_create,
            "delete": admin_groups_delete,
        },
        "sessions": admin_sessions,
        "permissions": admin_permissions,
        "cluster": {"state": admin_cluster_state},
    },
}


def resolve_cmd(tree, args):
    """Walk the command tree with args, returning (handler, remaining_args)."""
    if isinstance(tree, dict):
        if not args:
            print("Available subcommands: " + ", ".join(sorted(tree.keys())), file=sys.stderr)
            sys.exit(1)
        sub = args[0]
        if sub in tree:
            return resolve_cmd(tree[sub], args[1:])
        else:
            print(f"Unknown subcommand: {sub}", file=sys.stderr)
            print("Available: " + ", ".join(sorted(tree.keys())), file=sys.stderr)
            sys.exit(1)
    elif callable(tree):
        return tree, args
    else:
        print("Invalid command tree", file=sys.stderr)
        sys.exit(1)


def _hermes_config_path() -> str | None:
    """Find the Hermes config.yaml, respecting HERMES_HOME."""
    home = os.environ.get("HERMES_HOME") or os.path.join(os.path.expanduser("~"), ".hermes")
    path = os.path.join(home, "config.yaml")
    return path if os.path.isfile(path) else None


def _read_hermes_config() -> dict:
    """Read ~/.hermes/config.yaml and return as a flat dotted-key dict.

    Only supports top-level sections and one level of nesting, which is
    enough for 'tds.base_url' and 'tds.token'.  No YAML dependency needed.
    """
    path = _hermes_config_path()
    if not path:
        return {}
    result = {}
    # Cheap prefix-based parser — no PyYAML needed.
    # Matches top-level keys and one level of indented sub-keys.
    current_section = None
    try:
        with open(path) as f:
            for line in f:
                stripped = line.rstrip()
                if not stripped or stripped.startswith("#"):
                    continue
                # Non-indented line → section header
                if not stripped[0].isspace():
                    if ":" in stripped and not stripped.lstrip().startswith("-"):
                        key = stripped.split(":", 1)[0].strip()
                        if key and " " not in key:
                            current_section = key
                    else:
                        current_section = None
                # Indented line → key: value under current section
                elif current_section and stripped[0].isspace():
                    m = re.match(r"^\s+([\w.-]+)\s*:\s*(.*)", stripped)
                    if m:
                        full_key = f"{current_section}.{m.group(1)}"
                        val = m.group(2).strip().strip("\"'")
                        result[full_key] = val
    except OSError:
        pass
    return result


def main():
    hermes_cfg = _read_hermes_config()

    # Priority: Hermes config > env var > default
    base = (
        hermes_cfg.get("tds.base_url")
        or os.environ.get("TDS_BASE")
        or "http://localhost:5380"
    )
    token = (
        hermes_cfg.get("tds.token")
        or os.environ.get("TDS_TOKEN")
        or ""
    )

    if len(sys.argv) < 2:
        print("Usage: api_client.py <action> [args...]", file=sys.stderr)
        print(file=sys.stderr)
        print(f"  TDS base URL: {base}", file=sys.stderr)
        print(f"  Token set:    {'yes' if token else 'no'}", file=sys.stderr)
        print(file=sys.stderr)
        print("  Configure via Hermes (recommended):", file=sys.stderr)
        print("    hermes config set tds.base_url <url>", file=sys.stderr)
        print("    hermes config set tds.token <token>", file=sys.stderr)
        print(file=sys.stderr)
        print("  Or via environment:", file=sys.stderr)
        print("    export TDS_BASE=<url>", file=sys.stderr)
        print("    export TDS_TOKEN=<token>", file=sys.stderr)
        sys.exit(1)

    # Special case: login doesn't need a token
    if sys.argv[1] == "login":
        login_action(base, token, sys.argv[2:])
        return

    if not token:
        print("Error: No API token found.", file=sys.stderr)
        print(file=sys.stderr)
        print("  Set via Hermes config:", file=sys.stderr)
        print("    hermes config set tds.token <token>", file=sys.stderr)
        print(file=sys.stderr)
        print("  Or login interactively:", file=sys.stderr)
        print("    api_client.py login <user> <pass>", file=sys.stderr)
        sys.exit(1)

    handler, remaining = resolve_cmd(COMMANDS, sys.argv[1:])
    handler(base, token, remaining)


if __name__ == "__main__":
    main()
