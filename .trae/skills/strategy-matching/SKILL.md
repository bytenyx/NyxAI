---
name: "strategy-matching"
description: "Matches root causes to appropriate recovery strategies. Invoke when need to determine recovery actions from root causes."
agent_role: "decide"
version: "1.0.0"
---

# Strategy Matching Skill

This skill analyzes root causes and generates appropriate recovery actions using strategy matching.

## When to Use

- After root cause analysis is complete
- When generating remediation plan
- When selecting recovery strategies

## Input Parameters

- `root_causes`: List of identified root causes
- `service_id`: Affected service ID

## Output

Returns matched recovery strategies with confidence scores.
