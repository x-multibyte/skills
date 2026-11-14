# Complete vSphere Hardware Inventory Script

Production-ready Python script for extracting VM and ESXi host hardware configuration via vSphere API.

## Full Script Template

```python
#!/usr/bin/env python3
"""
Extract complete hardware inventory from vSphere (VMs + ESXi hosts)
Outputs: JSON data file + human-readable Markdown report
"""

import json
import ssl
import urllib3
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import atexit
from datetime import datetime

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# vCenter credentials
VCENTER_HOST = "vcenter.example.com"
VCENTER_USER = "administrator@vsphere.local"
VCENTER_PASS = "password"

def get_vm_hardware_info(vm):
    """Extract complete hardware configuration from a VM"""
    summary = vm.summary
    config = vm.config
    
    # Disk information
    disks = []
    for device in config.hardware.device:
        if isinstance(device, vim.vm.device.VirtualDisk):
            disks.append({
                "label": device.deviceInfo.label,
                "capacity_gb": round(device.capacityInKB / 1024 / 1024, 2),
                "thin_provisioned": getattr(device.backing, 'thinProvisioned', None),
                "disk_mode": device.backing.diskMode if hasattr(device.backing, 'diskMode') else None
            })
    
    # Network adapters
    network_adapters = []
    for device in config.hardware.device:
        if isinstance(device, vim.vm.device.VirtualEthernetCard):
            network_adapters.append({
                "label": device.deviceInfo.label,
                "type": type(device).__name__,
                "mac_address": device.macAddress,
                "connected": device.connectable.connected if device.connectable else None
            })
    
    return {
        "name": vm.name,
        "power_state": summary.runtime.powerState,
        "guest_os": config.guestFullName,
        "guest_id": config.guestId,
        "hardware_version": config.version,
        "cpu": {
            "num_cpus": config.hardware.numCPU,
            "cores_per_socket": config.hardware.numCoresPerSocket,
            "hot_add_enabled": config.cpuHotAddEnabled,
            "hot_remove_enabled": config.cpuHotRemoveEnabled
        },
        "memory": {
            "size_mb": config.hardware.memoryMB,
            "size_gb": round(config.hardware.memoryMB / 1024, 2),
            "hot_add_enabled": config.memoryHotAddEnabled
        },
        "disks": disks,
        "network_adapters": network_adapters,
        "firmware": config.firmware,
        "uuid": config.uuid,
        "instance_uuid": config.instanceUuid
    }

def get_host_hardware_info(host):
    """Extract ESXi host hardware configuration"""
    summary = host.summary
    hardware = summary.hardware
    config = summary.config
    
    return {
        "name": host.name,
        "model": hardware.model,
        "vendor": hardware.vendor,
        "cpu": {
            "model": hardware.cpuModel,
            "num_cpu_packages": hardware.numCpuPkgs,
            "num_cpu_cores": hardware.numCpuCores,
            "num_cpu_threads": hardware.numCpuThreads,
            "cpu_mhz": hardware.cpuMhz,
            "total_cpu_mhz": hardware.numCpuCores * hardware.cpuMhz
        },
        "memory": {
            "size_bytes": hardware.memorySize,
            "size_gb": round(hardware.memorySize / 1024 / 1024 / 1024, 2)
        },
        "connection_state": summary.runtime.connectionState,
        "power_state": summary.runtime.powerState,
        "uptime_seconds": summary.quickStats.uptime,
        "product": {
            "name": config.product.name,
            "version": config.product.version,
            "build": config.product.build,
            "full_name": config.product.fullName
        }
    }

def main():
    # Connect to vCenter
    context = ssl._create_unverified_context()
    si = SmartConnect(
        host=VCENTER_HOST,
        user=VCENTER_USER,
        pwd=VCENTER_PASS,
        sslContext=context
    )
    atexit.register(Disconnect, si)
    
    content = si.RetrieveContent()
    datacenter = content.rootFolder.childEntity[0]
    
    result = {
        "datacenter": datacenter.name,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "running_vms": [],
        "all_vms": [],
        "hosts": []
    }
    
    # Get all VMs
    vm_view = content.viewManager.CreateContainerView(
        datacenter,
        [vim.VirtualMachine],
        True
    )
    
    print(f"Processing {len(vm_view.view)} virtual machines...")
    
    for vm in vm_view.view:
        vm_info = get_vm_hardware_info(vm)
        result["all_vms"].append(vm_info)
        
        if vm.summary.runtime.powerState == "poweredOn":
            result["running_vms"].append(vm_info)
    
    vm_view.Destroy()
    
    # Get all ESXi hosts
    host_view = content.viewManager.CreateContainerView(
        datacenter,
        [vim.HostSystem],
        True
    )
    
    print(f"Processing {len(host_view.view)} ESXi hosts...")
    
    for host in host_view.view:
        host_info = get_host_hardware_info(host)
        result["hosts"].append(host_info)
    
    host_view.Destroy()
    
    # Save JSON
    output_file = "hardware_inventory.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Inventory saved to: {output_file}")
    print(f"  Total VMs: {len(result['all_vms'])}")
    print(f"  Running VMs: {len(result['running_vms'])}")
    print(f"  ESXi hosts: {len(result['hosts'])}")

if __name__ == "__main__":
    main()
```

## Markdown Report Generator

```python
#!/usr/bin/env python3
"""
Generate Markdown report from hardware inventory JSON
"""

import json
from datetime import datetime

def generate_markdown_report(json_file, output_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    md = f"""# vSphere Hardware Configuration Report

**Datacenter**: {data['datacenter']}
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total VMs**: {len(data['all_vms'])}
**Running VMs**: {len(data['running_vms'])}
**ESXi Hosts**: {len(data['hosts'])}

---

## ESXi Hosts

"""
    
    for host in data['hosts']:
        md += f"""### {host['name']}

| Item | Value |
|------|-------|
| Model | {host['vendor']} {host['model']} |
| CPU | {host['cpu']['model']} |
| Cores/Threads | {host['cpu']['num_cpu_cores']} / {host['cpu']['num_cpu_threads']} |
| Memory | {host['memory']['size_gb']} GB |
| System | {host['product']['full_name']} |
| Uptime | {host['uptime_seconds'] // 86400} days |

"""
    
    md += "\n## Running Virtual Machines\n\n"
    
    for vm in sorted(data['running_vms'], key=lambda x: x['name']):
        total_disk = sum(d['capacity_gb'] for d in vm['disks'])
        md += f"""### {vm['name']}

| Item | Value |
|------|-------|
| Power State | Running |
| Guest OS | {vm['guest_os']} |
| vCPU | {vm['cpu']['num_cpus']} ({vm['cpu']['cores_per_socket']} cores/socket) |
| Memory | {vm['memory']['size_gb']} GB |
| Disks | {len(vm['disks'])} ({total_disk:.2f} GB total) |
| Network | {len(vm['network_adapters'])} adapters |

"""
    
    # Resource statistics
    total_vcpu = sum(vm['cpu']['num_cpus'] for vm in data['running_vms'])
    total_memory = sum(vm['memory']['size_gb'] for vm in data['running_vms'])
    total_disk = sum(sum(d['capacity_gb'] for d in vm['disks']) for vm in data['running_vms'])
    
    md += f"""---

## Resource Statistics

| Resource | Running VMs |
|----------|-------------|
| vCPU | {total_vcpu} |
| Memory | {total_memory:.2f} GB |
| Disk | {total_disk:.2f} GB |
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(md)
    
    print(f"✓ Markdown report: {output_file}")

if __name__ == "__main__":
    generate_markdown_report('hardware_inventory.json', 'hardware_inventory.md')
```

## Usage

1. Install pyvmomi: `pip3 install pyvmomi`
2. Edit credentials in the script
3. Run: `python3 get_hardware_inventory.py`
4. Generate report: `python3 generate_markdown_report.py`

## Output Files

- `hardware_inventory.json` - Complete structured data
- `hardware_inventory.md` - Human-readable report with tables
