---
sidebar_position: 7
---

# Step 6 — Persisting to the Database

Both the error and the AI solution are saved to a local SQLite database:

## Errors Table

Stores:

- Device ID, timestamp, severity
- The error line and surrounding context
- Which pattern triggered the detection

## Solutions Table

Stores:

- Root cause, impact, solution, and prevention
- Linked back to the specific error

## Querying

You can query errors by:

- Device
- Severity
- Time range

You can also dismiss errors from the dashboard once you've addressed them.
