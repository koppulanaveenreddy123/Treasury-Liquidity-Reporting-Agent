"""Custom exceptions used across the application."""


class TreasuryLiquidityAssistantError(Exception):
    """Base exception for the demo application."""


class DataRetrievalError(TreasuryLiquidityAssistantError):
    """Raised when a data source cannot be read or queries fail."""


class ValidationError(TreasuryLiquidityAssistantError):
    """Raised when input data is invalid or cannot be processed."""


class FreshnessWarning(TreasuryLiquidityAssistantError):
    """Raised when source data is stale but processing can continue."""


class AnomalyDetected(TreasuryLiquidityAssistantError):
    """Raised when numerical anomalies are detected."""


class EvaluationMismatch(TreasuryLiquidityAssistantError):
    """Raised when computed results do not match expected ground truth."""


class HumanApprovalRequired(TreasuryLiquidityAssistantError):
    """Raised when a report requires explicit human approval."""
