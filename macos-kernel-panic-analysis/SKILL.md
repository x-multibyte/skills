---
name: macos-kernel-panic-analysis
description: Analyze Apple Silicon (M1-M4) macOS kernel panic logs
domain: apple/macos
trigger: User shares a kernel panic log or asks why their Mac crashed on Apple Silicon
steps:
  - id: read-panic
    description: Scan panic header, faulting task, and kext backtrace for the crash source. DCP panics show 'DCP PANIC - ASSERT!' with dcpav as faulting task 27.
  - id: classify
    description: Map to known panic family. DCP display panics have AppleDCPDPTXPowerController and RTBuddy in stack. GPU panics show AGXKextClient. PMU panics mention power management. NVMe panics mention ANS2.
  - id: check-software
    description: Look for BetterDisplay (most common trigger), DisplayLink drivers, or display managers. Check mdfind, /Applications, brew list --cask, systemextensionsctl list. Leftover config after uninstall can persist.
  - id: check-displays
    description: External monitors and USB-C to HDMI adapters are the #1 DCP trigger. USB-C to DP is more reliable. Ask about cable type, monitor setup, and whether disconnecting all externals stops the panic.
  - id: recommend
    description: Apply workarounds in order. 1) System Settings > Battery > prevent sleep when display off. 2) Shutdown + 30s wait (SMC reset equivalent). 3) Safe Boot to isolate third-party software. 4) Update macOS. 5) Try different cable (USB-C to DP instead of HDMI). 6) If BetterDisplay, disable virtual screens or uninstall.
  - id: collect
    description: Gather panic logs from ~/Library/Logs/DiagnosticReports/. grep for DCP pattern to find all occurrences. Include full log, macOS version, hardware model, and display setup for Apple feedback.
pitfalls:
  - Do not blame hardware unless the panic reproduces with no external monitors, no BetterDisplay, and across multiple macOS versions. DCP panics are overwhelmingly firmware/software bugs.
  - Apple Silicon has no SMC reset like Intel Macs; shutdown + 30s wait is the closest equivalent.
  - Sleep Count in panic logs is total since factory reset, not per-session.
  - No mapping found for coredump section lines in DCP panics are normal coprocessor memory artifacts; ignore them.
references:
  - references/dcp-panic-detailed.md
---

# macOS Kernel Panic Analysis (Apple Silicon)

## When to use this skill

A user shares a kernel panic log from an Apple Silicon Mac (M1-M4) or reports random reboots/crashes. This skill guides the analysis of the panic log, identification of the crash family, triage of likely causes, and recommendation of workarounds.

## Reading a panic log

The key sections in an Apple Silicon panic log:

### Panic header
```
panic(cpu 3 caller 0xfffffe003f17d53c): DCP PANIC - ASSERT!AppleDCPDPTXPowerController.cpp:603
```
This tells you the crash source (DCP), the exact source file and line, and which CPU core panicked.

### Faulting task
```
27 dcpav | 015 | 1072/16368 | RUNNABLE | 0 | [Faulting task]
```
RTKit task 27 (dcpav = Display Co-Processor Audio/Video) is the most common faulting task for display-related panics.

### Kernel extension backtrace
```
com.apple.driver.IOSlaveProcessor
com.apple.driver.RTBuddy
```
DCP panics always route through these two kexts.

### Sleep/Wake counts
```
Sleep Count: 1004474
Wake Count: 487515
```
Very high counts are normal on Macs that rarely reboot. Not actionable by themselves.

## Common Apple Silicon panic families

| Family | Signature | Faulting task | Common causes |
|--------|-----------|---------------|---------------|
| DCP (Display) | `DCP PANIC - ASSERT!` `AppleDCPDPTXPowerController` | dcpav (task 27) | BetterDisplay, external monitors, USB-C adapters, sleep/wake |
| GPU | `AGX` `GPU` `IOService:` | kernel_task | Graphics driver bugs, bad external monitor EDID |
| PMU/Power | `PMU` `Sleep/Wake` | kernel_task | Power management firmware bugs |
| Storage | `ANS2` `NVMe` | kernel_task | Storage controller firmware, disk sleep |

## Triage workflow

1. Read the header and classify the panic family.
2. Check if the user has BetterDisplay installed (most common DCP trigger).
3. Check if external monitors were connected at time of crash.
4. Ask about cable type — USB-C to HDMI is the most problematic.
5. Recommend workarounds starting from least invasive.
6. Collect logs if the user needs to file Apple Feedback.

## Key workarounds summary

- **Prevent sleep when display off**: Settings > Battery > check the box
- **Shutdown + 30s wait**: Apple Silicon SMC/NVRAM equivalent
- **Safe Boot**: Hold Shift at startup to isolate third-party software
- **Cable swap**: USB-C to DP instead of USB-C to HDMI
- **BetterDisplay**: Disable virtual screens or uninstall completely
