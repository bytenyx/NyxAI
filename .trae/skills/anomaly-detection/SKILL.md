---
name: "anomaly-detection"
description: "Detects anomalies in metrics data using various algorithms. Invoke when metrics need to be analyzed for anomalies."
agent_role: "monitor"
version: "1.0.0"
---

# Anomaly Detection Skill

This skill analyzes metrics data and identifies anomalies using configured detection algorithms.

## When to Use

- After collecting metrics data
- During periodic health checks
- When investigating service issues

## Input Parameters

- `metrics`: List of metric data to analyze
- `service_id`: Target service identifier
- `sensitivity`: Detection sensitivity (0.0 - 1.0)

## Output

Returns list of detected anomalies with severity levels and scores.
