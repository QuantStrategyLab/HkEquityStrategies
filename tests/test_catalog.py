from __future__ import annotations

import pytest

from quant_platform_kit.common.strategies import get_strategy_component_map

from hk_equity_strategies import get_strategy_definitions
from hk_equity_strategies.catalog import (
    HK_EQUITY_DOMAIN,
    HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE,
    HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE,
    get_compatible_platforms,
    get_direct_market_history_profiles,
    get_external_snapshot_scaffold_profiles,
    get_profile_aliases,
    get_research_backtest_only_profiles,
    get_runtime_enabled_profiles,
    get_snapshot_backed_profiles,
    get_strategy_definition,
    get_strategy_metadata,
    resolve_canonical_profile,
)


def test_catalog_declares_runtime_enabled_hk_direct_strategies():
    catalog = get_strategy_definitions()
    assert set(catalog) == {
        HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE,
        HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE,
    }
    definition = catalog[HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE]

    assert definition.domain == HK_EQUITY_DOMAIN
    assert definition.required_inputs == frozenset({"market_history"})
    assert definition.target_mode == "weight"
    assert get_compatible_platforms(HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE) == frozenset({"ibkr", "longbridge"})
    assert get_strategy_metadata(HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE).status == "runtime_enabled"
    assert HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE in get_runtime_enabled_profiles()
    assert get_profile_aliases()["hk_global_etf_rotation"] == HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE

    component_map = get_strategy_component_map(definition)
    assert component_map["signal_logic"].module_path == (
        "hk_equity_strategies.strategies.hk_listed_global_etf_rotation"
    )

    high_dividend_definition = catalog[HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE]
    assert high_dividend_definition.domain == HK_EQUITY_DOMAIN
    assert high_dividend_definition.required_inputs == frozenset({"market_history"})
    assert high_dividend_definition.target_mode == "weight"
    assert get_compatible_platforms(HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE) == frozenset({"ibkr", "longbridge"})
    assert get_strategy_metadata(HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE).status == "runtime_enabled"
    assert HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE in get_runtime_enabled_profiles()
    assert get_profile_aliases()["hk_hd_gold_trend"] == HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE

    high_dividend_component_map = get_strategy_component_map(high_dividend_definition)
    assert high_dividend_component_map["signal_logic"].module_path == (
        "hk_equity_strategies.strategies.hk_high_dividend_low_vol_trend"
    )


def test_profile_groups_keep_runtime_research_and_snapshot_scaffolds_separate():
    assert get_direct_market_history_profiles() == frozenset(
        {
            HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE,
            HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE,
        }
    )
    assert get_snapshot_backed_profiles() == frozenset()
    assert get_external_snapshot_scaffold_profiles() == frozenset(
        {
            "hk_ah_premium_relative_value",
            "hk_blue_chip_leader_rotation",
            "hk_central_soe_value_quality_select",
            "hk_composite_factor_quality_value_momentum",
            "hk_factor_mix_qvlm_risk_parity",
            "hk_free_cash_flow_quality",
            "hk_index_rebalance_event",
            "hk_liquid_momentum_quality",
            "hk_low_vol_dividend_quality",
            "hk_quality_growth_low_volatility",
            "hk_residual_momentum_quality",
            "hk_shareholder_yield_quality",
            "hk_southbound_flow_momentum",
        }
    )
    assert get_research_backtest_only_profiles() == frozenset(
        {
            "hk_index_mean_reversion",
            "hk_etf_regime_rotation",
        }
    )
    assert get_runtime_enabled_profiles() == frozenset(
        {
            HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE,
            HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE,
        }
    )
    assert get_research_backtest_only_profiles().isdisjoint(get_runtime_enabled_profiles())
    assert get_external_snapshot_scaffold_profiles().isdisjoint(get_runtime_enabled_profiles())


@pytest.mark.parametrize(
    "profile",
    [
        "hk_ah_premium_relative_value",
        "hk_blue_chip_leader_rotation",
        "hk_central_soe_value_quality_select",
        "hk_composite_factor_quality_value_momentum",
        "hk_factor_mix_qvlm_risk_parity",
        "hk_free_cash_flow_quality",
        "hk_index_rebalance_event",
        "hk_index_mean_reversion",
        "hk_liquid_momentum_quality",
        "hk_low_vol_dividend_quality",
        "hk_quality_growth_low_volatility",
        "hk_residual_momentum_quality",
        "hk_shareholder_yield_quality",
        "hk_southbound_flow_momentum",
        "hk_etf_regime_rotation",
        "hk_blue_chip_snapshot",
        "hk_index_reversion",
        "hk_etf_rotation",
    ],
)
def test_research_and_snapshot_scaffold_profiles_are_not_runtime_catalog_profiles(profile: str):
    with pytest.raises(ValueError):
        get_strategy_definition(profile)


def test_aliases_resolve_to_canonical_profile():
    assert resolve_canonical_profile("hk-global-etf-rotation") == HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE
    assert get_strategy_definition("hk_listed_global_rotation").profile == HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE
    assert resolve_canonical_profile("hk-hd-gold-trend") == HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE
    assert get_strategy_definition("hk_high_dividend_low_vol").profile == HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE
