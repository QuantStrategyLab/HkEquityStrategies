from __future__ import annotations

from typing import Any

BACKTEST_VALIDATION_POLICY_VERSION = "hk_backtest_validation_policy.v1"
MAX_ALLOWED_HK_STRATEGY_DRAWDOWN = 0.30

REQUIRED_BACKTEST_VALIDATION_BOOLEAN_FIELDS: tuple[str, ...] = (
    "survivorship_bias_controls",
    "lookahead_bias_controls",
    "benchmark_period_aligned",
    "point_in_time_inputs_only",
    "signal_timestamp_before_trade_timestamp",
    "reporting_date_asof_lag_enforced",
    "no_future_constituent_universe",
    "train_validation_test_or_walk_forward_split_documented",
    "parameter_grid_pre_registered_and_small",
    "no_full_sample_parameter_selection",
    "multiple_period_robustness_checked",
    "transaction_cost_slippage_lot_size_and_suspension_model_included",
)

REQUIRED_BACKTEST_RISK_CONSTRAINTS: tuple[str, ...] = (
    "max_drawdown_at_or_below_30_percent",
    "positive_strategy_excess_return_vs_profile_benchmark",
    "annualized_turnover_within_profile_threshold",
    "single_name_sector_and_theme_concentration_limits",
    "adv_capacity_spread_board_lot_and_odd_lot_limits",
    "suspension_stale_quote_vcm_cas_and_market_session_controls",
    "hk_fee_levy_stamp_duty_or_etf_exemption_slippage_model",
    "drawdown_tripwire_kill_switch_and_staged_rollout_limits",
)

REQUIRED_BACKTEST_VALIDATION_METRICS: tuple[str, ...] = (
    "period_start",
    "period_end",
    "annual_return",
    "benchmark_annual_return",
    "strategy_excess_return",
    "max_drawdown",
    "annualized_turnover",
)

BACKTEST_VALIDATION_REJECT_CRITERIA: tuple[str, ...] = (
    "using_current_constituents_for_historical_universe",
    "using_future_financials_estimates_or_index_changes_before_effective_timestamp",
    "signal_uses_next_close_or_post_trade_data",
    "choosing_parameters_by_best_full_sample_total_return",
    "missing_transaction_cost_slippage_lot_size_or_suspension_model",
    "single_period_only_backtest_without_walk_forward_or_robustness_checks",
    "sample_artifact_or_synthetic_data_used_as_live_enablement_evidence",
)


def build_backtest_validation_policy() -> dict[str, Any]:
    return {
        "required": True,
        "policy_version": BACKTEST_VALIDATION_POLICY_VERSION,
        "scope": "all_hk_runtime_and_snapshot_scaffold_strategy_profiles",
        "live_enablement_allowed_without_policy_evidence": False,
        "max_allowed_drawdown": MAX_ALLOWED_HK_STRATEGY_DRAWDOWN,
        "required_boolean_fields": list(REQUIRED_BACKTEST_VALIDATION_BOOLEAN_FIELDS),
        "required_risk_constraints": list(REQUIRED_BACKTEST_RISK_CONSTRAINTS),
        "required_metrics": list(REQUIRED_BACKTEST_VALIDATION_METRICS),
        "reject_criteria": list(BACKTEST_VALIDATION_REJECT_CRITERIA),
        "description": (
            "Every HK strategy must provide out-of-sample or walk-forward backtest evidence before live enablement, "
            "and max drawdown must be <= 30% unless a stricter per-profile threshold applies. "
            "Evidence must prove point-in-time inputs, no look-ahead or survivorship bias, pre-registered and small "
            "parameter searches, HK cost/slippage/lot-size/suspension handling, benchmark alignment, and robustness "
            "across multiple periods."
        ),
    }


__all__ = [
    "BACKTEST_VALIDATION_POLICY_VERSION",
    "BACKTEST_VALIDATION_REJECT_CRITERIA",
    "MAX_ALLOWED_HK_STRATEGY_DRAWDOWN",
    "REQUIRED_BACKTEST_RISK_CONSTRAINTS",
    "REQUIRED_BACKTEST_VALIDATION_BOOLEAN_FIELDS",
    "REQUIRED_BACKTEST_VALIDATION_METRICS",
    "build_backtest_validation_policy",
]
