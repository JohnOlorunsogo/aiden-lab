---
sidebar_position: 2
---

# Step 1 — Capturing CLI Traffic

The system needs to see everything happening in your eNSP console sessions. It supports two capture modes:

## Sniffer Mode (Passive)

This is the default mode on Windows. The system uses a network packet sniffer to passively listen on the loopback network adapter (the internal network that eNSP uses to communicate between your PC and the simulated routers).

### How it works

- eNSP routers expose their CLI over Telnet on specific ports (e.g., ports 2000–2010)
- The sniffer listens on the loopback adapter and filters for TCP traffic on those ports
- Every packet is captured, and the system determines the direction:
  - **Outgoing (→)**: commands you type into the console
  - **Incoming (←)**: responses the router sends back
- The system can auto-detect new console ports as they appear — you don't need to manually configure every port

### Key details

- You connect to eNSP as you normally would; the sniffer is invisible to you
- Duplicate packets (a quirk of Windows loopback capture) are automatically filtered out
- The sniffer handles Telnet protocol noise (control sequences, negotiation bytes) and strips them away, leaving only clean, readable text

## Proxy Mode (Active)

An alternative capture method. Instead of passively sniffing, the system acts as a middleman between your Telnet client and eNSP.

### How it works

- The proxy listens on offset ports (e.g., 3000–3004)
- You connect your Telnet client to the proxy port (e.g., 3000) instead of directly to eNSP (e.g., 2000)
- The proxy forwards everything transparently between you and eNSP, logging all traffic in both directions

## Mode Comparison

| Mode | Advantage | Requirement |
|------|-----------|-------------|
| Sniffer | No config changes needed — completely invisible | Admin privileges, Npcap installed |
| Proxy | Works without admin/Npcap, captures 100% of data | Must change your Telnet connection port |
