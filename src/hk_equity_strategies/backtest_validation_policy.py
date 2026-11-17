from __future__ import annotations

from .policy_catalog import build_backtest_validation_policy, get_policy_spec

_SPEC = get_policy_spec("backtest_validation")

BACKTEST_VALIDATION_POLICY_VERSION = str(_SPEC["policy_version"])
MAX_ALLOWED_HK_STRATEGY_DRAWDOWN = float(_SPEC["max_allowed_drawdown"])
MIN_RETURN_TO_DRAWDOWN_RATIO = float(_SPEC["min_return_to_drawdown_ratio"])
MIN_REQUIRED_OOS_FOLD_COUNT = int(_SPEC["min_required_oos_fold_count"])
MAX_SINGLE_PERIOD_RETURN_CONTRIBUTION = float(_SPEC["max_single_period_return_contribution"])

REQUIRED_BACKTEST_VALIDATION_BOOLEAN_FIELDS: tuple[str, ...] = tuple(_SPEC["required_boolean_fields"])
REQUIRED_BACKTEST_RISK_CONSTRAINTS: tuple[str, ...] = tuple(_SPEC["required_risk_constraints"])
REQUIRED_BACKTEST_VALIDATION_METRICS: tuple[str, ...] = tuple(_SPEC["required_metrics"])
BACKTEST_VALIDATION_REJECT_CRITERIA: tuple[str, ...] = tuple(_SPEC["reject_criteria"])

__all__ = [
    "BACKTEST_VALIDATION_POLICY_VERSION",
    "BACKTEST_VALIDATION_REJECT_CRITERIA",
    "MAX_SINGLE_PERIOD_RETURN_CONTRIBUTION",
    "MAX_ALLOWED_HK_STRATEGY_DRAWDOWN",
    "MIN_REQUIRED_OOS_FOLD_COUNT",
    "MIN_RETURN_TO_DRAWDOWN_RATIO",
    "REQUIRED_BACKTEST_RISK_CONSTRAINTS",
    "REQUIRED_BACKTEST_VALIDATION_BOOLEAN_FIELDS",
    "REQUIRED_BACKTEST_VALIDATION_METRICS",
    "build_backtest_validation_policy",
]
