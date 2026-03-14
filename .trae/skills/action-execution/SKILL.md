---
name: "action-execution"
description: "Executes recovery actions and tracks results. Invoke when approved recovery actions need to be executed."
agent_role: "execute"
version: "1.0.0"
---

# Action Execution Skill

This skill executes recovery actions and tracks their execution results.

## When to Use

- When recovery actions are approved
- When automated remediation is triggered
- When executing manual recovery procedures

## Input Parameters

- `actions`: List of actions to execute
- `service_id`: Target service ID

## Output

Returns execution results with success/failure status and execution times.
