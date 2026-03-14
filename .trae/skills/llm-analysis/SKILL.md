---
name: "llm-analysis"
description: "Performs root cause analysis using LLM assistance. Invoke when need intelligent analysis of complex anomaly patterns."
agent_role: "analyze"
version: "1.0.0"
---

# LLM Analysis Skill

This skill uses LLM to perform intelligent root cause analysis based on anomaly data and service context.

## When to Use

- When anomalies are complex or unclear
- When human-like analysis is needed
- When generating remediation suggestions

## Input Parameters

- `service_id`: ID of the affected service
- `anomalies`: List of detected anomalies
- `service_context`: Service context information

## Output

Returns LLM-generated root causes with suggested actions and prevention measures.
