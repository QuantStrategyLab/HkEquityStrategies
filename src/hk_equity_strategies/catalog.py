from __future__ import annotations

from quant_platform_kit.common.strategies import (
    StrategyCatalog,
    StrategyComponentDefinition,
    StrategyDefinition,
    StrategyEntrypointDefinition,
    StrategyMetadata,
    build_strategy_catalog,
    build_strategy_index_rows,
    get_catalog_compatible_platforms,
    get_catalog_strategy_definition,
    get_catalog_strategy_metadata,
    load_strategy_entrypoint,
    normalize_profile_name as qpk_normalize_profile_name,
)

from hk_equity_strategies.strategies import blue_chip_leader_rotation as blue_chip_strategy
from hk_equity_strategies.strategies import hk_index_mean_reversion as index_mr_strategy

HK_EQUITY_DOMAIN = blue_chip_strategy.HK_EQUITY_DOMAIN
HK_BLUE_CHIP_LEADER_ROTATION_PROFILE = blue_chip_strategy.PROFILE_NAME
HK_INDEX_MEAN_REVERSION_PROFILE = index_mr_strategy.PROFILE_NAME

STRATEGY_PLATFORM_COMPATIBILITY: dict[str, frozenset[str]] = {
    HK_BLUE_CHIP_LEADER_ROTATION_PROFILE: frozenset({"ibkr", "longbridge"}),
    HK_INDEX_MEAN_REVERSION_PROFILE: frozenset({"ibkr", "longbridge"}),
}

STRATEGY_REQUIRED_INPUTS: dict[str, frozenset[str]] = {
    HK_BLUE_CHIP_LEADER_ROTATION_PROFILE: frozenset({"feature_snapshot"}),
    HK_INDEX_MEAN_REVERSION_PROFILE: frozenset({"market_history"}),
}

STRATEGY_DEFAULT_CONFIG: dict[str, dict[str, object]] = {
    HK_BLUE_CHIP_LEADER_ROTATION_PROFILE: {
        "benchmark_symbol": blue_chip_strategy.BENCHMARK_SYMBOL,
        "broad_benchmark_symbol": blue_chip_strategy.BROAD_BENCHMARK_SYMBOL,
        "safe_haven": blue_chip_strategy.SAFE_HAVEN,
        "dynamic_universe_size": blue_chip_strategy.DEFAULT_DYNAMIC_UNIVERSE_SIZE,
        "holdings_count": blue_chip_strategy.DEFAULT_HOLDINGS_COUNT,
        "single_name_cap": blue_chip_strategy.DEFAULT_SINGLE_NAME_CAP,
        "min_position_value_hkd": blue_chip_strategy.DEFAULT_MIN_POSITION_VALUE_HKD,
        "hold_buffer": blue_chip_strategy.DEFAULT_HOLD_BUFFER,
        "hold_bonus": blue_chip_strategy.DEFAULT_HOLD_BONUS,
        "risk_on_exposure": blue_chip_strategy.DEFAULT_RISK_ON_EXPOSURE,
        "soft_defense_exposure": blue_chip_strategy.DEFAULT_SOFT_DEFENSE_EXPOSURE,
        "hard_defense_exposure": blue_chip_strategy.DEFAULT_HARD_DEFENSE_EXPOSURE,
        "soft_breadth_threshold": blue_chip_strategy.DEFAULT_SOFT_BREADTH_THRESHOLD,
        "hard_breadth_threshold": blue_chip_strategy.DEFAULT_HARD_BREADTH_THRESHOLD,
        "min_adv20_hkd": blue_chip_strategy.DEFAULT_MIN_ADV20_HKD,
        "runtime_execution_window_trading_days": blue_chip_strategy.DEFAULT_RUNTIME_EXECUTION_WINDOW_TRADING_DAYS,
        "execution_cash_reserve_ratio": blue_chip_strategy.DEFAULT_EXECUTION_CASH_RESERVE_RATIO,
    },
    HK_INDEX_MEAN_REVERSION_PROFILE: {
        "anchor_symbol": index_mr_strategy.DEFAULT_ANCHOR_SYMBOL,
        "satellite_symbol": index_mr_strategy.DEFAULT_SATELLITE_SYMBOL,
        "lookback_days": index_mr_strategy.DEFAULT_LOOKBACK_DAYS,
        "entry_z": index_mr_strategy.DEFAULT_ENTRY_Z,
        "exit_z": index_mr_strategy.DEFAULT_EXIT_Z,
        "neutral_satellite_weight": index_mr_strategy.DEFAULT_NEUTRAL_SATELLITE_WEIGHT,
        "oversold_satellite_weight": index_mr_strategy.DEFAULT_OVERSOLD_SATELLITE_WEIGHT,
        "rich_satellite_weight": index_mr_strategy.DEFAULT_RICH_SATELLITE_WEIGHT,
        "trend_window_days": index_mr_strategy.DEFAULT_TREND_WINDOW_DAYS,
        "defensive_gross_exposure": index_mr_strategy.DEFAULT_DEFENSIVE_GROSS_EXPOSURE,
        "defensive_satellite_weight": index_mr_strategy.DEFAULT_DEFENSIVE_SATELLITE_WEIGHT,
        "min_history_days": index_mr_strategy.DEFAULT_MIN_HISTORY_DAYS,
        "rebalance_frequency": index_mr_strategy.DEFAULT_REBALANCE_FREQUENCY,
        "execution_cash_reserve_ratio": index_mr_strategy.DEFAULT_EXECUTION_CASH_RESERVE_RATIO,
    },
}

STRATEGY_ENTRYPOINT_ATTRIBUTES: dict[str, str] = {
    HK_BLUE_CHIP_LEADER_ROTATION_PROFILE: "hk_blue_chip_leader_rotation_entrypoint",
    HK_INDEX_MEAN_REVERSION_PROFILE: "hk_index_mean_reversion_entrypoint",
}

STRATEGY_TARGET_MODES: dict[str, str] = {
    HK_BLUE_CHIP_LEADER_ROTATION_PROFILE: "weight",
    HK_INDEX_MEAN_REVERSION_PROFILE: "weight",
}


def _build_strategy_definition(
    profile: str,
    *,
    component_name: str,
    module_path: str,
) -> StrategyDefinition:
    return StrategyDefinition(
        profile=profile,
        domain=HK_EQUITY_DOMAIN,
        supported_platforms=STRATEGY_PLATFORM_COMPATIBILITY[profile],
        components=(
            StrategyComponentDefinition(
                name=component_name,
                module_path=module_path,
            ),
        ),
        entrypoint=StrategyEntrypointDefinition(
            module_path="hk_equity_strategies.entrypoints",
            attribute_name=STRATEGY_ENTRYPOINT_ATTRIBUTES[profile],
        ),
        required_inputs=STRATEGY_REQUIRED_INPUTS[profile],
        default_config=STRATEGY_DEFAULT_CONFIG[profile],
        target_mode=STRATEGY_TARGET_MODES[profile],
    )


STRATEGY_DEFINITIONS: dict[str, StrategyDefinition] = {
    HK_BLUE_CHIP_LEADER_ROTATION_PROFILE: _build_strategy_definition(
        HK_BLUE_CHIP_LEADER_ROTATION_PROFILE,
        component_name="signal_logic",
        module_path="hk_equity_strategies.strategies.blue_chip_leader_rotation",
    ),
    HK_INDEX_MEAN_REVERSION_PROFILE: _build_strategy_definition(
        HK_INDEX_MEAN_REVERSION_PROFILE,
        component_name="signal_logic",
        module_path="hk_equity_strategies.strategies.hk_index_mean_reversion",
    ),
}

STRATEGY_METADATA: dict[str, StrategyMetadata] = {
    HK_BLUE_CHIP_LEADER_ROTATION_PROFILE: StrategyMetadata(
        canonical_profile=HK_BLUE_CHIP_LEADER_ROTATION_PROFILE,
        display_name="HK Blue Chip Leader Rotation",
        description=(
            "Architecture scaffold for a future Hong Kong blue-chip snapshot strategy; not runtime-enabled yet."
        ),
        aliases=("hk_blue_chip_snapshot", "hk_leader_rotation"),
        cadence="monthly snapshot",
        asset_scope="hk_blue_chip_stocks",
        benchmark="02800",
        role="hk_snapshot_leader_rotation",
        status="architecture_scaffold",
    ),
    HK_INDEX_MEAN_REVERSION_PROFILE: StrategyMetadata(
        canonical_profile=HK_INDEX_MEAN_REVERSION_PROFILE,
        display_name="HK Index Mean Reversion",
        description=(
            "Research candidate for long-only HSI/Hang Seng TECH ETF relative mean reversion "
            "using daily market history."
        ),
        aliases=("hk_hsi_hstech_mean_reversion", "hk_index_reversion"),
        cadence="weekly review",
        asset_scope="hk_index_etfs",
        benchmark="02800",
        role="hk_non_snapshot_index_mean_reversion",
        status="research_candidate",
    ),
}

PROFILE_ALIASES: dict[str, str] = {
    alias: metadata.canonical_profile
    for metadata in STRATEGY_METADATA.values()
    for alias in metadata.aliases
}

STRATEGY_CATALOG: StrategyCatalog = build_strategy_catalog(
    strategy_definitions=STRATEGY_DEFINITIONS,
    metadata=STRATEGY_METADATA,
    compatible_platforms=STRATEGY_PLATFORM_COMPATIBILITY,
    profile_aliases=PROFILE_ALIASES,
)


def normalize_profile_name(profile: str | None) -> str:
    return qpk_normalize_profile_name(profile).replace("-", "_")


def resolve_canonical_profile(profile: str | None) -> str:
    normalized = normalize_profile_name(profile)
    if not normalized:
        return normalized
    definition = get_catalog_strategy_definition(STRATEGY_CATALOG, normalized)
    return definition.profile


def get_strategy_definitions() -> dict[str, StrategyDefinition]:
    return dict(STRATEGY_DEFINITIONS)


def get_strategy_catalog() -> StrategyCatalog:
    return STRATEGY_CATALOG


def get_strategy_platform_compatibility_map() -> dict[str, frozenset[str]]:
    return dict(STRATEGY_PLATFORM_COMPATIBILITY)


def get_compatible_platforms(profile: str) -> frozenset[str]:
    return get_catalog_compatible_platforms(STRATEGY_CATALOG, profile)


def get_strategy_definition(profile: str) -> StrategyDefinition:
    return get_catalog_strategy_definition(STRATEGY_CATALOG, profile)


def get_strategy_entrypoint(profile: str):
    definition = get_strategy_definition(profile)
    metadata = get_strategy_metadata(profile)
    return load_strategy_entrypoint(definition, metadata=metadata)


def get_strategy_index_rows() -> list[dict[str, object]]:
    return build_strategy_index_rows(STRATEGY_CATALOG)


def get_strategy_metadata_map() -> dict[str, StrategyMetadata]:
    return dict(STRATEGY_METADATA)


def get_runtime_enabled_profiles() -> frozenset[str]:
    return frozenset(
        profile
        for profile, metadata in STRATEGY_METADATA.items()
        if str(metadata.status or "").strip().lower() == "runtime_enabled"
    )


def get_strategy_metadata(profile: str) -> StrategyMetadata:
    return get_catalog_strategy_metadata(STRATEGY_CATALOG, profile)


def get_profile_aliases() -> dict[str, str]:
    return dict(PROFILE_ALIASES)
