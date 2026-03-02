---
sidebar_position: 9
---

# System Architecture Diagram

```mermaid
graph TB
    subgraph Capture[" Traffic Capture"]
        ENSP["eNSP Router Consoles<br/>(Telnet ports 2000-2010)"]
        SNIFF["Sniffer Mode<br/>(Passive packet capture)"]
        PROXY["Proxy Mode<br/>(Active relay)"]
        ENSP --> SNIFF
        ENSP --> PROXY
    end

    subgraph Processing["Processing Pipeline"]
        LOGFILE["Log Files<br/>(one per device)"]
        WATCH["File Watcher<br/>(event-driven)"]
        PARSE["Log Parser<br/>(structured extraction)"]
        DETECT["Error Detector<br/>(pattern matching)"]
    end

    subgraph Analysis[" AI Analysis"]
        LLM["Self-Hosted LLM<br/>(OpenAI-compatible)"]
        PROMPT["Prompt Builder<br/>(error + context + history)"]
    end

    subgraph Storage[" Storage & Delivery"]
        DB["SQLite Database<br/>(errors + solutions)"]
        WS["WebSocket<br/>(real-time push)"]
        DASH["Dashboard"]
    end

    SNIFF --> LOGFILE
    PROXY --> LOGFILE
    LOGFILE --> WATCH
    WATCH --> PARSE
    PARSE --> DETECT
    DETECT --> PROMPT
    PROMPT --> LLM
    LLM --> DB
    DB --> WS
    WS --> DASH
```

## Component Overview

| Component | Description |
|-----------|-------------|
| Traffic Capture | Sniffer or Proxy mode to capture CLI traffic |
| Log Files | One log file per device/port |
| File Watcher | Event-driven monitoring |
| Log Parser | Extracts structured data from log lines |
| Error Detector | Pattern matching for errors |
| AI Analyzer | LLM-based root cause analysis |
| Database | SQLite storage |
| WebSocket | Real-time push to dashboard |
