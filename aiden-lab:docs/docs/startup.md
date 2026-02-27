---
sidebar_position: 10
---

# Startup Sequence

When the AIDEN Labs backend starts, it automatically:

1. Connects to the database (creates it if it doesn't exist)
2. Configures the AI/LLM service
3. Starts the traffic capture (sniffer or proxy, based on settings)
4. Begins watching the log directory for changes
5. Registers the error analyzer to receive new log content
6. Opens the WebSocket for dashboard connections

## Shutdown

When it shuts down, it:

1. Stops the capture service
2. Stops the file watcher
3. Cleans up old log files
4. Closes the database connection

Everything is automated — once the backend is running, the full pipeline is active.
