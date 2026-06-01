from __future__ import annotations

import pytest

from quant_platform_kit.common.strategies import get_strategy_component_map

from hk_equity_strategies import get_strategy_definitions
from hk_equity_strategies.catalog import (
    HK_EQUITY_DOMAIN,
    HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE,
    get_compatible_platforms,
    get_direct_market_history_profiles,
    get_profile_aliases,
    get_research_backtest_only_profiles,
    get_runtime_enabled_profiles,
    get_snapshot_backed_profiles,
    get_strategy_definition,
    get_strategy_metadata,
    resolve_canonical_profile,
)


def test_catalog_declares_only_runtime_enabled_hk_direct_strategy():
    catalog = get_strategy_definitions()
    assert set(catalog) == {HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE}
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


def test_profile_groups_keep_runtime_research_and_snapshot_scaffolds_separate():
    assert get_direct_market_history_profiles() == frozenset({HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE})
    assert get_snapshot_backed_profiles() == frozenset()
    assert get_research_backtest_only_profiles() == frozenset(
        {
            "hk_index_mean_reversion",
            "hk_etf_regime_rotation",
        }
    )
    assert get_runtime_enabled_profiles() == frozenset({HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE})
    assert get_research_backtest_only_profiles().isdisjoint(get_runtime_enabled_profiles())


@pytest.mark.parametrize(
    "profile",
    [
        "hk_blue_chip_leader_rotation",
        "hk_index_mean_reversion",
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
