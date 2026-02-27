---
sidebar_position: 8
---

# Step 7 — Real-Time Dashboard Notification

The moment an error is analyzed and stored, the system broadcasts it over a WebSocket connection to all connected dashboard clients.

This means:

- The error and its AI-generated solution appear on your dashboard **immediately** — no page refresh needed
- Multiple users can watch the same dashboard simultaneously
- If the WebSocket disconnects, the frontend falls back to periodic polling so you never miss an error
