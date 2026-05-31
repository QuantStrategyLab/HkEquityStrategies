from __future__ import annotations

from quant_platform_kit.common.strategies import get_strategy_component_map

from hk_equity_strategies import get_strategy_definitions
from hk_equity_strategies.catalog import (
    HK_BLUE_CHIP_LEADER_ROTATION_PROFILE,
    HK_INDEX_MEAN_REVERSION_PROFILE,
    HK_ETF_REGIME_ROTATION_PROFILE,
    HK_EQUITY_DOMAIN,
    get_compatible_platforms,
    get_profile_aliases,
    get_strategy_definition,
    get_runtime_enabled_profiles,
    get_strategy_metadata,
    resolve_canonical_profile,
)


def test_catalog_declares_hk_snapshot_profile_for_ibkr_and_longbridge():
    catalog = get_strategy_definitions()
    definition = catalog[HK_BLUE_CHIP_LEADER_ROTATION_PROFILE]

    assert definition.domain == HK_EQUITY_DOMAIN
    assert definition.required_inputs == frozenset({"feature_snapshot"})
    assert definition.target_mode == "weight"
    assert get_compatible_platforms(HK_BLUE_CHIP_LEADER_ROTATION_PROFILE) == frozenset({"ibkr", "longbridge"})
    assert get_strategy_metadata(HK_BLUE_CHIP_LEADER_ROTATION_PROFILE).status == "architecture_scaffold"
    assert HK_BLUE_CHIP_LEADER_ROTATION_PROFILE not in get_runtime_enabled_profiles()
    assert get_profile_aliases()["hk_blue_chip_snapshot"] == HK_BLUE_CHIP_LEADER_ROTATION_PROFILE

    component_map = get_strategy_component_map(definition)
    assert component_map["signal_logic"].module_path == "hk_equity_strategies.strategies.blue_chip_leader_rotation"


def test_catalog_declares_hk_index_mean_reversion_research_candidate():
    catalog = get_strategy_definitions()
    definition = catalog[HK_INDEX_MEAN_REVERSION_PROFILE]

    assert definition.domain == HK_EQUITY_DOMAIN
    assert definition.required_inputs == frozenset({"market_history"})
    assert definition.target_mode == "weight"
    assert get_compatible_platforms(HK_INDEX_MEAN_REVERSION_PROFILE) == frozenset({"ibkr", "longbridge"})
    assert get_strategy_metadata(HK_INDEX_MEAN_REVERSION_PROFILE).status == "research_candidate"
    assert HK_INDEX_MEAN_REVERSION_PROFILE not in get_runtime_enabled_profiles()
    assert get_profile_aliases()["hk_index_reversion"] == HK_INDEX_MEAN_REVERSION_PROFILE

    component_map = get_strategy_component_map(definition)
    assert component_map["signal_logic"].module_path == "hk_equity_strategies.strategies.hk_index_mean_reversion"


def test_catalog_declares_hk_etf_regime_rotation_research_candidate():
    catalog = get_strategy_definitions()
    definition = catalog[HK_ETF_REGIME_ROTATION_PROFILE]

    assert definition.domain == HK_EQUITY_DOMAIN
    assert definition.required_inputs == frozenset({"market_history"})
    assert definition.target_mode == "weight"
    assert get_compatible_platforms(HK_ETF_REGIME_ROTATION_PROFILE) == frozenset({"ibkr", "longbridge"})
    assert get_strategy_metadata(HK_ETF_REGIME_ROTATION_PROFILE).status == "research_candidate"
    assert HK_ETF_REGIME_ROTATION_PROFILE not in get_runtime_enabled_profiles()
    assert get_profile_aliases()["hk_etf_rotation"] == HK_ETF_REGIME_ROTATION_PROFILE

    component_map = get_strategy_component_map(definition)
    assert component_map["signal_logic"].module_path == "hk_equity_strategies.strategies.hk_etf_regime_rotation"


def test_aliases_resolve_to_canonical_profile():
    assert resolve_canonical_profile("hk-blue-chip-snapshot") == HK_BLUE_CHIP_LEADER_ROTATION_PROFILE
    assert get_strategy_definition("hk_leader_rotation").profile == HK_BLUE_CHIP_LEADER_ROTATION_PROFILE
    assert resolve_canonical_profile("hk-hsi-hstech-mean-reversion") == HK_INDEX_MEAN_REVERSION_PROFILE
    assert resolve_canonical_profile("hk-etf-rotation") == HK_ETF_REGIME_ROTATION_PROFILE
