from __future__ import annotations

import pytest

from hk_equity_strategies import (
    backtest_validation_policy,
    dry_run_order_preview_policy,
    evidence_freshness_policy,
    evidence_uri_policy,
    execution_capacity_policy,
    notification_audit_policy,
    policy_catalog,
    rollout_risk_policy,
    runtime_equity_product_policy,
    runtime_etf_product_policy,
    runtime_market_data_policy,
)


def test_policy_catalog_matches_thin_module_exports():
    assert backtest_validation_policy.build_backtest_validation_policy() == policy_catalog.build_backtest_validation_policy()
    assert dry_run_order_preview_policy.build_dry_run_order_preview_policy() == policy_catalog.build_dry_run_order_preview_policy()
    assert evidence_freshness_policy.build_evidence_freshness_policy() == policy_catalog.build_evidence_freshness_policy()
    assert evidence_uri_policy.build_evidence_uri_policy() == policy_catalog.build_evidence_uri_policy()
    assert execution_capacity_policy.build_execution_capacity_policy("hk_low_vol_dividend_quality_snapshot") == (
        policy_catalog.build_execution_capacity_policy("hk_low_vol_dividend_quality_snapshot")
    )
    assert notification_audit_policy.build_notification_audit_policy() == policy_catalog.build_notification_audit_policy()
    assert rollout_risk_policy.build_rollout_risk_policy() == policy_catalog.build_rollout_risk_policy()
    assert runtime_equity_product_policy.build_runtime_equity_product_policy() == (
        policy_catalog.build_runtime_equity_product_policy()
    )
    assert runtime_etf_product_policy.build_runtime_etf_product_policy() == (
        policy_catalog.build_runtime_etf_product_policy()
    )
    assert runtime_market_data_policy.build_runtime_market_data_policy() == (
        policy_catalog.build_runtime_market_data_policy()
    )


def test_policy_catalog_returns_isolated_copies_and_rejects_unknown_policy():
    first = policy_catalog.build_evidence_freshness_policy()
    first["max_allowed_age_days_by_section"]["strategy_backtest"] = 1
    second = policy_catalog.build_evidence_freshness_policy()
    assert second["max_allowed_age_days_by_section"]["strategy_backtest"] == 90

    with pytest.raises(KeyError):
        policy_catalog.get_policy_spec("missing_policy")
