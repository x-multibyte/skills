---
name: vmware-vsphere-operations
description: Query vSphere VM/host hardware, automate with Terraform.
---

# VMware vSphere Operations

## When to Use

- Query hardware configuration of VMs and ESXi hosts
- Generate infrastructure inventory reports
- Automate VM provisioning with Terraform
- Extract detailed VM specs (CPU, memory, disks, network adapters)
- Audit resource allocation across the datacenter

## Hardware Inventory Extraction

### Preferred Method: Python + pyvmomi

Use Python with the pyVim/pyvmomi library for reliable hardware queries. This method handles VMs with special characters in names and provides granular details that Terraform data sources cannot reach.

**Install dependency:**
```bash
pip3 install pyvmomi
```

**Core pattern:**
```python
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl

# Disable SSL verification for self-signed certs
context = ssl._create_unverified_context()
si = SmartConnect(
    host="vcenter.example.com",
    user="administrator@vsphere.local",
    pwd="password",
    sslContext=context
)

content = si.RetrieveContent()
datacenter = content.rootFolder.childEntity[0]

# Get all VMs
vm_view = content.viewManager.CreateContainerView(
    datacenter,
    [vim.VirtualMachine],
    True
)

for vm in vm_view.view:
    config = vm.config
    summary = vm.summary
    
    # Extract hardware details
    hw_info = {
        "name": vm.name,
        "power_state": summary.runtime.powerState,
        "cpu": config.hardware.numCPU,
        "memory_mb": config.hardware.memoryMB,
        "guest_os": config.guestFullName
    }
    
    # Disk details
    for device in config.hardware.device:
        if isinstance(device, vim.vm.device.VirtualDisk):
            disk_info = {
                "label": device.deviceInfo.label,
                "capacity_gb": device.capacityInKB / 1024 / 1024,
                "thin_provisioned": device.backing.thinProvisioned
            }
    
    # Network adapters
    for device in config.hardware.device:
        if isinstance(device, vim.vm.device.VirtualEthernetCard):
            net_info = {
                "label": device.deviceInfo.label,
                "mac": device.macAddress,
                "type": type(device).__name__
            }

vm_view.Destroy()
Disconnect(si)
```

**ESXi host hardware:**
```python
host_view = content.viewManager.CreateContainerView(
    datacenter,
    [vim.HostSystem],
    True
)

for host in host_view.view:
    hw = host.summary.hardware
    host_info = {
        "name": host.name,
        "model": hw.model,
        "cpu_cores": hw.numCpuCores,
        "cpu_threads": hw.numCpuThreads,
        "cpu_mhz": hw.cpuMhz,
        "memory_gb": hw.memorySize / 1024 / 1024 / 1024
    }
```

### Output Format

Generate both JSON (for automation) and Markdown (for humans):

- **JSON**: Complete structured data with all fields
- **Markdown**: Tables with VM name, CPU, memory, disk, power state
- **Include**: Resource statistics (total vCPU, memory, disk allocated)

## Terraform for VM Provisioning

Use Terraform for infrastructure-as-code VM deployment, not for querying existing VMs with special characters in names.

**Provider setup:**
```hcl
provider "vsphere" {
  user                 = var.vsphere_user
  password             = var.vsphere_password
  vsphere_server       = var.vsphere_server
  allow_unverified_ssl = true
}
```

**Data sources for resource discovery:**
```hcl
data "vsphere_datacenter" "dc" {
  name = "Datacenter"
}

data "vsphere_datastore" "datastore" {
  name          = "datastore1"
  datacenter_id = data.vsphere_datacenter.dc.id
}

data "vsphere_network" "network" {
  name          = "VM Network"
  datacenter_id = data.vsphere_datacenter.dc.id
}

data "vsphere_resource_pool" "pool" {
  name          = "Resources"
  datacenter_id = data.vsphere_datacenter.dc.id
}
```

## Pitfalls

**Terraform data sources fail on VMs with special characters.** VM names containing dots, hyphens with numbers, or Unicode will cause `vm 'name' not found` errors even when the VM exists. Use Python + pyvmomi for inventory queries; reserve Terraform for provisioning only.

**Always use ContainerView, never iterate rootFolder directly.** Direct iteration misses nested folders and is slow. `CreateContainerView(datacenter, [vim.VirtualMachine], True)` with recursive=True finds all VMs regardless of folder structure.

**Disconnect the session.** Call `Disconnect(si)` or register it with `atexit.register(Disconnect, si)` — orphaned sessions accumulate and can exhaust vCenter's connection pool.

**Filter VMs by power state before querying details.** Check `summary.runtime.powerState == 'poweredOn'` before extracting hardware — saves API calls and time when you only need running VMs.

**ESXi single-host has no cluster.** When connecting directly to ESXi (not vCenter), the `cluster` field must be empty string. Terraform data source `vsphere_compute_cluster` will fail; use `vsphere_resource_pool` with name `"Resources"` instead.

**Disk thin_provisioned is on the backing, not the device.** Access `device.backing.thinProvisioned`, not `device.thinProvisioned`. The latter does not exist and will raise AttributeError.

## Report Content Principle

**When the task is information collection, the report must be pure data — no recommendations, no "next steps", no storage proposals.** This user uses vSphere inventory reports as an input to planning, not as a request for advice. Present facts only:

- Host hardware specs (CPU model/cores/threads/frequency, RAM, ESXi version, uptime)
- Datastore capacity (total / used / free / utilization %)
- VM summary table (running/stopped counts, vCPU, RAM, disk)
- Per-VM detail tables (guest OS, hardware version, vCPU, memory, each disk with size and thin/thick, each NIC with type and MAC)
- Stopped VM summary table
- Resource overcommit ratios (vCPU, RAM, disk allocated vs physical)
- Disk allocation breakdown per VM
- Network config overview (NIC count, adapter type, MAC addresses)

Do not append storage sizing recommendations, migration complexity ratings, or architectural opinions unless the user explicitly asks for them.

## Verification

After generating inventory:

1. Validate JSON with `jq empty <file>` — catches malformed output
2. Count running VMs in JSON and compare to vCenter UI
3. Sum vCPU/memory and verify against known resource allocation
4. Spot-check 2-3 VM entries for accuracy (CPU count, disk size)

## Reference

See `references/pyvmomi-complete-script.md` for a production-ready script template.
