---
sidebar_position: 6
---

# Step 5 — AI Analysis

When an error is detected, it's sent to an AI language model for analysis. The system builds a detailed prompt that includes:

- The **device name** and **timestamp**
- The **error line** itself
- **Surrounding context** — the 30 lines before and after the error for full visibility
- **Recent command history** — what commands were typed leading up to the error

## AI Response Structure

The AI responds with a structured analysis:

| Section | What it answers |
|---------|-----------------|
| Root Cause | What specifically caused this error |
| Impact | What services or interfaces are affected |
| Solution | Exact VRP commands to fix the issue |
| Prevention | Best practices to avoid it in the future |

## Privacy

The AI service connects to a self-hosted LLM server (compatible with the OpenAI API format), so **no data leaves your network**.
