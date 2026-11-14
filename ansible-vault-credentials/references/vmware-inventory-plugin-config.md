# VMware Inventory Plugin Configuration

## Plugin Deprecation

`community.vmware.vmware_vm_inventory` is deprecated as of Ansible 13 / community.vmware 6.x.
Will be removed in community.vmware 7.0.0.

**Migration target:** `vmware.vmware.vms` (in the new `vmware.vmware` collection)

## Required Naming

The auto plugin detects `community.vmware.vmware_vm_inventory` only for files ending with:
- `vmware.yml`
- `vmware.yaml`
- `vmware_vm_inventory.yml`
- `vmware_vm_inventory.yaml`

A file named `vcenter.yml` will NOT be detected by the auto plugin.

## Env Var Support (Native)

The plugin reads these env vars as fallback when the corresponding YAML key is absent:

| Env var | YAML key |
|---|---|
| `VMWARE_HOST` / `VMWARE_SERVER` | `hostname` |
| `VMWARE_USER` / `VMWARE_USERNAME` | `username` |
| `VMWARE_PASSWORD` | `password` |
| `VMWARE_VALIDATE_CERTS` | `validate_certs` |
| `VMWARE_PORT` | `port` |
| `VMWARE_PROXY_HOST` | `proxy_host` |
| `VMWARE_PROXY_PORT` | `proxy_port` |

## Jinja2 Support in Config

The `password` and `username` fields support Jinja2 templating and vault-encrypted values:

```yaml
password: '{{ (lookup("file","~/.config/vmware.yaml") | from_yaml).password }}'
```

But native env var is simpler: just omit the field entirely.

## Full Working Example

```yaml
# inventory/vmware/vmware_vm_inventory.yml
plugin: community.vmware.vmware_vm_inventory
strict: false
hostname_pattern: '.*'
hostnames:
  - name
properties:
  - name
  - guest.ipAddress
  - guest.hostName
  - summary.runtime.powerState
filters:
  - summary.runtime.powerState = "poweredOn"
keyed_groups:
  - key: 'config.guestId'
    prefix: 'guest'
  - key: 'summary.runtime.powerState'
    prefix: 'power_state'
hostname: 192.168.70.1
username: administrator@vsphere.local
validate_certs: false
```

## Fix: Auto-Generated Inventory YAML Indentation

When using `to_nice_yaml` inside a playbook template to generate inventory files,
the `regex_replace` indent must match the YAML nesting level of the parent key.

**Wrong** (produces hosts at wrong nesting level):
```yaml
          {{ vm_hosts | to_nice_yaml | regex_replace('(?m)^', '  ') }}
```

**Correct** (matches 18-space indent under `hosts:` at column 16):
```yaml
                hosts:
          {{ vm_hosts | to_nice_yaml | regex_replace('(?m)^', '                  ') }}
```

The indent count = column position of `hosts:` + 2.
