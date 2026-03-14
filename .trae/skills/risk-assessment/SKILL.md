---
name: "risk-assessment"
description: "Assesses risk of recovery actions and determines approval requirements. Invoke before executing recovery actions."
agent_role: "decide"
version: "1.0.0"
---

# Risk Assessment Skill

This skill evaluates the risk level of proposed recovery actions and determines if they require approval.

## When to Use

- Before executing recovery actions
- When determining approval workflow
- When assessing action safety

## Input Parameters

- `actions`: List of recovery actions to assess
- `service_id`: Target service ID
- `service_criticality`: Service criticality level

## Output

Returns risk scores, risk levels, and approval requirements for each action.
