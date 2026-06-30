from __future__ import annotations

import pytest

from quant_platform_kit.common.strategies import get_strategy_component_map

from hk_equity_strategies import get_strategy_definitions
from hk_equity_strategies.catalog import (
    HK_EQUITY_COMBO_PROFILE,
    HK_EQUITY_DOMAIN,
    HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE,
    HK_LOW_VOL_DIVIDEND_QUALITY_SNAPSHOT_PROFILE,
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
        HK_EQUITY_COMBO_PROFILE,
        HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE,
        HK_LOW_VOL_DIVIDEND_QUALITY_SNAPSHOT_PROFILE,
    }
    definition = catalog[HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE]

    assert definition.domain == HK_EQUITY_DOMAIN
    assert definition.required_inputs == frozenset({"market_history"})
    assert definition.target_mode == "weight"
    assert get_compatible_platforms(HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE) == frozenset({"ibkr", "longbridge"})
    assert get_strategy_metadata(HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE).status == "runtime_enabled"
    assert HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE in get_runtime_enabled_profiles()

    component_map = get_strategy_component_map(definition)
    assert component_map["signal_logic"].module_path == (
        "hk_equity_strategies.strategies.hk_global_etf_tactical_rotation"
    )

    low_vol_definition = catalog[HK_LOW_VOL_DIVIDEND_QUALITY_SNAPSHOT_PROFILE]
    assert low_vol_definition.domain == HK_EQUITY_DOMAIN
    assert low_vol_definition.required_inputs == frozenset({"feature_snapshot"})
    assert low_vol_definition.target_mode == "weight"
    assert get_compatible_platforms(HK_LOW_VOL_DIVIDEND_QUALITY_SNAPSHOT_PROFILE) == frozenset({"ibkr", "longbridge"})
    assert get_strategy_metadata(HK_LOW_VOL_DIVIDEND_QUALITY_SNAPSHOT_PROFILE).status == "runtime_enabled"
    assert HK_LOW_VOL_DIVIDEND_QUALITY_SNAPSHOT_PROFILE in get_runtime_enabled_profiles()

    low_vol_component_map = get_strategy_component_map(low_vol_definition)
    assert low_vol_component_map["signal_logic"].module_path == (
        "hk_equity_strategies.strategies.hk_low_vol_dividend_quality_snapshot"
    )


def test_profile_groups_keep_runtime_research_and_snapshot_scaffolds_separate():
    assert get_direct_market_history_profiles() == frozenset(
        {
            HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE,
        }
    )
    assert get_snapshot_backed_profiles() == frozenset({HK_LOW_VOL_DIVIDEND_QUALITY_SNAPSHOT_PROFILE})
    assert get_external_snapshot_scaffold_profiles() == frozenset()
    assert get_research_backtest_only_profiles() == frozenset()
    assert get_runtime_enabled_profiles() == frozenset(
        {
            HK_EQUITY_COMBO_PROFILE,
            HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE,
            HK_LOW_VOL_DIVIDEND_QUALITY_SNAPSHOT_PROFILE,
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
        "hk_quality_growth_low_volatility",
        "hk_residual_momentum_quality",
        "hk_shareholder_yield_quality",
        "hk_southbound_flow_momentum",
        "hk_etf_regime_rotation",
        "hk_blue_chip_snapshot",
        "hk_index_reversion",
        "hk_etf_rotation",
        "hk_dividend_gold_defensive_rotation",
    ],
)
def test_research_and_snapshot_scaffold_profiles_are_not_runtime_catalog_profiles(profile: str):
    with pytest.raises(ValueError):
        get_strategy_definition(profile)


def test_canonical_profiles_resolve_without_legacy_aliases():
    assert get_profile_aliases() == {}
    assert resolve_canonical_profile("hk-global-etf-tactical-rotation") == HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE
    assert resolve_canonical_profile("hk-low-vol-dividend-quality-snapshot") == (
        HK_LOW_VOL_DIVIDEND_QUALITY_SNAPSHOT_PROFILE
    )


@pytest.mark.parametrize(
    "profile",
    [
        "hk_global_etf_rotation",
        "hk_listed_global_rotation",
        "hk_hd_gold_trend",
        "hk_dividend_gold_defensive_rotation",
        "hk-dividend-gold-defensive-rotation",
        "hk_high_dividend_low_vol",
        "hk_low_vol_dividend_snapshot",
        "hk_dividend_quality",
    ],
)
def test_legacy_aliases_are_not_preserved(profile: str):
    with pytest.raises(ValueError):
        get_strategy_definition(profile)
