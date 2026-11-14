# DCP (Display Co-Processor) Panic — Detailed Reference

## Full panic signature

```
panic(cpu N caller 0x...): DCP PANIC - ASSERT!AppleDCPDPTXPowerController.cpp:603
  No device added after powering on the rails. HPD=0 - dcpav(27)
```

Older macOS versions use line 538 instead of 603; same root cause.

## What happens

The DCP (Display Co-Processor) is a separate RTKit-based coprocessor on Apple
Silicon that handles all display output. Its DPTX (DisplayPort TX) power
controller executes a power-on sequence for the display interface:

1. Power rails are turned on
2. Firmware waits for HPD (Hot Plug Detect) signal from the display
3. If HPD does not assert (stays 0), the firmware triggers an ASSERT panic

The firmware should handle this gracefully (timeout + retry), but Apple's
implementation treats it as a fatal assertion.

## Trigger scenarios (most common first)

### 1. BetterDisplay / BetterDummy

BetterDisplay creates virtual screens and programmatically controls display
resolution/scaling. This directly interacts with DCP power sequencing and has
been the #1 reported trigger across thousands of GitHub issues. Even remnants
after uninstall (plists, preferences, sandbox containers) can occasionally
cause issues.

### 2. External monitor via USB-C to HDMI

USB-C alt-mode to HDMI requires active conversion. The HDMI adapter's
handshake timing can conflict with the DCP power-on sequence. USB-C direct
to DisplayPort (DP) is significantly more reliable because it uses native
DisplayPort alt-mode without conversion.

### 3. Sleep/wake transitions

The panic often occurs when the system wakes from sleep. The DCP firmware
state machine can get into a race condition during sleep entry and wake
restoration — particularly when connected to external displays.

### 4. Multiple monitors with mixed specs

Different resolutions, refresh rates, or display types (built-in + external
+ virtual) increase the chance of DCP power sequencing failures.

### 5. macOS version-specific bugs

Apple has partially addressed this in various macOS point releases but has
never fully fixed it. Certain builds are worse than others.

## What to check on the user's system

```bash
# Check if BetterDisplay is installed
mdfind "kMDItemFSName == '*BetterDisplay*'"
ls /Applications/BetterDisplay* ~/Applications/BetterDisplay* 2>/dev/null
brew list --cask 2>/dev/null | grep -i better

# Check DisplayLink system extension
systemextensionsctl list | grep -i displaylink

# Check for panic logs
ls -lt ~/Library/Logs/DiagnosticReports/*.panic 2>/dev/null | head -5
grep -l 'DCP PANIC\|AppleDCPDPTX' ~/Library/Logs/DiagnosticReports/*.panic 2>/dev/null

# Check recent kernel messages
sudo log show --predicate 'process == "kernel"' --last 1h | grep -i panic
```

## Workarounds (ordered by effectiveness and invasiveness)

| # | Workaround | Effort | Effectiveness |
|---|-----------|--------|---------------|
| 1 | Settings > Battery > prevent sleep when display off | Low | High |
| 2 | Disconnect external monitors | Low | High (diagnostic) |
| 3 | Swap USB-C/HDMI cable for USB-C to DP | Low | Medium |
| 4 | Shutdown + 30s wait | Low | Low (temporary) |
| 5 | Safe Boot to check | Medium | Medium (diagnostic) |
| 6 | Uninstall BetterDisplay + clean config | Medium | High |
| 7 | Update macOS | Medium | Variable |
| 8 | Full erase/reinstall | High | High (last resort) |

## Apple Silicon hardware repair relevance

Apple has acknowledged DCP-related hardware issues on certain models (known
programs for display backlight service on some 13-inch M2 MacBook Air and
MacBook Pro models). However, the DCP PANIC - ASSERT crash itself is
**not** a reliable hardware failure indicator. Hardware repair should only
be pursued if:

- Panic happens with built-in display only (no external monitors)
- No BetterDisplay or similar software ever installed
- Panics across multiple macOS versions (clean installs)
- Apple Diagnostics / ASD passes software tests but panic persists

## Reference links

- BetterDisplay GitHub issue tracker: https://github.com/waydabber/BetterDisplay/issues
- Apple Community discussions (search "DCP PANIC"):
  https://discussions.apple.com/search?q=DCP+PANIC
