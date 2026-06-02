from __future__ import annotations

import pytest

from hk_equity_strategies.catalog import (
    HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE,
    HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE,
    HK_LOW_VOL_DIVIDEND_QUALITY_PROFILE,
)
from hk_equity_strategies.runtime_adapters import (
    describe_platform_runtime_requirements,
    get_platform_runtime_adapter,
)


def test_global_etf_rotation_runtime_adapter_uses_market_history():
    adapter = get_platform_runtime_adapter(HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE, platform_id="ibkr")

    assert adapter.available_inputs == frozenset({"market_history"})
    assert adapter.available_capabilities == frozenset({"broker_client"})
    assert adapter.require_snapshot_manifest is False


def test_global_etf_rotation_longbridge_adapter_adds_portfolio_for_value_native_platform():
    adapter = get_platform_runtime_adapter(HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE, platform_id="longbridge")

    assert adapter.available_inputs == frozenset({"market_history", "portfolio_snapshot"})
    assert adapter.portfolio_input_name == "portfolio_snapshot"


def test_global_etf_rotation_runtime_requirements_are_direct_inputs():
    requirements = describe_platform_runtime_requirements(
        HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE,
        platform_id="longbridge",
    )

    assert requirements["profile_group"] == "direct_runtime_inputs"
    assert requirements["input_mode"] == "market_history"
    assert requirements["requires_snapshot_artifacts"] is False
    assert requirements["requires_snapshot_manifest_path"] is False


def test_high_dividend_low_vol_trend_runtime_adapter_uses_market_history():
    adapter = get_platform_runtime_adapter(HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE, platform_id="ibkr")

    assert adapter.available_inputs == frozenset({"market_history"})
    assert adapter.available_capabilities == frozenset({"broker_client"})
    assert adapter.require_snapshot_manifest is False


def test_high_dividend_low_vol_trend_longbridge_adapter_adds_portfolio_for_value_native_platform():
    adapter = get_platform_runtime_adapter(HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE, platform_id="longbridge")

    assert adapter.available_inputs == frozenset({"market_history", "portfolio_snapshot"})
    assert adapter.portfolio_input_name == "portfolio_snapshot"


def test_low_vol_dividend_quality_runtime_adapter_requires_feature_snapshot_manifest():
    adapter = get_platform_runtime_adapter(HK_LOW_VOL_DIVIDEND_QUALITY_PROFILE, platform_id="ibkr")

    assert adapter.available_inputs == frozenset({"feature_snapshot"})
    assert adapter.available_capabilities == frozenset({"broker_client"})
    assert adapter.require_snapshot_manifest is True
    assert adapter.snapshot_contract_version == "hk_low_vol_dividend_quality.factor_snapshot.v1"
    assert "dividend_yield_net" in adapter.required_feature_columns
    assert "realized_vol_126" in adapter.required_feature_columns


def test_low_vol_dividend_quality_longbridge_adapter_adds_portfolio_for_value_native_platform():
    adapter = get_platform_runtime_adapter(HK_LOW_VOL_DIVIDEND_QUALITY_PROFILE, platform_id="longbridge")

    assert adapter.available_inputs == frozenset({"feature_snapshot", "portfolio_snapshot"})
    assert adapter.portfolio_input_name == "portfolio_snapshot"


def test_low_vol_dividend_quality_runtime_requirements_are_snapshot_backed():
    requirements = describe_platform_runtime_requirements(
        HK_LOW_VOL_DIVIDEND_QUALITY_PROFILE,
        platform_id="longbridge",
    )

    assert requirements["profile_group"] == "snapshot_backed"
    assert requirements["input_mode"] == "feature_snapshot"
    assert requirements["requires_snapshot_artifacts"] is True
    assert requirements["requires_snapshot_manifest_path"] is True


@pytest.mark.parametrize(
    "profile",
    [
        "hk_blue_chip_leader_rotation",
        "hk_index_mean_reversion",
        "hk_etf_regime_rotation",
    ],
)
def test_research_and_snapshot_scaffold_profiles_have_no_runtime_adapter(profile: str):
    with pytest.raises(ValueError):
        get_platform_runtime_adapter(profile, platform_id="ibkr")
