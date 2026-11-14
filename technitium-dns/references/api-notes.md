# Technitium DNS API Notes (from real usage)

## `domain` parameter semantics

The API parameter `domain` in `/api/zones/records/add`, `update`, `delete` is the
**record's FQDN** (e.g. `app01.local`, `dsm.home.lan`, `example.com`), NOT just the
zone name.

The `api_client.py` script maps the _first positional argument_ to this `domain`
parameter.  Any subsequent `key=value` argument with key `domain` will **overwrite**
the first positional arg, which likely breaks the call — the server treats the
overwritten value as the record's FQDN and tries to auto-find a zone for it.

### Correct patterns

```bash
# zone-apex record — FQDN == zone name
python3 api_client.py records add example.com A ipAddress=1.2.3.4

# subdomain record — use full FQDN as first arg
python3 api_client.py records add sub.example.com A ipAddress=1.2.3.4

# explicit zone (avoids auto-detection, useful at zone boundaries)
python3 api_client.py records add sub.example.com A ipAddress=1.2.3.4 zone=example.com
```

### Wrong patterns (DO NOT use)

```bash
# WRONG — 'domain=app01' overwrites the zone 'local', server looks for zone 'app01'
python3 api_client.py records add local A domain=app01 ipAddress=192.168.69.1

# WRONG — same bug, 'domain=dsm' overwrites 'home.lan'
python3 api_client.py records add home.lan A domain=dsm ipAddress=192.168.1.10
```

## Observed record structure

From a working `local` zone (Primary):

| name | type | rData |
|------|------|-------|
| `local` | NS | nameServer: "dns01" |
| `local` | SOA | ... |
| `dev01.local` | A | 192.168.69.101 |
| `dns01.local` | A | 192.168.71.11 |
| `app01.local` | A | 192.168.69.1 |

Record `name` in the JSON response always shows the **full FQDN**, even for
zone-apex records (where it equals the zone name).
