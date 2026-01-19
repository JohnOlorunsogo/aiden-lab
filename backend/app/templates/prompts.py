"""AI prompt templates for Huawei ENSP error analysis."""


ERROR_ANALYSIS_PROMPT = """You are an expert Huawei network engineer analyzing VRP device logs.

Device: {device_id}
Timestamp: {timestamp}
Device Type: Huawei ENSP (AR/S-series Router/Switch)

Recent Command History:
```
{command_history}
```

Error Context (last {context_lines} lines):
```
{context}
```

Error Detected:
{error_line}

Provide a structured analysis with these exact sections:

**Root Cause:**
[Explain what caused this error]

**Impact:**
[Describe affected services/interfaces]

**Solution:**
[Provide specific VRP commands to fix it]

**Prevention:**
[Best practices to avoid this in the future]
"""


def build_error_analysis_prompt(
    device_id: str,
    timestamp: str,
    context: str,
    error_line: str,
    context_lines: int = 30,
    command_history: str = "No recent commands available"
) -> str:
    """Build the error analysis prompt with provided context."""
    return ERROR_ANALYSIS_PROMPT.format(
        device_id=device_id,
        timestamp=timestamp,
        context=context,
        error_line=error_line,
        context_lines=context_lines,
        command_history=command_history or "No recent commands available"
    )
