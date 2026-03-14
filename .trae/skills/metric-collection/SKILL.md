---
name: "metric-collection"
description: "Collects and preprocesses metrics data from various sources. Invoke when agent needs to gather metrics for monitoring or analysis."
agent_role: "monitor"
version: "1.0.0"
---

# Metric Collection Skill

This skill handles the collection and preprocessing of metrics data from various sources like Prometheus, Grafana, etc.

## When to Use

- When starting monitoring workflow
- When metrics data is needed for anomaly detection
- When refreshing current metrics data

## Input Parameters

- `service_id`: Target service identifier
- `metric_names`: List of metric names to collect
- `time_range`: Time range for collection (start, end)

## Output

Returns collected and preprocessed metrics data with quality scores.
