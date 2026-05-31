from __future__ import annotations

from hk_equity_strategies.catalog import (
    HK_BLUE_CHIP_LEADER_ROTATION_PROFILE,
    HK_INDEX_MEAN_REVERSION_PROFILE,
    HK_ETF_REGIME_ROTATION_PROFILE,
)
from hk_equity_strategies.runtime_adapters import (
    describe_platform_runtime_requirements,
    get_platform_runtime_adapter,
)
from hk_equity_strategies.strategies.blue_chip_leader_rotation import (
    REQUIRED_FEATURE_COLUMNS,
    SNAPSHOT_CONTRACT_VERSION,
)


def test_ibkr_runtime_adapter_uses_snapshot_and_broker_client():
    adapter = get_platform_runtime_adapter(HK_BLUE_CHIP_LEADER_ROTATION_PROFILE, platform_id="ibkr")

    assert adapter.available_inputs == frozenset({"feature_snapshot"})
    assert adapter.available_capabilities == frozenset({"broker_client"})
    assert adapter.required_feature_columns == REQUIRED_FEATURE_COLUMNS
    assert adapter.require_snapshot_manifest is True
    assert adapter.snapshot_contract_version == SNAPSHOT_CONTRACT_VERSION


def test_longbridge_runtime_adapter_adds_portfolio_for_value_native_platform():
    adapter = get_platform_runtime_adapter(HK_BLUE_CHIP_LEADER_ROTATION_PROFILE, platform_id="longbridge")

    assert adapter.available_inputs == frozenset({"feature_snapshot", "portfolio_snapshot"})
    assert adapter.portfolio_input_name == "portfolio_snapshot"


def test_runtime_requirements_match_snapshot_contract():
    requirements = describe_platform_runtime_requirements(
        HK_BLUE_CHIP_LEADER_ROTATION_PROFILE,
        platform_id="longbridge",
    )

    assert requirements["profile_group"] == "snapshot_backed"
    assert requirements["input_mode"] == "feature_snapshot"
    assert requirements["requires_snapshot_artifacts"] is True
    assert requirements["requires_snapshot_manifest_path"] is True
    assert requirements["requires_strategy_config_path"] is False


def test_index_mean_reversion_runtime_adapter_uses_market_history():
    adapter = get_platform_runtime_adapter(HK_INDEX_MEAN_REVERSION_PROFILE, platform_id="ibkr")

    assert adapter.available_inputs == frozenset({"market_history"})
    assert adapter.available_capabilities == frozenset({"broker_client"})
    assert adapter.require_snapshot_manifest is False


def test_index_mean_reversion_runtime_requirements_are_direct_inputs():
    requirements = describe_platform_runtime_requirements(HK_INDEX_MEAN_REVERSION_PROFILE, platform_id="longbridge")

    assert requirements["profile_group"] == "direct_runtime_inputs"
    assert requirements["input_mode"] == "market_history"
    assert requirements["requires_snapshot_artifacts"] is False
    assert requirements["requires_snapshot_manifest_path"] is False


def test_etf_regime_rotation_runtime_adapter_uses_market_history():
    adapter = get_platform_runtime_adapter(HK_ETF_REGIME_ROTATION_PROFILE, platform_id="ibkr")

    assert adapter.available_inputs == frozenset({"market_history"})
    assert adapter.available_capabilities == frozenset({"broker_client"})
    assert adapter.require_snapshot_manifest is False


def test_etf_regime_rotation_runtime_requirements_are_direct_inputs():
    requirements = describe_platform_runtime_requirements(HK_ETF_REGIME_ROTATION_PROFILE, platform_id="longbridge")

    assert requirements["profile_group"] == "direct_runtime_inputs"
    assert requirements["input_mode"] == "market_history"
    assert requirements["requires_snapshot_artifacts"] is False
    assert requirements["requires_snapshot_manifest_path"] is False
