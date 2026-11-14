---
name: ansible-vault-credentials
description: >
  Securely manage Ansible credentials using Ansible Vault + environment
  variable injection for inventory plugins. Covers the vault-to-env
  bridge pattern, inventory plugin naming requirements, and credential
  isolation so no secrets appear in YAML config files.
---

# Ansible Vault Credentials

## When to Use

- An inventory plugin (e.g. `community.vmware.vmware_vm_inventory`) needs a password or API key
- You want to avoid hardcoded credentials in inventory YAML files committed to version control
- Your project already has a `.vault_pass` file (gitignored) for vault operations
- You need a repeatable pattern that works with both CLI and Docker execution

## The Pattern: Vault → Env Var → Inventory Plugin

Most Ansible inventory plugins natively support environment variable fallback for credential fields (`set_via: env` in plugin options). The pattern is:

1. Store credentials in a vault-encrypted YAML file (e.g. `vars/vmware_credentials.yml`)
2. Create a `source`-able shell script that decrypts vault and exports env vars
3. Remove the `password` field (and optionally `hostname`/`username`) from the inventory plugin YAML config
4. `source scripts/load-vmware-vault.sh` before any ansible command

### Step 1: Encrypted Credentials File

```bash
# Create the vault file
ansible-vault create vars/vmware_credentials.yml
```

Structure:
```yaml
vmware_vcenter:
  host: "192.168.70.1"
  username: "administrator@vsphere.local"
  password: "your-password-here"
  validate_certs: false
```

### Step 2: Helper Script

Create `scripts/load-vmware-vault.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

VAULT_FILE="$PROJECT_DIR/vars/vmware_credentials.yml"
VAULT_PASS_FILE="$PROJECT_DIR/.vault_pass"

export_payload=$(ansible-vault decrypt "$VAULT_FILE" --output - \
  --vault-password-file "$VAULT_PASS_FILE" 2>/dev/null)

eval "$(echo "$export_payload" | python3 -c "
import yaml, sys, json
data = yaml.safe_load(sys.stdin)
vcenter = data.get('vmware_vcenter', {})
exports = {}
if vcenter.get('host'):          exports['VMWARE_HOST'] = vcenter['host']
if vcenter.get('username'):      exports['VMWARE_USER'] = vcenter['username']
if vcenter.get('password'):      exports['VMWARE_PASSWORD'] = vcenter['password']
if 'validate_certs' in vcenter:  exports['VMWARE_VALIDATE_CERTS'] = str(vcenter['validate_certs']).lower()
for k, v in exports.items():
    print(f'export {k}={json.dumps(v)}')
")"
```

Note: The python3 used must have `yaml` (PyYAML) installed. On Homebrew Ansible installs, use the bundled python or `python3.14`.

### Step 3: Inventory Plugin Config

Remove `password` from the inventory plugin YAML. The plugin reads `VMWARE_PASSWORD` from the environment when the config field is absent.

```yaml
# inventory/vmware/vmware_vm_inventory.yml
plugin: community.vmware.vmware_vm_inventory
strict: false
hostname: 192.168.70.1
username: administrator@vsphere.local
validate_certs: false
# password intentionally omitted — sourced from VMWARE_PASSWORD env var
```

### Step 4: Usage

```bash
cd ~/ansible
source scripts/load-vmware-vault.sh
ansible-inventory --graph
ansible-playbook playbooks/vmware/get_info.yml
```

## Inventory Plugin File Naming

The `auto` inventory plugin detects the correct plugin by file suffix. Required naming patterns:

| Plugin | Required suffix |
|---|---|
| `community.vmware.vmware_vm_inventory` | `vmware.yml`, `vmware.yaml`, `vmware_vm_inventory.yml`, `vmware_vm_inventory.yaml` |
| Most community plugins | `*.<plugin_keyword>.yml` or as documented |

If the file doesn't match, you'll get:
```
Failed to parse inventory with 'auto' plugin: ... could not be verified by inventory plugin
```

## Multiple Inventory Sources

In `ansible.cfg`, separate multiple inventory paths with commas:

```ini
[defaults]
inventory = ./inventory/hosts, ./inventory/vmware
```

## Environment Variables Supported by community.vmware Plugins

These plugins check env vars natively (no Jinja2 or lookup needed):

| Env var | Plugin field |
|---|---|
| `VMWARE_HOST`, `VMWARE_SERVER` | `hostname` |
| `VMWARE_USER`, `VMWARE_USERNAME` | `username` |
| `VMWARE_PASSWORD` | `password` |
| `VMWARE_VALIDATE_CERTS` | `validate_certs` |
| `VMWARE_PORT` | `port` |
| `VMWARE_PROXY_HOST` | `proxy_host` |
| `VMWARE_PROXY_PORT` | `proxy_port` |

## Pitfalls

- **Jinja2 in inventory plugins**: Most plugin config keys do NOT support Jinja2 substitution. However, `password` and `username` fields DO support `{{ lookup(...) }}` — but native env var is simpler and more reliable.
- **Deprecation warnings**: Set `deprecation_warnings = False` in `ansible.cfg` if you're using deprecated plugins and the warnings clutter output.
- **`ansible-vault decrypt --output -`**: Streams decrypted content to stdout, does NOT modify the original encrypted file.
- **YAML indentation in generated files**: When using `to_nice_yaml` in a playbook template, the indentation must match the YAML nesting level of the surrounding template. Use `regex_replace('(?m)^', '<N-spaces>')` where N = the column position of the parent key + 2.
- **`.vault_pass` security**: Ensure this file is in `.gitignore`. Use `chmod 600` on it.

## Related

- Built-in skill `ansible-automation` (hub-installed) — general Ansible automation workflows
- Reference: [vmware-inventory-plugin-config](references/vmware-inventory-plugin-config.md) — detailed vmware_vm_inventory config and deprecation notes
