---
sidebar_position: 5
---

# Step 4 — Detecting Errors

The new log content is sent through two processing stages:

## Parsing

The log parser reads each line and extracts structured information:

| Field | Description |
|-------|-------------|
| Timestamp | when the line was logged |
| Device ID | which router/switch produced it |
| Direction | whether it's a command (→) or a response (←) |
| Content | the actual text |

## Pattern Matching

The error detector checks each line against two sets of known patterns:

### Critical Patterns

Serious errors that typically need immediate attention:

- `Error:` messages (e.g., Error: Unrecognized command)
- Interface errors (down, error-down)
- Protocol failures (OSPF neighbor errors, BGP session drops)

### Warning Patterns

Less severe issues worth noting:

- Duplicate IP addresses
- Timeout messages
- Configuration conflicts

## Deduplication

The system also has TTL-based deduplication — if the same error appears again within 5 minutes, it's not flagged again. This prevents you from being flooded with repeated alerts for the same issue.
