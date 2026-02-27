---
sidebar_position: 4
---

# Step 3 — Watching for Changes

A file watcher continuously monitors the log directory. The moment a log file is created or modified, the watcher:

1. Detects the change
2. Reads only the new content that was just appended (it tracks how much it has already read)
3. Passes the new content to the error detection pipeline

This is event-driven — there's no polling delay. Changes are picked up within milliseconds.
