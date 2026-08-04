from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from hk_equity_strategies.catalog import (
    HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE,
    HK_LOW_VOL_DIVIDEND_QUALITY_SNAPSHOT_PROFILE,
)
from hk_equity_strategies.runtime_readiness import build_hk_runtime_readiness

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "print_hk_runtime_readiness.py"


def test_ibkr_global_etf_readiness_uses_hk_market_defaults():
    plan = build_hk_runtime_readiness(
        HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE,
        platform_id="ibkr",
    )

    assert plan["runtime_enabled"] is True
    assert plan["dry_run_only"] is True
    assert plan["market_defaults"] == {
        "market": "HK",
        "market_calendar": "XHKG",
        "market_timezone": "Asia/Hong_Kong",
        "market_exchange": "SEHK",
        "trading_currency": "HKD",
        "symbol_suffix": ".HK",
        "quantity_type": "integer_shares",
    }
    assert plan["platform_dry_run_env"]["IBKR_DRY_RUN_ONLY"] == "true"
    assert plan["platform_dry_run_env"]["IBKR_MARKET_EXCHANGE"] == "SEHK"
    assert plan["managed_symbols"] == [
        "02800",
        "02822",
        "03188",
        "03033",
        "02834",
        "02840",
        "03175",
        "03110",
    ]
    assert plan["target_conversion"] == {
        "strategy_target_mode": "weight",
        "platform_native_target_mode": "weight",
        "requires_portfolio_snapshot": False,
        "portfolio_input_name": None,
    }
    assert any("lot-size" in check for check in plan["dry_run_checks"])
    assert any("stamp-duty" in check for check in plan["etf_live_enablement_checks"])
    assert any("official product factsheet" in check for check in plan["etf_live_enablement_checks"])
    assert any("NAV/iNAV" in check for check in plan["etf_live_enablement_checks"])
    assert any("underlying-market trading-hour gaps" in check for check in plan["etf_live_enablement_checks"])
    assert any("futures roll" in check for check in plan["etf_live_enablement_checks"])
    assert plan["live_enablement_thresholds"] == {
        "max_allowed_backtest_drawdown": 0.30,
        "min_required_return_to_drawdown_ratio": 0.50,
        "max_allowed_annualized_turnover": 1.50,
        "min_required_annual_return": 0.0,
        "min_required_walk_forward_years": 3.0,
        "min_required_oos_fold_count": 3,
        "max_single_period_return_contribution": 0.60,
    }
    assert "hk_fees_levies_and_stamp_duty_or_etf_exemption_verified" in plan["required_live_evidence_fields"]
    assert "runtime_etf_product_due_diligence_verified" in plan["required_live_evidence_fields"]
    assert "runtime_market_data_audit_verified" in plan["required_live_evidence_fields"]
    assert "runtime_market_history_source_provenance_verified" in plan["required_live_evidence_fields"]
    assert "backtest_validation_policy_evidence" in plan["required_live_evidence_fields"]
    assert "point_in_time_no_lookahead_and_no_overfit_controls" in plan["required_live_evidence_fields"]
    assert "walk_forward_backtest_min_three_oos_folds" in plan["required_live_evidence_fields"]
    assert "walk_forward_backtest_single_period_return_contribution_below_60_percent" in (
        plan["required_live_evidence_fields"]
    )
    assert "fresh_section_evidence_generated_at" in plan["required_live_evidence_fields"]
    assert "execution_capacity_and_liquidity_limits_verified" in plan["required_live_evidence_fields"]
    assert "dry_run_order_preview_artifact_provenance_verified" in plan["required_live_evidence_fields"]
    assert "staged_rollout_tripwires_and_rollback_ready" in plan["required_live_evidence_fields"]
    assert "bilingual_notification_delivery_log_verified" in plan["required_live_evidence_fields"]
    assert plan["evidence_uri_policy"]["allowed_schemes"] == ["gs://", "https://", "s3://"]
    assert "token=" in plan["evidence_uri_policy"]["rejected_query_markers"]
    assert plan["evidence_freshness_policy"]["required_field"] == "evidence_generated_at"
    assert plan["execution_capacity_policy"]["min_median_daily_turnover_hkd"] == 20_000_000
    assert plan["rollout_risk_policy"]["max_cumulative_drawdown_tripwire"] == 0.05
    assert plan["runtime_etf_product_policy"]["policy_version"] == "hk_runtime_etf_product_due_diligence.v2"
    assert "etf_product_universe_audit_uri" in plan["runtime_etf_product_policy"]["required_uri_fields"]
    assert "official_product_document_uri" in plan["runtime_etf_product_policy"]["required_uri_fields"]
    assert "multi_counter_currency_and_creation_redemption_reviewed" in (
        plan["runtime_etf_product_policy"]["required_boolean_fields"]
    )
    assert "distribution_history" in plan["runtime_market_data_policy"]["required_boolean_fields"]
    assert "market_history_coverage_start" in plan["runtime_market_data_policy"]["required_fields"]
    assert "market_history_source_uri" in plan["runtime_market_data_policy"]["required_uri_fields"]
    assert plan["notification_audit_policy"]["expected_event_type"] == "hk_runtime_live_enablement_dry_run"
    assert "notification_locale_zh_hans" in plan["notification_audit_policy"]["required_boolean_fields"]
    assert plan["dry_run_order_preview_policy"]["policy_version"] == "hk_dry_run_order_preview_provenance.v1"
    assert "raw_order_preview_uri" in plan["dry_run_order_preview_policy"]["required_uri_fields"]
    assert any("ETFs.htm" in url for url in plan["runtime_market_data_policy"]["source_reference_urls"])
    assert any("03175" in check for check in plan["profile_live_optimization_checks"])
    assert any("02800" in check and "TraHK" in check for check in plan["profile_live_optimization_checks"])
    assert any("02822 and 03188" in check for check in plan["profile_live_optimization_checks"])
    assert any("03033" in check and "Hang Seng TECH" in check for check in plan["profile_live_optimization_checks"])
    assert any("02834" in check and "Nasdaq" in check for check in plan["profile_live_optimization_checks"])
    assert any("WTI futures roll" in check for check in plan["profile_live_optimization_checks"])
    assert any("Cloud Run" in note for note in plan["risk_notes"])


def test_longbridge_global_etf_readiness_requires_portfolio_snapshot_conversion():
    plan = build_hk_runtime_readiness(
        HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE,
        platform_id="longbridge",
    )

    assert plan["canonical_profile"] == HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE
    assert plan["platform_dry_run_env"]["ACCOUNT_REGION"] == "HK"
    assert plan["platform_dry_run_env"]["LONGBRIDGE_SYMBOL_SUFFIX"] == ".HK"
    assert plan["target_conversion"] == {
        "strategy_target_mode": "weight",
        "platform_native_target_mode": "value",
        "requires_portfolio_snapshot": True,
        "portfolio_input_name": "portfolio_snapshot",
    }
    assert "portfolio_snapshot" in plan["available_inputs"]


def test_low_vol_dividend_quality_readiness_requires_snapshot_artifacts():
    plan = build_hk_runtime_readiness(
        HK_LOW_VOL_DIVIDEND_QUALITY_SNAPSHOT_PROFILE,
        platform_id="longbridge",
    )

    assert plan["runtime_enabled"] is True
    assert plan["required_inputs"] == ["feature_snapshot"]
    assert plan["available_inputs"] == ["feature_snapshot", "portfolio_snapshot"]
    assert plan["managed_symbols"] == []
    assert plan["managed_symbols_source"] == "runtime_input_required"
    assert plan["runtime_requirements"] == {
        "input_mode": "feature_snapshot",
        "requires_snapshot_artifacts": True,
        "requires_snapshot_manifest_path": True,
        "snapshot_contract_version": "hk_low_vol_dividend_quality_snapshot.factor_snapshot.v1",
        "requires_strategy_config_path": False,
        "config_source_policy": "none",
        "reconciliation_output_policy": "optional",
        "profile_group": "snapshot_backed",
    }
    assert plan["platform_dry_run_env"]["LONGBRIDGE_FEATURE_SNAPSHOT_PATH"] == "<required>"
    assert plan["platform_dry_run_env"]["LONGBRIDGE_FEATURE_SNAPSHOT_MANIFEST_PATH"] == "<required>"
    assert plan["target_conversion"] == {
        "strategy_target_mode": "weight",
        "platform_native_target_mode": "value",
        "requires_portfolio_snapshot": True,
        "portfolio_input_name": "portfolio_snapshot",
    }
    assert plan["live_enablement_thresholds"] == {
        "max_allowed_backtest_drawdown": 0.30,
        "min_required_return_to_drawdown_ratio": 0.50,
        "max_allowed_annualized_turnover": 1.00,
        "min_required_annual_return": 0.0,
        "min_required_walk_forward_years": 3.0,
        "min_required_oos_fold_count": 3,
        "max_single_period_return_contribution": 0.60,
    }
    assert plan["execution_capacity_policy"]["min_median_daily_turnover_hkd"] == 30_000_000
    assert plan["etf_live_enablement_checks"] == []
    assert any("single-name equity" in check for check in plan["equity_live_enablement_checks"])
    assert any("dividend yield and payout-ratio" in check for check in plan["product_live_enablement_checks"])
    assert "runtime_equity_product_due_diligence_verified" in plan["required_live_evidence_fields"]
    assert "runtime_etf_product_due_diligence_verified" not in plan["required_live_evidence_fields"]
    assert "hk_fees_levies_and_stamp_duty_verified" in plan["required_live_evidence_fields"]
    assert "hk_fees_levies_and_stamp_duty_or_etf_exemption_verified" not in plan["required_live_evidence_fields"]
    assert "equity_spread_and_trading_status_guard_verified" in (
        plan["execution_capacity_policy"]["required_boolean_fields"]
    )
    assert "etf_nav_or_spread_guard_verified" not in plan["execution_capacity_policy"]["required_boolean_fields"]
    assert "single-name equity liquidity" in plan["execution_capacity_policy"]["description"]
    assert plan["runtime_equity_product_policy"]["policy_version"] == "hk_runtime_equity_product_due_diligence.v1"
    assert any("factor snapshot" in check for check in plan["profile_live_optimization_checks"])
    assert any("validated factor snapshot artifact" in note for note in plan["risk_notes"])


def test_print_hk_runtime_readiness_json():
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--profile",
            HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE,
            "--platform",
            "ibkr",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["platform"] == "ibkr"
    assert payload["canonical_profile"] == HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE
    assert payload["platform_dry_run_env"]["IBKR_MARKET_DATA_SYMBOL_SUFFIX"] == ".HK"
    assert payload["live_enablement_thresholds"]["max_allowed_backtest_drawdown"] == 0.30
    assert payload["evidence_uri_policy"]["required"] is True
    assert payload["evidence_freshness_policy"]["required"] is True
    assert payload["execution_capacity_policy"]["required"] is True
    assert payload["rollout_risk_policy"]["required"] is True
    assert payload["runtime_etf_product_policy"]["required"] is True
    assert payload["runtime_market_data_policy"]["required"] is True
    assert payload["notification_audit_policy"]["required"] is True
    assert payload["dry_run_order_preview_policy"]["required"] is True
    assert "operator_approval_reference" in payload["required_live_evidence_fields"]


def test_smoke_hk_global_etf_tactical_rotation_dry_run_json():
    script = Path(__file__).resolve().parents[1] / "scripts" / "smoke_hk_global_etf_tactical_rotation_dry_run.py"
    completed = subprocess.run(
        [sys.executable, str(script), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["status"] == "pass"
    assert payload["profile"] == HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE
    assert payload["checks"] == {
        "signal_actionable": True,
        "uses_direct_market_history": True,
        "safe_no_order": True,
        "all_cash": True,
        "risk_gate_rejected": True,
        "ibkr_dry_run_only": True,
        "longbridge_dry_run_only": True,
        "longbridge_requires_portfolio_snapshot": True,
        "ibkr_weight_native": True,
    }
    assert payload["execution_mode"] == "synthetic_offline"
    assert payload["order_authority"] == "none"
    assert payload["target_weights"] == {}
    assert payload["gross_exposure"] == 0.0
    assert payload["cash_weight"] == 1.0
    assert payload["platforms"]["ibkr"]["market_defaults"]["market_exchange"] == "SEHK"
    assert payload["platforms"]["longbridge"]["market_defaults"]["symbol_suffix"] == ".HK"
