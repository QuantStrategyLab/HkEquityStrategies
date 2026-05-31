from __future__ import annotations

from quant_platform_kit.common.strategies import get_strategy_component_map

from hk_equity_strategies import get_strategy_definitions
from hk_equity_strategies.catalog import (
    HK_BLUE_CHIP_LEADER_ROTATION_PROFILE,
    HK_EQUITY_DOMAIN,
    get_compatible_platforms,
    get_profile_aliases,
    get_strategy_definition,
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
    assert get_strategy_metadata(HK_BLUE_CHIP_LEADER_ROTATION_PROFILE).status == "runtime_enabled"
    assert get_profile_aliases()["hk_blue_chip_snapshot"] == HK_BLUE_CHIP_LEADER_ROTATION_PROFILE

    component_map = get_strategy_component_map(definition)
    assert component_map["signal_logic"].module_path == "hk_equity_strategies.strategies.blue_chip_leader_rotation"


def test_aliases_resolve_to_canonical_profile():
    assert resolve_canonical_profile("hk-blue-chip-snapshot") == HK_BLUE_CHIP_LEADER_ROTATION_PROFILE
    assert get_strategy_definition("hk_leader_rotation").profile == HK_BLUE_CHIP_LEADER_ROTATION_PROFILE
