from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from hk_equity_strategies.catalog import HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE
from hk_equity_strategies.runtime_live_enablement_evidence import (
    build_runtime_live_enablement_evidence_template,
    validate_runtime_live_enablement_evidence,
)

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_hk_runtime_live_enablement.py"


def _evidence(**overrides):
    payload = {
        "evidence_type": "hk_runtime_live_enablement",
        "profile": HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE,
        "platform": "longbridge",
        "validation_as_of": "2026-06-02",
        "strategy_backtest": {
            "status": "passed",
            "out_of_sample": True,
            "period_start": "2021-09-01",
            "period_end": "2026-05-29",
            "annual_return": 0.1716,
            "max_drawdown": -0.0806,
            "rolling_oos_fold_max_drawdown": -0.092,
            "annual_return_to_max_drawdown_ratio": 2.13,
            "annualized_turnover": 0.42,
            "survivorship_bias_controls": True,
            "lookahead_bias_controls": True,
            "benchmark_period_aligned": True,
            "point_in_time_inputs_only": True,
            "signal_timestamp_before_trade_timestamp": True,
            "reporting_date_asof_lag_enforced": True,
            "no_future_constituent_universe": True,
            "train_validation_test_or_walk_forward_split_documented": True,
            "parameter_grid_pre_registered_and_small": True,
            "no_full_sample_parameter_selection": True,
            "rolling_oos_fold_drawdown_controls": True,
            "parameter_sensitivity_and_holdout_stability_controls": True,
            "multiple_period_robustness_checked": True,
            "regime_stress_and_liquidity_shock_controls": True,
            "transaction_cost_slippage_lot_size_and_suspension_model_included": True,
            "fee_slippage_spread_stress_sensitivity_controls": True,
            "net_return_after_costs_controls": True,
            "data_vendor_reconciliation_and_missingness_controls": True,
            "corporate_action_delisting_and_stale_price_controls": True,
            "cash_leverage_short_borrow_and_margin_controls": True,
            "tail_loss_time_underwater_and_recovery_controls": True,
            "portfolio_correlation_and_aggregate_risk_budget_controls": True,
            "benchmark_symbol": "03110",
            "benchmark_annual_return": 0.08,
            "strategy_excess_return": 0.0916,
            "evidence_generated_at": "2026-04-15",
            "evidence_uri": "gs://qsl-hk-evidence/runtime/hk-high-dividend-low-vol-trend/backtest.json",
        },
        "runtime_readiness": {
            "status": "passed",
            "profile": HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE,
            "platform": "longbridge",
            "market_history_feed_verified": True,
            "managed_symbols_verified": True,
            "target_conversion_verified": True,
            "dry_run_only_before_approval": True,
            "market_history_source_name": "audited-prod-hk-etf-market-history",
            "market_history_coverage_start": "2021-09-01",
            "market_history_coverage_end": "2026-05-29",
            "market_history_source_uri": (
                "gs://qsl-hk-prod-sources/runtime/hk-high-dividend-low-vol-trend/20260601/market-history.parquet"
            ),
            "market_history_quality_report_uri": (
                "gs://qsl-hk-prod-sources/runtime/hk-high-dividend-low-vol-trend/20260601/market-history-quality.json"
            ),
            "point_in_time_data_dictionary_uri": (
                "gs://qsl-hk-prod-sources/runtime/hk-high-dividend-low-vol-trend/20260601/data-dictionary.json"
            ),
            "point_in_time_market_history": True,
            "adjusted_price_history": True,
            "distribution_history": True,
            "corporate_action_history": True,
            "stale_quote_checks": True,
            "suspension_and_trading_status_checks": True,
            "holiday_and_half_day_calendar_checks": True,
            "symbol_mapping_history": True,
            "etf_nav_or_inav_source_verified": True,
            "stamp_duty_or_etf_exemption_source_verified": True,
            "evidence_generated_at": "2026-05-25",
            "evidence_uri": "gs://qsl-hk-evidence/runtime/hk-high-dividend-low-vol-trend/readiness.json",
        },
        "platform_dry_run_order_preview": {
            "status": "passed",
            "orders_previewed": 2,
            "fractional_share_errors": 0,
            "lot_size_errors": 0,
            "currency_errors": 0,
            "symbol_mapping_errors": 0,
            "bid_ask_spread_captured": True,
            "slippage_estimate_captured": True,
            "notification_sent": True,
            "notification_schema_version": "hk_live_enablement_notification.v1",
            "notification_event_type": "hk_runtime_live_enablement_dry_run",
            "notification_correlation_id": "hk-runtime-hd-lv-20260602-dryrun-001",
            "notification_locale_en": True,
            "notification_locale_zh_hans": True,
            "notification_contains_profile": True,
            "notification_contains_platform": True,
            "notification_contains_validation_status": True,
            "notification_contains_order_preview_summary": True,
            "notification_redacts_sensitive_fields": True,
            "notification_delivery_log_uri": (
                "gs://qsl-hk-evidence/runtime/hk-high-dividend-low-vol-trend/notifications/"
                "20260602-dryrun.json"
            ),
            "dry_run_session_id": "hk-runtime-hd-lv-longbridge-20260602-dryrun-001",
            "raw_order_preview_uri": (
                "gs://qsl-hk-evidence/runtime/hk-high-dividend-low-vol-trend/order-preview/"
                "raw-order-preview.json"
            ),
            "raw_order_preview_sha256": "b" * 64,
            "quote_snapshot_uri": (
                "gs://qsl-hk-evidence/runtime/hk-high-dividend-low-vol-trend/order-preview/quote-snapshot.json"
            ),
            "quote_snapshot_sha256": "c" * 64,
            "fee_breakdown_uri": (
                "gs://qsl-hk-evidence/runtime/hk-high-dividend-low-vol-trend/order-preview/fee-breakdown.json"
            ),
            "fee_breakdown_sha256": "d" * 64,
            "order_preview_artifact_not_sample": True,
            "order_preview_redacts_sensitive_fields": True,
            "quote_snapshot_covers_all_symbols": True,
            "fee_breakdown_reconciled_to_broker_preview": True,
            "order_preview_reconciled_to_strategy_decision": True,
            "order_submission_blocked_during_dry_run": True,
            "adv_window_trading_days": 60,
            "median_daily_turnover_hkd": 80_000_000,
            "max_single_order_adv_fraction": 0.01,
            "rebalance_adv_fraction": 0.04,
            "liquidity_cap_verified": True,
            "board_lot_rounding_verified": True,
            "odd_lot_avoidance_verified": True,
            "market_session_routing_verified": True,
            "vcm_price_band_controls_verified": True,
            "etf_nav_or_spread_guard_verified": True,
            "evidence_generated_at": "2026-05-28",
            "evidence_uri": "gs://qsl-hk-evidence/runtime/hk-high-dividend-low-vol-trend/order-preview.json",
        },
        "broker_permission_and_fee_verification": {
            "status": "passed",
            "hk_market_data": True,
            "sehk_trading_permission": True,
            "hkd_cash_handling": True,
            "fees_levies_verified": True,
            "stamp_duty_or_etf_exemption_verified": True,
            "etf_product_permission_verified": True,
            "etf_product_audit_id": "hk-runtime-hd-lv-longbridge-20260602-etf-product-audit-001",
            "managed_etf_symbols_audited_count": 2,
            "etf_product_universe_audit_uri": (
                "gs://qsl-hk-evidence/runtime/hk-high-dividend-low-vol-trend/etf-product/product-universe.json"
            ),
            "official_product_document_uri": (
                "gs://qsl-hk-evidence/runtime/hk-high-dividend-low-vol-trend/etf-product/product-documents.json"
            ),
            "underlying_index_or_reference_asset_source_uri": (
                "gs://qsl-hk-evidence/runtime/hk-high-dividend-low-vol-trend/etf-product/"
                "underlying-index-reference-asset.json"
            ),
            "nav_or_inav_source_uri": (
                "gs://qsl-hk-evidence/runtime/hk-high-dividend-low-vol-trend/etf-product/nav-inav.json"
            ),
            "market_maker_or_liquidity_provider_source_uri": (
                "gs://qsl-hk-evidence/runtime/hk-high-dividend-low-vol-trend/etf-product/"
                "market-maker-liquidity-provider.json"
            ),
            "stock_connect_etf_eligibility_source_uri": (
                "gs://qsl-hk-evidence/runtime/hk-high-dividend-low-vol-trend/etf-product/"
                "stock-connect-etf-eligibility.json"
            ),
            "southbound_etf_turnover_and_fund_flow_source_uri": (
                "gs://qsl-hk-evidence/runtime/hk-high-dividend-low-vol-trend/etf-product/"
                "southbound-etf-turnover-flow.json"
            ),
            "distribution_tax_and_fee_treatment_source_uri": (
                "gs://qsl-hk-evidence/runtime/hk-high-dividend-low-vol-trend/etf-product/"
                "distribution-tax-fees.json"
            ),
            "etf_fee_and_stamp_duty_audit_uri": (
                "gs://qsl-hk-evidence/runtime/hk-high-dividend-low-vol-trend/etf-product/fees-stamp-duty.json"
            ),
            "broker_product_permission_audit_uri": (
                "gs://qsl-hk-evidence/runtime/hk-high-dividend-low-vol-trend/etf-product/broker-permission.json"
            ),
            "all_managed_symbols_confirmed_etp": True,
            "leveraged_inverse_or_synthetic_flags_audited": True,
            "complex_or_futures_based_products_operator_reviewed": True,
            "etf_stamp_duty_exemption_or_tax_treatment_verified": True,
            "market_maker_or_liquidity_provider_presence_checked": True,
            "product_kid_or_prospectus_risk_disclosure_reviewed": True,
            "official_product_documents_current": True,
            "underlying_index_or_reference_asset_verified": True,
            "nav_or_inav_reconciled_to_market_data": True,
            "tracking_error_or_tracking_difference_reviewed": True,
            "stock_connect_etf_eligibility_or_sell_only_status_reviewed": True,
            "etf_connect_daily_turnover_and_fund_flow_trend_reviewed": True,
            "stock_connect_holiday_eligibility_change_and_cross_boundary_settlement_reviewed": True,
            "southbound_buy_order_availability_and_broker_route_reviewed": True,
            "multi_counter_currency_and_creation_redemption_reviewed": True,
            "underlying_market_trading_hour_and_premium_discount_reviewed": True,
            "cross_market_holiday_fx_and_settlement_risk_reviewed": True,
            "futures_roll_margin_and_contango_backwardation_risk_reviewed": True,
            "distribution_policy_and_capital_distribution_risk_reviewed": True,
            "commodity_trust_single_asset_and_storage_risk_reviewed": True,
            "high_dividend_index_concentration_and_yield_trap_risk_reviewed": True,
            "broker_trading_permission_per_symbol_verified": True,
            "currency_and_board_lot_per_symbol_verified": True,
            "distribution_and_corporate_action_treatment_verified": True,
            "evidence_generated_at": "2026-05-20",
            "evidence_uri": "gs://qsl-hk-evidence/runtime/hk-high-dividend-low-vol-trend/broker-fees.json",
        },
        "runtime_switch_plan": {
            "status": "passed",
            "explicit_deploy_step_required": True,
            "rollback_plan_ready": True,
            "dry_run_first": True,
            "production_cloud_run_not_changed_by_package_merge": True,
            "staged_rollout_plan_ready": True,
            "initial_capital_fraction": 0.10,
            "per_symbol_capital_fraction": 0.08,
            "intraday_drawdown_tripwire": 0.02,
            "cumulative_drawdown_tripwire": 0.04,
            "observation_trading_days_before_scale_up": 20,
            "kill_switch_ready": True,
            "post_deploy_monitoring_ready": True,
            "operator_notification_ready": True,
            "severe_weather_trading_runbook_ready": True,
            "vcm_cooling_off_handling_ready": True,
            "evidence_generated_at": "2026-05-20",
            "evidence_uri": "https://github.com/QuantStrategyLab/platform-ops/issues/2026-hk-runtime-switch",
        },
        "risk_approval": {
            "operator_approved": True,
            "live_rollout_approved": True,
            "dry_run_removal_approved": True,
            "approval_reference": "ops-review-2026-06-hk-hd-lv",
        },
    }
    payload.update(overrides)
    return payload


def test_validate_runtime_live_enablement_evidence_accepts_complete_pack():
    result = validate_runtime_live_enablement_evidence(_evidence())

    assert result["validation_status"] == "passed"
    assert result["live_enablement_allowed"] is True
    assert result["live_enablement_thresholds"] == {
        "max_allowed_backtest_drawdown": 0.12,
        "min_required_return_to_drawdown_ratio": 0.5,
        "max_allowed_annualized_turnover": 1.0,
        "min_required_annual_return": 0.0,
        "min_required_walk_forward_years": 3.0,
    }
    assert result["evidence_uri_policy"]["allowed_schemes"] == ["gs://", "https://", "s3://"]
    assert "token=" in result["evidence_uri_policy"]["rejected_query_markers"]
    assert result["validation_as_of"] == "2026-06-02"
    assert result["evidence_freshness_policy"]["required_field"] == "evidence_generated_at"
    assert result["execution_capacity_policy"]["min_median_daily_turnover_hkd"] == 10_000_000
    assert result["rollout_risk_policy"]["max_initial_capital_fraction"] == 0.25
    assert result["runtime_etf_product_policy"]["policy_version"] == "hk_runtime_etf_product_due_diligence.v2"
    assert "etf_product_universe_audit_uri" in result["runtime_etf_product_policy"]["required_uri_fields"]
    assert "official_product_document_uri" in result["runtime_etf_product_policy"]["required_uri_fields"]
    assert "nav_or_inav_source_uri" in result["runtime_etf_product_policy"]["required_uri_fields"]
    assert "stock_connect_etf_eligibility_source_uri" in result["runtime_etf_product_policy"]["required_uri_fields"]
    assert "southbound_etf_turnover_and_fund_flow_source_uri" in (
        result["runtime_etf_product_policy"]["required_uri_fields"]
    )
    assert "complex_or_futures_based_products_operator_reviewed" in (
        result["runtime_etf_product_policy"]["required_boolean_fields"]
    )
    assert "commodity_trust_single_asset_and_storage_risk_reviewed" in (
        result["runtime_etf_product_policy"]["required_boolean_fields"]
    )
    assert "futures_roll_margin_and_contango_backwardation_risk_reviewed" in (
        result["runtime_etf_product_policy"]["required_boolean_fields"]
    )
    assert "high_dividend_index_concentration_and_yield_trap_risk_reviewed" in (
        result["runtime_etf_product_policy"]["required_boolean_fields"]
    )
    assert "stock_connect_etf_eligibility_or_sell_only_status_reviewed" in (
        result["runtime_etf_product_policy"]["required_boolean_fields"]
    )
    assert "etf_connect_daily_turnover_and_fund_flow_trend_reviewed" in (
        result["runtime_etf_product_policy"]["required_boolean_fields"]
    )
    assert "adjusted_price_history" in result["runtime_market_data_policy"]["required_boolean_fields"]
    assert "market_history_coverage_start" in result["runtime_market_data_policy"]["required_fields"]
    assert "market_history_source_uri" in result["runtime_market_data_policy"]["required_uri_fields"]
    assert result["notification_audit_policy"]["expected_event_type"] == "hk_runtime_live_enablement_dry_run"
    assert "notification_delivery_log_uri" in result["notification_audit_policy"]["required_uri_fields"]
    assert result["dry_run_order_preview_policy"]["policy_version"] == "hk_dry_run_order_preview_provenance.v1"
    assert "raw_order_preview_uri" in result["dry_run_order_preview_policy"]["required_uri_fields"]
    assert "raw_order_preview_sha256" in result["dry_run_order_preview_policy"]["required_sha256_fields"]
    assert "fee_breakdown_reconciled_to_broker_preview" in (
        result["dry_run_order_preview_policy"]["required_boolean_fields"]
    )
    assert result["errors"] == []


def test_build_runtime_live_enablement_evidence_template_is_not_preapproved():
    template = build_runtime_live_enablement_evidence_template("hk_hd_gold_trend", platform="ibkr")

    assert template["evidence_type"] == "hk_runtime_live_enablement"
    assert template["template_status"] == "pending_operator_evidence"
    assert template["profile"] == HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE
    assert template["platform"] == "ibkr"
    assert template["runtime_readiness"]["managed_symbols"] == ["02840", "03110"]
    assert template["evidence_uri_policy"]["required"] is True
    assert template["evidence_uri_policy"]["allowed_schemes"] == ["gs://", "https://", "s3://"]
    assert template["evidence_freshness_policy"]["required_field"] == "evidence_generated_at"
    assert template["execution_capacity_policy"]["max_single_order_adv_fraction"] == 0.025
    assert template["rollout_risk_policy"]["min_observation_trading_days_before_scale_up"] == 20
    assert template["runtime_etf_product_policy"]["required"] is True
    assert template["runtime_etf_product_policy"]["policy_version"] == "hk_runtime_etf_product_due_diligence.v2"
    assert "official_product_document_uri" in template["runtime_etf_product_policy"]["required_uri_fields"]
    assert template["runtime_market_data_policy"]["required"] is True
    assert "market_history_source_uri" in template["runtime_market_data_policy"]["required_uri_fields"]
    assert template["backtest_validation_policy"]["policy_version"] == "hk_backtest_validation_policy.v1"
    assert "no_full_sample_parameter_selection" in template["backtest_validation_policy"]["required_boolean_fields"]
    assert template["notification_audit_policy"]["schema_version"] == "hk_live_enablement_notification.v1"
    assert template["notification_audit_policy"]["expected_event_type"] == "hk_runtime_live_enablement_dry_run"
    assert template["dry_run_order_preview_policy"]["required"] is True
    assert template["dry_run_order_preview_policy"]["policy_version"] == "hk_dry_run_order_preview_provenance.v1"
    assert template["validation_as_of"] == "<YYYY-MM-DD>"
    assert template["strategy_backtest"]["annual_return"] is None
    assert template["strategy_backtest"]["rolling_oos_fold_max_drawdown"] is None
    assert template["strategy_backtest"]["annual_return_to_max_drawdown_ratio"] is None
    assert template["strategy_backtest"]["benchmark_symbol"] == "03110"
    assert template["strategy_backtest"]["strategy_excess_return"] is None
    assert template["strategy_backtest"]["point_in_time_inputs_only"] is False
    assert template["strategy_backtest"]["no_full_sample_parameter_selection"] is False
    assert template["strategy_backtest"]["rolling_oos_fold_drawdown_controls"] is False
    assert template["strategy_backtest"]["parameter_sensitivity_and_holdout_stability_controls"] is False
    assert template["strategy_backtest"]["regime_stress_and_liquidity_shock_controls"] is False
    assert template["strategy_backtest"]["fee_slippage_spread_stress_sensitivity_controls"] is False
    assert template["strategy_backtest"]["data_vendor_reconciliation_and_missingness_controls"] is False
    assert template["strategy_backtest"]["tail_loss_time_underwater_and_recovery_controls"] is False
    assert template["strategy_backtest"]["portfolio_correlation_and_aggregate_risk_budget_controls"] is False
    assert template["strategy_backtest"]["net_return_after_costs_controls"] is False
    assert template["strategy_backtest"]["transaction_cost_slippage_lot_size_and_suspension_model_included"] is False
    assert template["platform_dry_run_order_preview"]["liquidity_cap_verified"] is False
    assert template["platform_dry_run_order_preview"]["notification_locale_zh_hans"] is False
    assert template["platform_dry_run_order_preview"]["notification_delivery_log_uri"] == ""
    assert template["platform_dry_run_order_preview"]["dry_run_session_id"] == ""
    assert template["platform_dry_run_order_preview"]["raw_order_preview_uri"] == ""
    assert template["platform_dry_run_order_preview"]["raw_order_preview_sha256"] == ""
    assert template["platform_dry_run_order_preview"]["quote_snapshot_uri"] == ""
    assert template["platform_dry_run_order_preview"]["fee_breakdown_uri"] == ""
    assert template["platform_dry_run_order_preview"]["order_preview_artifact_not_sample"] is False
    assert template["platform_dry_run_order_preview"]["fee_breakdown_reconciled_to_broker_preview"] is False
    assert template["runtime_switch_plan"]["staged_rollout_plan_ready"] is False
    assert template["runtime_switch_plan"]["initial_capital_fraction"] is None
    assert template["runtime_readiness"]["adjusted_price_history"] is False
    assert template["runtime_readiness"]["market_history_coverage_start"] == ""
    assert template["runtime_readiness"]["market_history_source_uri"] == ""
    assert template["broker_permission_and_fee_verification"]["etf_product_audit_id"] == ""
    assert template["broker_permission_and_fee_verification"]["managed_etf_symbols_audited_count"] == 0
    assert template["broker_permission_and_fee_verification"]["etf_product_universe_audit_uri"] == ""
    assert template["broker_permission_and_fee_verification"]["official_product_document_uri"] == ""
    assert template["broker_permission_and_fee_verification"]["stock_connect_etf_eligibility_source_uri"] == ""
    assert template["broker_permission_and_fee_verification"]["southbound_etf_turnover_and_fund_flow_source_uri"] == ""
    assert template["broker_permission_and_fee_verification"]["nav_or_inav_reconciled_to_market_data"] is False
    assert (
        template["broker_permission_and_fee_verification"][
            "stock_connect_etf_eligibility_or_sell_only_status_reviewed"
        ]
        is False
    )
    assert (
        template["broker_permission_and_fee_verification"][
            "etf_connect_daily_turnover_and_fund_flow_trend_reviewed"
        ]
        is False
    )
    assert template["broker_permission_and_fee_verification"][
        "futures_roll_margin_and_contango_backwardation_risk_reviewed"
    ] is False
    assert template["broker_permission_and_fee_verification"]["complex_or_futures_based_products_operator_reviewed"] is False
    assert template["risk_approval"]["operator_approved"] is False


def test_validate_runtime_live_enablement_evidence_rejects_drawdown_above_profile_limit():
    payload = _evidence(strategy_backtest={**_evidence()["strategy_backtest"], "max_drawdown": -0.18})

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("max_drawdown exceeds" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_rejects_oos_fold_drawdown_above_profile_limit():
    payload = _evidence(
        strategy_backtest={**_evidence()["strategy_backtest"], "rolling_oos_fold_max_drawdown": -0.18}
    )

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("rolling_oos_fold_max_drawdown exceeds" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_rejects_low_return_to_drawdown_ratio():
    payload = _evidence(
        strategy_backtest={**_evidence()["strategy_backtest"], "annual_return_to_max_drawdown_ratio": 0.49}
    )

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("annual_return_to_max_drawdown_ratio must be" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_rejects_low_computed_return_to_drawdown_ratio():
    payload = _evidence(
        strategy_backtest={
            **_evidence()["strategy_backtest"],
            "annual_return": 0.03,
            "max_drawdown": -0.10,
            "annual_return_to_max_drawdown_ratio": 2.00,
        }
    )

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("computed_annual_return_to_max_drawdown_ratio must be" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_rejects_excess_turnover():
    payload = _evidence(strategy_backtest={**_evidence()["strategy_backtest"], "annualized_turnover": 1.25})

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("annualized_turnover exceeds" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_rejects_missing_bias_control():
    payload = _evidence(strategy_backtest={**_evidence()["strategy_backtest"], "survivorship_bias_controls": False})

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("strategy_backtest.survivorship_bias_controls" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_rejects_overfit_or_lookahead_backtest_controls():
    payload = _evidence(
        strategy_backtest={
            **_evidence()["strategy_backtest"],
            "point_in_time_inputs_only": False,
            "no_full_sample_parameter_selection": False,
        }
    )

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("strategy_backtest.point_in_time_inputs_only" in error for error in result["errors"])
    assert any("strategy_backtest.no_full_sample_parameter_selection" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_requires_market_data_audit_fields():
    payload = _evidence(runtime_readiness={**_evidence()["runtime_readiness"], "adjusted_price_history": False})

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("runtime_readiness.adjusted_price_history must be true" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_requires_market_history_source_uri():
    payload = _evidence(
        runtime_readiness={
            **_evidence()["runtime_readiness"],
            "market_history_source_uri": "",
        }
    )

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("runtime_readiness.market_history_source_uri is required" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_rejects_reversed_market_history_coverage():
    payload = _evidence(
        runtime_readiness={
            **_evidence()["runtime_readiness"],
            "market_history_coverage_start": "2026-01-01",
            "market_history_coverage_end": "2025-12-31",
        }
    )

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("market_history_coverage_end must not be before market_history_coverage_start" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_rejects_unstable_market_history_quality_report_uri():
    payload = _evidence(
        runtime_readiness={
            **_evidence()["runtime_readiness"],
            "market_history_quality_report_uri": "market-history-quality.json",
        }
    )

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any(
        "runtime_readiness.market_history_quality_report_uri must be a stable URI" in error
        for error in result["errors"]
    )


def test_validate_runtime_live_enablement_evidence_rejects_non_positive_excess_return():
    payload = _evidence(strategy_backtest={**_evidence()["strategy_backtest"], "strategy_excess_return": -0.01})

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("strategy_excess_return must be positive" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_rejects_wrong_benchmark():
    payload = _evidence(strategy_backtest={**_evidence()["strategy_backtest"], "benchmark_symbol": "02800"})

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("benchmark_symbol must be '03110'" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_rejects_short_oos_period():
    payload = _evidence(
        strategy_backtest={
            **_evidence()["strategy_backtest"],
            "period_start": "2024-01-01",
            "period_end": "2026-01-01",
        }
    )

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("period must cover at least" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_rejects_missing_approval_reference():
    payload = _evidence(risk_approval={**_evidence()["risk_approval"], "approval_reference": ""})

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("approval_reference" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_rejects_missing_section_evidence_uri():
    payload = _evidence(
        platform_dry_run_order_preview={
            **_evidence()["platform_dry_run_order_preview"],
            "evidence_uri": "",
        }
    )

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("platform_dry_run_order_preview.evidence_uri is required" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_requires_section_evidence_generated_at():
    payload = _evidence(
        platform_dry_run_order_preview={
            **_evidence()["platform_dry_run_order_preview"],
            "evidence_generated_at": "",
        }
    )

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("platform_dry_run_order_preview.evidence_generated_at is required" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_rejects_stale_evidence_generated_at():
    payload = _evidence(
        runtime_readiness={
            **_evidence()["runtime_readiness"],
            "evidence_generated_at": "2026-05-01",
        }
    )

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("runtime_readiness.evidence_generated_at is stale" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_rejects_order_above_adv_cap():
    payload = _evidence(
        platform_dry_run_order_preview={
            **_evidence()["platform_dry_run_order_preview"],
            "max_single_order_adv_fraction": 0.04,
        }
    )

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("platform_dry_run_order_preview.max_single_order_adv_fraction exceeds" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_requires_execution_capacity_flags():
    payload = _evidence(
        platform_dry_run_order_preview={
            **_evidence()["platform_dry_run_order_preview"],
            "vcm_price_band_controls_verified": False,
        }
    )

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("platform_dry_run_order_preview.vcm_price_band_controls_verified must be true" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_rejects_initial_capital_above_rollout_cap():
    payload = _evidence(runtime_switch_plan={**_evidence()["runtime_switch_plan"], "initial_capital_fraction": 0.50})

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("runtime_switch_plan.initial_capital_fraction exceeds" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_requires_rollout_runbooks():
    payload = _evidence(
        runtime_switch_plan={
            **_evidence()["runtime_switch_plan"],
            "severe_weather_trading_runbook_ready": False,
        }
    )

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("runtime_switch_plan.severe_weather_trading_runbook_ready must be true" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_rejects_unstable_evidence_uri():
    payload = _evidence(
        runtime_readiness={
            **_evidence()["runtime_readiness"],
            "evidence_uri": "manual-check-passed",
        }
    )

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("runtime_readiness.evidence_uri must be a stable URI" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_rejects_secret_bearing_evidence_uri():
    payload = _evidence(
        broker_permission_and_fee_verification={
            **_evidence()["broker_permission_and_fee_verification"],
            "evidence_uri": "https://evidence.example/hk/broker-fees.json?token=secret",
        }
    )

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("must not contain secret-like query parameters" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_requires_all_managed_etfs_audited():
    payload = _evidence(
        broker_permission_and_fee_verification={
            **_evidence()["broker_permission_and_fee_verification"],
            "managed_etf_symbols_audited_count": 1,
        }
    )

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("managed_etf_symbols_audited_count must be >= 2" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_requires_complex_product_review():
    payload = _evidence(
        broker_permission_and_fee_verification={
            **_evidence()["broker_permission_and_fee_verification"],
            "complex_or_futures_based_products_operator_reviewed": False,
        }
    )

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any(
        "broker_permission_and_fee_verification.complex_or_futures_based_products_operator_reviewed must be true"
        in error
        for error in result["errors"]
    )


def test_validate_runtime_live_enablement_evidence_rejects_unstable_etf_product_audit_uri():
    payload = _evidence(
        broker_permission_and_fee_verification={
            **_evidence()["broker_permission_and_fee_verification"],
            "etf_product_universe_audit_uri": "product-universe.json",
        }
    )

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any(
        "broker_permission_and_fee_verification.etf_product_universe_audit_uri must be a stable URI" in error
        for error in result["errors"]
    )


def test_validate_runtime_live_enablement_evidence_requires_product_lineage_checks():
    payload = _evidence(
        broker_permission_and_fee_verification={
            **_evidence()["broker_permission_and_fee_verification"],
            "official_product_document_uri": "",
            "nav_or_inav_reconciled_to_market_data": False,
        }
    )

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any(
        "broker_permission_and_fee_verification.official_product_document_uri is required" in error
        for error in result["errors"]
    )
    assert any(
        "broker_permission_and_fee_verification.nav_or_inav_reconciled_to_market_data must be true" in error
        for error in result["errors"]
    )


def test_validate_runtime_live_enablement_evidence_requires_etf_connect_reviews():
    payload = _evidence(
        broker_permission_and_fee_verification={
            **_evidence()["broker_permission_and_fee_verification"],
            "stock_connect_etf_eligibility_source_uri": "",
            "etf_connect_daily_turnover_and_fund_flow_trend_reviewed": False,
        }
    )

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any(
        "broker_permission_and_fee_verification.stock_connect_etf_eligibility_source_uri is required" in error
        for error in result["errors"]
    )
    assert any(
        "broker_permission_and_fee_verification.etf_connect_daily_turnover_and_fund_flow_trend_reviewed must be true"
        in error
        for error in result["errors"]
    )


def test_validate_runtime_live_enablement_evidence_requires_notification_audit_schema():
    payload = _evidence(
        platform_dry_run_order_preview={
            **_evidence()["platform_dry_run_order_preview"],
            "notification_schema_version": "legacy",
        }
    )

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("notification_schema_version must be" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_requires_bilingual_notification():
    payload = _evidence(
        platform_dry_run_order_preview={
            **_evidence()["platform_dry_run_order_preview"],
            "notification_locale_zh_hans": False,
        }
    )

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("notification_locale_zh_hans must be true" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_rejects_unstable_notification_delivery_log_uri():
    payload = _evidence(
        platform_dry_run_order_preview={
            **_evidence()["platform_dry_run_order_preview"],
            "notification_delivery_log_uri": "notifications/20260602-dryrun.json",
        }
    )

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("notification_delivery_log_uri must be a stable URI" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_requires_dry_run_session_id():
    payload = _evidence(
        platform_dry_run_order_preview={
            **_evidence()["platform_dry_run_order_preview"],
            "dry_run_session_id": "",
        }
    )

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("platform_dry_run_order_preview.dry_run_session_id is required" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_requires_order_preview_sha256():
    payload = _evidence(
        platform_dry_run_order_preview={
            **_evidence()["platform_dry_run_order_preview"],
            "raw_order_preview_sha256": "not-a-sha",
        }
    )

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any(
        "platform_dry_run_order_preview.raw_order_preview_sha256 must be a 64-character hex sha256" in error
        for error in result["errors"]
    )


def test_validate_runtime_live_enablement_evidence_rejects_unstable_quote_snapshot_uri():
    payload = _evidence(
        platform_dry_run_order_preview={
            **_evidence()["platform_dry_run_order_preview"],
            "quote_snapshot_uri": "order-preview/quote-snapshot.json",
        }
    )

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any("platform_dry_run_order_preview.quote_snapshot_uri must be a stable URI" in error for error in result["errors"])


def test_validate_runtime_live_enablement_evidence_requires_broker_fee_reconciliation():
    payload = _evidence(
        platform_dry_run_order_preview={
            **_evidence()["platform_dry_run_order_preview"],
            "fee_breakdown_reconciled_to_broker_preview": False,
        }
    )

    result = validate_runtime_live_enablement_evidence(payload)

    assert result["live_enablement_allowed"] is False
    assert any(
        "platform_dry_run_order_preview.fee_breakdown_reconciled_to_broker_preview must be true" in error
        for error in result["errors"]
    )


def test_runtime_live_enablement_evidence_cli_json(tmp_path):
    evidence_file = tmp_path / "evidence.json"
    evidence_file.write_text(json.dumps(_evidence()), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--evidence-file",
            str(evidence_file),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)

    assert payload["validation_status"] == "passed"
    assert payload["live_enablement_allowed"] is True
    assert payload["evidence_uri_policy"]["allowed_schemes"] == ["gs://", "https://", "s3://"]
    assert payload["evidence_freshness_policy"]["required"] is True
    assert payload["execution_capacity_policy"]["required"] is True
    assert payload["rollout_risk_policy"]["required"] is True
    assert payload["runtime_etf_product_policy"]["policy_version"] == "hk_runtime_etf_product_due_diligence.v2"
    assert payload["runtime_market_data_policy"]["required"] is True
    assert payload["notification_audit_policy"]["required"] is True
    assert payload["dry_run_order_preview_policy"]["required"] is True


def test_print_runtime_live_enablement_evidence_template_cli():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "hk_equity_strategies.runtime_live_enablement_evidence",
            "--print-template",
            "--profile",
            HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE,
            "--platform",
            "longbridge",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)

    assert payload["profile"] == HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE
    assert payload["template_status"] == "pending_operator_evidence"
    assert payload["evidence_uri_policy"]["required"] is True
    assert payload["evidence_freshness_policy"]["required"] is True
    assert payload["execution_capacity_policy"]["required"] is True
    assert payload["rollout_risk_policy"]["required"] is True
    assert payload["runtime_etf_product_policy"]["required"] is True
    assert payload["runtime_market_data_policy"]["required"] is True
    assert payload["notification_audit_policy"]["expected_event_type"] == "hk_runtime_live_enablement_dry_run"
    assert payload["dry_run_order_preview_policy"]["required"] is True
    assert payload["platform_dry_run_order_preview"]["raw_order_preview_uri"] == ""
    assert payload["broker_permission_and_fee_verification"]["etf_product_universe_audit_uri"] == ""
    assert payload["broker_permission_and_fee_verification"]["official_product_document_uri"] == ""
    assert payload["broker_permission_and_fee_verification"]["stock_connect_etf_eligibility_source_uri"] == ""
    assert payload["broker_permission_and_fee_verification"]["etf_connect_daily_turnover_and_fund_flow_trend_reviewed"] is False
