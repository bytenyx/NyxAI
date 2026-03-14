"""Risk assessment for recovery actions.

This module provides risk assessment capabilities to evaluate
the potential impact and safety of recovery actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from nyxai.recovery.strategies.base import RecoveryAction, RiskLevel


class RiskFactor(str, Enum):
    """Types of risk factors."""

    SERVICE_CRITICALITY = "service_criticality"
    ACTION_IMPACT = "action_impact"
    FAILURE_PROBABILITY = "failure_probability"
    ROLLBACK_DIFFICULTY = "rollback_difficulty"
    BLAST_RADIUS = "blast_radius"
    TIME_OF_DAY = "time_of_day"
    DEPENDENCY_COUNT = "dependency_count"


@dataclass
class RiskScore:
    """Represents a risk score for a specific factor.

    Attributes:
        factor: Type of risk factor.
        score: Risk score (0.0 to 1.0, higher = more risky).
        weight: Weight of this factor in overall calculation.
        description: Description of the risk.
    """

    factor: RiskFactor
    score: float
    weight: float = 1.0
    description: str = ""


@dataclass
class RiskAssessment:
    """Complete risk assessment for a recovery action.

    Attributes:
        action_id: ID of the recovery action.
        overall_score: Overall risk score (0.0 to 1.0).
        risk_level: Risk level classification.
        scores: Individual risk factor scores.
        recommendations: Risk mitigation recommendations.
        approved: Whether the action is approved based on risk.
        assessed_at: Assessment timestamp.
        metadata: Additional assessment metadata.
    """

    action_id: str
    overall_score: float
    risk_level: RiskLevel
    scores: list[RiskScore] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    approved: bool = False
    assessed_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation of the assessment.
        """
        return {
            "action_id": self.action_id,
            "overall_score": self.overall_score,
            "risk_level": self.risk_level.value,
            "scores": [
                {
                    "factor": s.factor.value,
                    "score": s.score,
                    "weight": s.weight,
                    "description": s.description,
                }
                for s in self.scores
            ],
            "recommendations": self.recommendations,
            "approved": self.approved,
            "assessed_at": self.assessed_at.isoformat() if self.assessed_at else None,
            "metadata": self.metadata,
        }


class RiskAssessorConfig(BaseModel):
    """Configuration for Risk Assessor.

    Attributes:
        approval_threshold: Score below which action is auto-approved.
        critical_service_threshold: Score threshold for critical services.
        max_blast_radius: Maximum acceptable blast radius score.
        require_approval_for_critical: Always require approval for critical.
        weights: Custom weights for risk factors.
    """

    approval_threshold: float = Field(
        default=0.3, ge=0.0, le=1.0, description="Auto-approval threshold"
    )
    critical_service_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Critical service threshold"
    )
    max_blast_radius: float = Field(
        default=0.6, ge=0.0, le=1.0, description="Max blast radius"
    )
    require_approval_for_critical: bool = Field(
        default=True, description="Require approval for critical actions"
    )
    weights: dict[str, float] = Field(
        default_factory=lambda: {
            "service_criticality": 0.25,
            "action_impact": 0.20,
            "failure_probability": 0.20,
            "rollback_difficulty": 0.15,
            "blast_radius": 0.10,
            "time_of_day": 0.05,
            "dependency_count": 0.05,
        },
        description="Risk factor weights",
    )


class RiskAssessor:
    """Assesses risk for recovery actions.

    This class evaluates the potential risks of recovery actions
    based on multiple factors and provides recommendations.

    Attributes:
        config: Risk assessor configuration.
        _service_criticality: Cache of service criticality scores.
    """

    def __init__(self, config: RiskAssessorConfig | None = None) -> None:
        """Initialize the risk assessor.

        Args:
            config: Risk assessor configuration. Uses defaults if None.
        """
        self.config = config or RiskAssessorConfig()
        self._service_criticality: dict[str, float] = {}

    def assess(
        self,
        action: RecoveryAction,
        context: dict[str, Any] | None = None,
    ) -> RiskAssessment:
        """Assess the risk of a recovery action.

        Args:
            action: Recovery action to assess.
            context: Additional context about the action.

        Returns:
            Risk assessment result.
        """
        context = context or {}
        scores: list[RiskScore] = []

        # Calculate individual risk factors
        scores.append(self._assess_service_criticality(action, context))
        scores.append(self._assess_action_impact(action, context))
        scores.append(self._assess_failure_probability(action, context))
        scores.append(self._assess_rollback_difficulty(action, context))
        scores.append(self._assess_blast_radius(action, context))
        scores.append(self._assess_time_of_day(action, context))
        scores.append(self._assess_dependency_count(action, context))

        # Calculate overall score (weighted average)
        total_weight = sum(s.weight for s in scores)
        if total_weight > 0:
            overall_score = sum(s.score * s.weight for s in scores) / total_weight
        else:
            overall_score = 0.5

        overall_score = min(overall_score, 1.0)

        # Determine risk level
        risk_level = self._score_to_risk_level(overall_score)

        # Generate recommendations
        recommendations = self._generate_recommendations(scores, overall_score)

        # Determine if approved
        approved = self._determine_approval(
            overall_score, risk_level, action.requires_approval
        )

        return RiskAssessment(
            action_id=action.id,
            overall_score=overall_score,
            risk_level=risk_level,
            scores=scores,
            recommendations=recommendations,
            approved=approved,
            metadata={
                "action_type": action.action_type.value,
                "target": action.target,
                "context": context,
            },
        )

    def _assess_service_criticality(
        self, action: RecoveryAction, context: dict[str, Any]
    ) -> RiskScore:
        """Assess service criticality risk.

        Args:
            action: Recovery action.
            context: Execution context.

        Returns:
            Risk score for service criticality.
        """
        service_id = action.target
        criticality = context.get("service_criticality", "medium")

        # Map criticality to score
        criticality_scores = {
            "critical": 1.0,
            "high": 0.75,
            "medium": 0.5,
            "low": 0.25,
        }
        score = criticality_scores.get(criticality.lower(), 0.5)

        return RiskScore(
            factor=RiskFactor.SERVICE_CRITICALITY,
            score=score,
            weight=self.config.weights.get("service_criticality", 0.25),
            description=f"Service '{service_id}' has {criticality} criticality",
        )

    def _assess_action_impact(
        self, action: RecoveryAction, context: dict[str, Any]
    ) -> RiskScore:
        """Assess action impact risk.

        Args:
            action: Recovery action.
            context: Execution context.

        Returns:
            Risk score for action impact.
        """
        # Map action types to impact scores
        impact_scores = {
            "restart": 0.4,
            "scale": 0.2,
            "clear_cache": 0.1,
            "circuit_breaker": 0.5,
            "rollback": 0.6,
            "config_update": 0.3,
            "alert": 0.0,
            "custom": 0.5,
        }
        score = impact_scores.get(action.action_type.value, 0.5)

        return RiskScore(
            factor=RiskFactor.ACTION_IMPACT,
            score=score,
            weight=self.config.weights.get("action_impact", 0.20),
            description=f"Action type '{action.action_type.value}' has impact score {score}",
        )

    def _assess_failure_probability(
        self, action: RecoveryAction, context: dict[str, Any]
    ) -> RiskScore:
        """Assess failure probability risk.

        Args:
            action: Recovery action.
            context: Execution context.

        Returns:
            Risk score for failure probability.
        """
        # Check historical success rate if available
        historical_success = context.get("historical_success_rate", 0.9)
        failure_prob = 1.0 - historical_success

        # Adjust based on action complexity
        complexity_factors = {
            "restart": 0.1,
            "scale": 0.15,
            "clear_cache": 0.05,
            "circuit_breaker": 0.2,
            "rollback": 0.25,
            "config_update": 0.15,
            "alert": 0.0,
            "custom": 0.3,
        }
        complexity = complexity_factors.get(action.action_type.value, 0.2)

        score = min(failure_prob + complexity, 1.0)

        return RiskScore(
            factor=RiskFactor.FAILURE_PROBABILITY,
            score=score,
            weight=self.config.weights.get("failure_probability", 0.20),
            description=f"Failure probability: {score:.2%} (historical: {historical_success:.2%})",
        )

    def _assess_rollback_difficulty(
        self, action: RecoveryAction, context: dict[str, Any]
    ) -> RiskScore:
        """Assess rollback difficulty risk.

        Args:
            action: Recovery action.
            context: Execution context.

        Returns:
            Risk score for rollback difficulty.
        """
        # Map action types to rollback difficulty
        rollback_scores = {
            "restart": 0.0,  # Easy to restart again
            "scale": 0.2,  # Can scale back
            "clear_cache": 0.1,  # Cache will refill
            "circuit_breaker": 0.3,  # Can disable
            "rollback": 0.5,  # Rollback of rollback is complex
            "config_update": 0.4,  # Need to revert config
            "alert": 0.0,  # No rollback needed
            "custom": 0.5,  # Unknown
        }
        score = rollback_scores.get(action.action_type.value, 0.5)

        return RiskScore(
            factor=RiskFactor.ROLLBACK_DIFFICULTY,
            score=score,
            weight=self.config.weights.get("rollback_difficulty", 0.15),
            description=f"Rollback difficulty for '{action.action_type.value}': {score}",
        )

    def _assess_blast_radius(
        self, action: RecoveryAction, context: dict[str, Any]
    ) -> RiskScore:
        """Assess blast radius risk.

        Args:
            action: Recovery action.
            context: Execution context.

        Returns:
            Risk score for blast radius.
        """
        # Get number of affected services
        affected_count = context.get("affected_service_count", 1)
        downstream_count = context.get("downstream_service_count", 0)

        # Calculate blast radius score
        total_affected = affected_count + downstream_count
        if total_affected <= 1:
            score = 0.1
        elif total_affected <= 3:
            score = 0.3
        elif total_affected <= 5:
            score = 0.5
        elif total_affected <= 10:
            score = 0.7
        else:
            score = 0.9

        return RiskScore(
            factor=RiskFactor.BLAST_RADIUS,
            score=score,
            weight=self.config.weights.get("blast_radius", 0.10),
            description=f"Blast radius: {total_affected} services affected",
        )

    def _assess_time_of_day(
        self, action: RecoveryAction, context: dict[str, Any]
    ) -> RiskScore:
        """Assess time of day risk.

        Args:
            action: Recovery action.
            context: Execution context.

        Returns:
            Risk score for time of day.
        """
        # Get current hour (0-23)
        hour = datetime.utcnow().hour

        # Define peak hours (assume 9 AM - 6 PM UTC is high traffic)
        if 9 <= hour < 18:
            score = 0.6  # Business hours
        elif 7 <= hour < 9 or 18 <= hour < 22:
            score = 0.4  # Shoulder hours
        else:
            score = 0.2  # Off hours

        return RiskScore(
            factor=RiskFactor.TIME_OF_DAY,
            score=score,
            weight=self.config.weights.get("time_of_day", 0.05),
            description=f"Current hour ({hour}) risk score: {score}",
        )

    def _assess_dependency_count(
        self, action: RecoveryAction, context: dict[str, Any]
    ) -> RiskScore:
        """Assess dependency count risk.

        Args:
            action: Recovery action.
            context: Execution context.

        Returns:
            Risk score for dependency count.
        """
        # Get dependency count
        dependency_count = context.get("dependency_count", 0)

        # Calculate score based on dependencies
        if dependency_count == 0:
            score = 0.0
        elif dependency_count <= 2:
            score = 0.2
        elif dependency_count <= 5:
            score = 0.4
        elif dependency_count <= 10:
            score = 0.6
        else:
            score = 0.8

        return RiskScore(
            factor=RiskFactor.DEPENDENCY_COUNT,
            score=score,
            weight=self.config.weights.get("dependency_count", 0.05),
            description=f"Service has {dependency_count} dependencies",
        )

    def _score_to_risk_level(self, score: float) -> RiskLevel:
        """Convert score to risk level.

        Args:
            score: Risk score (0.0 to 1.0).

        Returns:
            Risk level classification.
        """
        if score < 0.25:
            return RiskLevel.LOW
        elif score < 0.5:
            return RiskLevel.MEDIUM
        elif score < 0.75:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def _generate_recommendations(
        self, scores: list[RiskScore], overall_score: float
    ) -> list[str]:
        """Generate risk mitigation recommendations.

        Args:
            scores: Individual risk scores.
            overall_score: Overall risk score.

        Returns:
            List of recommendations.
        """
        recommendations = []

        # Find high-risk factors
        high_risk_factors = [s for s in scores if s.score > 0.6]

        for factor in high_risk_factors:
            if factor.factor == RiskFactor.SERVICE_CRITICALITY:
                recommendations.append(
                    "Consider executing during maintenance window for critical services"
                )
            elif factor.factor == RiskFactor.ACTION_IMPACT:
                recommendations.append(
                    "Review action impact and consider less invasive alternatives"
                )
            elif factor.factor == RiskFactor.FAILURE_PROBABILITY:
                recommendations.append(
                    "Have rollback plan ready before executing"
                )
            elif factor.factor == RiskFactor.ROLLBACK_DIFFICULTY:
                recommendations.append(
                    "Test rollback procedure before executing action"
                )
            elif factor.factor == RiskFactor.BLAST_RADIUS:
                recommendations.append(
                    "Notify stakeholders of potential widespread impact"
                )
            elif factor.factor == RiskFactor.TIME_OF_DAY:
                recommendations.append(
                    "Consider delaying action to off-peak hours"
                )
            elif factor.factor == RiskFactor.DEPENDENCY_COUNT:
                recommendations.append(
                    "Verify all dependencies are healthy before proceeding"
                )

        # Add general recommendations based on overall score
        if overall_score > 0.7:
            recommendations.append(
                "HIGH RISK: Manual approval strongly recommended"
            )
        elif overall_score > 0.5:
            recommendations.append(
                "MEDIUM RISK: Review action details before proceeding"
            )

        if not recommendations:
            recommendations.append("Risk level acceptable for automatic execution")

        return recommendations

    def _determine_approval(
        self,
        overall_score: float,
        risk_level: RiskLevel,
        requires_approval: bool,
    ) -> bool:
        """Determine if action is approved based on risk.

        Args:
            overall_score: Overall risk score.
            risk_level: Risk level classification.
            requires_approval: Whether action requires approval.

        Returns:
            True if action is approved.
        """
        # If explicitly requires approval, not auto-approved
        if requires_approval:
            return False

        # If critical risk level and config requires approval
        if (
            risk_level == RiskLevel.CRITICAL
            and self.config.require_approval_for_critical
        ):
            return False

        # Auto-approve if below threshold
        return overall_score < self.config.approval_threshold

    def set_service_criticality(self, service_id: str, criticality: float) -> None:
        """Set the criticality score for a service.

        Args:
            service_id: Service ID.
            criticality: Criticality score (0.0 to 1.0).
        """
        self._service_criticality[service_id] = min(max(criticality, 0.0), 1.0)

    def get_service_criticality(self, service_id: str) -> float:
        """Get the criticality score for a service.

        Args:
            service_id: Service ID.

        Returns:
            Criticality score (0.0 to 1.0).
        """
        return self._service_criticality.get(service_id, 0.5)
