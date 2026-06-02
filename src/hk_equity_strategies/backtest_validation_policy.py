from __future__ import annotations

from typing import Any

BACKTEST_VALIDATION_POLICY_VERSION = "hk_backtest_validation_policy.v1"
MAX_ALLOWED_HK_STRATEGY_DRAWDOWN = 0.30
MIN_RETURN_TO_DRAWDOWN_RATIO = 0.50
MIN_REQUIRED_OOS_FOLD_COUNT = 3
MAX_SINGLE_PERIOD_RETURN_CONTRIBUTION = 0.60

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
    "rolling_oos_fold_drawdown_controls",
    "parameter_sensitivity_and_holdout_stability_controls",
    "multiple_period_robustness_checked",
    "regime_stress_and_liquidity_shock_controls",
    "transaction_cost_slippage_lot_size_and_suspension_model_included",
    "fee_slippage_spread_stress_sensitivity_controls",
    "net_return_after_costs_controls",
    "data_vendor_reconciliation_and_missingness_controls",
    "corporate_action_delisting_and_stale_price_controls",
    "cash_leverage_short_borrow_and_margin_controls",
    "tail_loss_time_underwater_and_recovery_controls",
    "portfolio_correlation_and_aggregate_risk_budget_controls",
)

REQUIRED_BACKTEST_RISK_CONSTRAINTS: tuple[str, ...] = (
    "max_drawdown_at_or_below_30_percent",
    "each_oos_fold_max_drawdown_at_or_below_30_percent",
    "positive_strategy_excess_return_vs_profile_benchmark",
    "annualized_turnover_within_profile_threshold",
    "single_name_sector_and_theme_concentration_limits",
    "factor_exposure_crowding_and_loss_concentration_limits",
    "cash_leverage_short_borrow_and_margin_constraints",
    "adv_capacity_spread_board_lot_and_odd_lot_limits",
    "suspension_stale_quote_vcm_cas_and_market_session_controls",
    "hk_fee_levy_stamp_duty_or_etf_exemption_slippage_model",
    "fee_slippage_spread_sensitivity_stays_profitable",
    "annual_return_to_max_drawdown_ratio_at_or_above_50_percent",
    "minimum_three_independent_oos_folds",
    "single_period_return_contribution_at_or_below_60_percent",
    "worst_month_or_worst_rebalance_loss_within_profile_threshold",
    "time_underwater_and_drawdown_recovery_within_profile_threshold",
    "cross_strategy_correlation_and_aggregate_drawdown_budget_limits",
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
    "oos_fold_count",
    "rolling_oos_fold_max_drawdown",
    "max_single_period_return_contribution",
    "net_annual_return_after_costs",
    "worst_month_or_worst_rebalance_loss",
    "max_time_underwater_days",
    "fee_slippage_stress_excess_return",
    "annual_return_to_max_drawdown_ratio",
    "correlation_to_existing_live_hk_profiles",
    "parameter_sensitivity_summary",
    "capacity_at_target_aum",
)

BACKTEST_VALIDATION_REJECT_CRITERIA: tuple[str, ...] = (
    "using_current_constituents_for_historical_universe",
    "using_future_financials_estimates_or_index_changes_before_effective_timestamp",
    "signal_uses_next_close_or_post_trade_data",
    "choosing_parameters_by_best_full_sample_total_return",
    "missing_transaction_cost_slippage_lot_size_or_suspension_model",
    "single_period_only_backtest_without_walk_forward_or_robustness_checks",
    "sample_artifact_or_synthetic_data_used_as_live_enablement_evidence",
    "gross_return_only_backtest_without_net_cost_validation",
    "rolling_or_oos_fold_drawdown_above_30_percent",
    "insufficient_parameter_sensitivity_or_holdout_stability",
    "fee_slippage_spread_stress_turns_excess_return_non_positive",
    "annual_return_to_max_drawdown_ratio_below_50_percent",
    "fewer_than_three_independent_oos_folds",
    "single_period_return_contribution_above_60_percent",
    "time_underwater_or_worst_rebalance_loss_exceeds_profile_limit",
    "high_correlation_to_existing_live_profiles_without_aggregate_risk_budget",
    "hidden_leverage_or_short_exposure_without_borrow_margin_and_tick_rule_controls",
    "unmodeled_corporate_actions_suspensions_delistings_or_stale_prices",
)


def build_backtest_validation_policy() -> dict[str, Any]:
    return {
        "required": True,
        "policy_version": BACKTEST_VALIDATION_POLICY_VERSION,
        "scope": "all_hk_runtime_and_snapshot_scaffold_strategy_profiles",
        "live_enablement_allowed_without_policy_evidence": False,
        "max_allowed_drawdown": MAX_ALLOWED_HK_STRATEGY_DRAWDOWN,
        "min_return_to_drawdown_ratio": MIN_RETURN_TO_DRAWDOWN_RATIO,
        "min_required_oos_fold_count": MIN_REQUIRED_OOS_FOLD_COUNT,
        "max_single_period_return_contribution": MAX_SINGLE_PERIOD_RETURN_CONTRIBUTION,
        "required_boolean_fields": list(REQUIRED_BACKTEST_VALIDATION_BOOLEAN_FIELDS),
        "required_risk_constraints": list(REQUIRED_BACKTEST_RISK_CONSTRAINTS),
        "required_metrics": list(REQUIRED_BACKTEST_VALIDATION_METRICS),
        "reject_criteria": list(BACKTEST_VALIDATION_REJECT_CRITERIA),
        "description": (
            "Every HK strategy must provide out-of-sample or walk-forward backtest evidence before live enablement, "
            "and max drawdown must be <= 30% unless a stricter per-profile threshold applies. "
            "Evidence must prove point-in-time inputs, no look-ahead or survivorship bias, pre-registered and small "
            "parameter searches, at least three independent OOS folds, per-fold drawdown <= 30%, single-period return "
            "contribution <= 60%, net-of-cost returns, HK cost/slippage/lot-size/suspension "
            "handling, corporate-action / stale-price handling, benchmark alignment, annual-return-to-drawdown ratio, leverage/shorting feasibility, capacity, "
            "fee/slippage stress, tail loss and time-under-water recovery, cross-strategy correlation, aggregate risk budget, "
            "regime stress, and robustness across multiple periods."
        ),
    }


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
