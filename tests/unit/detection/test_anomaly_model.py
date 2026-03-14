"""Unit tests for anomaly model."""

from __future__ import annotations

from datetime import datetime

import pytest

from nyxai.detection.models.anomaly import Anomaly, AnomalySeverity


class TestAnomaly:
    """Tests for Anomaly model."""

    def test_create_anomaly(self):
        """Test creating an anomaly."""
        anomaly = Anomaly.create(
            title="Test Anomaly",
            description="Test description",
            severity=AnomalySeverity.HIGH,
            source_type="metric",
            detection_method="three_sigma",
            score=0.85,
            confidence=0.9,
        )

        assert anomaly.title == "Test Anomaly"
        assert anomaly.description == "Test description"
        assert anomaly.severity == AnomalySeverity.HIGH
        assert anomaly.source_type == "metric"
        assert anomaly.detection_method == "three_sigma"
        assert anomaly.score == 0.85
        assert anomaly.confidence == 0.9
        assert anomaly.id is not None
        assert anomaly.timestamp is not None

    def test_anomaly_from_score(self):
        """Test creating anomaly severity from score."""
        assert Anomaly.from_score(0.95) == AnomalySeverity.CRITICAL
        assert Anomaly.from_score(0.8) == AnomalySeverity.HIGH
        assert Anomaly.from_score(0.6) == AnomalySeverity.MEDIUM
        assert Anomaly.from_score(0.4) == AnomalySeverity.LOW
        assert Anomaly.from_score(0.2) == AnomalySeverity.INFO

    def test_anomaly_to_dict(self):
        """Test converting anomaly to dictionary."""
        anomaly = Anomaly.create(
            title="Test Anomaly",
            description="Test description",
            severity=AnomalySeverity.HIGH,
            source_type="metric",
            detection_method="three_sigma",
            score=0.85,
            confidence=0.9,
            service_id="service-a",
            metric_name="cpu_usage",
        )

        data = anomaly.to_dict()

        assert data["title"] == "Test Anomaly"
        assert data["description"] == "Test description"
        assert data["severity"] == "high"
        assert data["source_type"] == "metric"
        assert data["detection_method"] == "three_sigma"
        assert data["score"] == 0.85
        assert data["confidence"] == 0.9
        assert data["service_id"] == "service-a"
        assert data["metric_name"] == "cpu_usage"
        assert "id" in data
        assert "timestamp" in data

    def test_anomaly_from_dict(self):
        """Test creating anomaly from dictionary."""
        data = {
            "id": "test-id",
            "title": "Test Anomaly",
            "description": "Test description",
            "severity": "high",
            "source_type": "metric",
            "detection_method": "three_sigma",
            "score": 0.85,
            "confidence": 0.9,
            "timestamp": datetime.utcnow().isoformat(),
            "service_id": "service-a",
        }

        anomaly = Anomaly.from_dict(data)

        assert anomaly.id == "test-id"
        assert anomaly.title == "Test Anomaly"
        assert anomaly.severity == AnomalySeverity.HIGH
        assert anomaly.score == 0.85

    def test_anomaly_equality(self):
        """Test anomaly equality comparison."""
        anomaly1 = Anomaly.create(title="Test 1", severity=AnomalySeverity.HIGH)
        anomaly2 = Anomaly.create(title="Test 2", severity=AnomalySeverity.HIGH)
        anomaly3 = Anomaly.create(title="Test 1", severity=AnomalySeverity.LOW)

        # Different IDs should not be equal
        assert anomaly1 != anomaly2

        # Same title but different severity
        anomaly3.id = anomaly1.id
        assert anomaly1 != anomaly3

    def test_anomaly_str_representation(self):
        """Test string representation of anomaly."""
        anomaly = Anomaly.create(
            title="High CPU",
            severity=AnomalySeverity.HIGH,
            score=0.85,
        )

        str_repr = str(anomaly)
        assert "High CPU" in str_repr
        assert "high" in str_repr

    def test_anomaly_with_metadata(self):
        """Test anomaly with metadata."""
        anomaly = Anomaly.create(
            title="Test Anomaly",
            severity=AnomalySeverity.HIGH,
            metadata={"index": 10, "value": 150.0},
        )

        assert anomaly.metadata["index"] == 10
        assert anomaly.metadata["value"] == 150.0

    def test_anomaly_severity_ordering(self):
        """Test anomaly severity ordering."""
        severities = [
            AnomalySeverity.INFO,
            AnomalySeverity.LOW,
            AnomalySeverity.MEDIUM,
            AnomalySeverity.HIGH,
            AnomalySeverity.CRITICAL,
        ]

        for i, sev in enumerate(severities):
            assert sev.value == i + 1

    def test_anomaly_timestamp_handling(self):
        """Test anomaly timestamp handling."""
        custom_time = datetime(2024, 1, 15, 10, 30, 0)

        anomaly = Anomaly.create(
            title="Test",
            severity=AnomalySeverity.HIGH,
            timestamp=custom_time,
        )

        assert anomaly.timestamp == custom_time

        # Test from dict with string timestamp
        data = anomaly.to_dict()
        restored = Anomaly.from_dict(data)
        assert restored.timestamp == custom_time
