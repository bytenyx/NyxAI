---
name: "topology-analysis"
description: "Analyzes root causes using service topology graph. Invoke when need to identify root causes based on service dependencies."
agent_role: "analyze"
version: "1.0.0"
---

# Topology Analysis Skill

This skill traverses the service topology graph to identify potential root causes of anomalies.

## When to Use

- When anomalies are detected
- When investigating service failures
- When analyzing impact of upstream services

## Input Parameters

- `service_id`: ID of the affected service
- `service_graph`: Service topology graph data
- `anomalies`: List of detected anomalies

## Output

Returns identified root causes with confidence scores and hop distances.
