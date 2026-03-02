---
sidebar_position: 3
---

# Step 2 — Writing Log Files

Regardless of which capture mode is used, all traffic is written to log files on disk. Each device/port gets its own log file, named with the device hostname and a timestamp (e.g., `Router1_2000_20260227_080000.log`).

## Log Format

Each line in the log file follows this format:

```
[2026-02-27 08:00:01] [Router1] → 'display ip interface brief'
[2026-02-27 08:00:01] [Router1] ← 'Interface         IP Address      ...'
[2026-02-27 08:00:02] [Router1] ← '<Router1>'
```

- **→** = commands you typed
- **←** = responses from the router

The device name (e.g., Router1) is automatically detected from router prompts like `<Router1>` or `[Router1]`.

## Data Cleaning

Before writing, the system cleans up the raw data:

- Strips Telnet control sequences (the behind-the-scenes protocol negotiation)
- Removes ANSI escape codes (color/formatting from terminal emulators)
- Handles backspace characters (so corrected typos look clean in the log)
- Reconstructs error messages that arrive split across multiple packets
- Suppresses echoed commands and duplicate prompt lines
