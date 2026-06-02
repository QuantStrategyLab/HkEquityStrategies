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

from hk_equity_strategies.strategies import hk_high_dividend_low_vol_trend as high_dividend_strategy
from hk_equity_strategies.strategies import hk_listed_global_etf_rotation as global_etf_strategy

HK_EQUITY_DOMAIN = global_etf_strategy.HK_EQUITY_DOMAIN
HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE = global_etf_strategy.PROFILE_NAME
HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE = high_dividend_strategy.PROFILE_NAME

HK_DIRECT_MARKET_HISTORY_PROFILES = frozenset(
    {
        HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE,
        HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE,
    }
)
HK_SNAPSHOT_BACKED_PROFILES = frozenset()
HK_EXTERNAL_SNAPSHOT_SCAFFOLD_PROFILES = frozenset(
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
HK_RESEARCH_BACKTEST_ONLY_PROFILES = frozenset(
    {
        "hk_index_mean_reversion",
        "hk_etf_regime_rotation",
    }
)

STRATEGY_PLATFORM_COMPATIBILITY: dict[str, frozenset[str]] = {
    HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE: frozenset({"ibkr", "longbridge"}),
    HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE: frozenset({"ibkr", "longbridge"}),
}

STRATEGY_REQUIRED_INPUTS: dict[str, frozenset[str]] = {
    HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE: frozenset({"market_history"}),
    HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE: frozenset({"market_history"}),
}

STRATEGY_DEFAULT_CONFIG: dict[str, dict[str, object]] = {
    HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE: {
        "universe_symbols": global_etf_strategy.DEFAULT_UNIVERSE_SYMBOLS,
        "momentum_window_days": global_etf_strategy.DEFAULT_MOMENTUM_WINDOW_DAYS,
        "trend_window_days": global_etf_strategy.DEFAULT_TREND_WINDOW_DAYS,
        "volatility_window_days": global_etf_strategy.DEFAULT_VOLATILITY_WINDOW_DAYS,
        "top_n": global_etf_strategy.DEFAULT_TOP_N,
        "min_momentum": global_etf_strategy.DEFAULT_MIN_MOMENTUM,
        "rebalance_frequency": global_etf_strategy.DEFAULT_REBALANCE_FREQUENCY,
        "weighting_mode": global_etf_strategy.DEFAULT_WEIGHTING_MODE,
        "target_annual_volatility": global_etf_strategy.DEFAULT_TARGET_ANNUAL_VOLATILITY,
        "max_gross_exposure": global_etf_strategy.DEFAULT_MAX_GROSS_EXPOSURE,
        "min_history_days": global_etf_strategy.DEFAULT_MIN_HISTORY_DAYS,
        "execution_cash_reserve_ratio": global_etf_strategy.DEFAULT_EXECUTION_CASH_RESERVE_RATIO,
    },
    HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE: {
        "universe_symbols": high_dividend_strategy.DEFAULT_UNIVERSE_SYMBOLS,
        "momentum_window_days": high_dividend_strategy.DEFAULT_MOMENTUM_WINDOW_DAYS,
        "trend_window_days": high_dividend_strategy.DEFAULT_TREND_WINDOW_DAYS,
        "volatility_window_days": high_dividend_strategy.DEFAULT_VOLATILITY_WINDOW_DAYS,
        "top_n": high_dividend_strategy.DEFAULT_TOP_N,
        "min_momentum": high_dividend_strategy.DEFAULT_MIN_MOMENTUM,
        "rebalance_frequency": high_dividend_strategy.DEFAULT_REBALANCE_FREQUENCY,
        "weighting_mode": high_dividend_strategy.DEFAULT_WEIGHTING_MODE,
        "target_annual_volatility": high_dividend_strategy.DEFAULT_TARGET_ANNUAL_VOLATILITY,
        "max_gross_exposure": high_dividend_strategy.DEFAULT_MAX_GROSS_EXPOSURE,
        "min_history_days": high_dividend_strategy.DEFAULT_MIN_HISTORY_DAYS,
        "execution_cash_reserve_ratio": high_dividend_strategy.DEFAULT_EXECUTION_CASH_RESERVE_RATIO,
    },
}

STRATEGY_ENTRYPOINT_ATTRIBUTES: dict[str, str] = {
    HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE: "hk_listed_global_etf_rotation_entrypoint",
    HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE: "hk_high_dividend_low_vol_trend_entrypoint",
}

STRATEGY_TARGET_MODES: dict[str, str] = {
    HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE: "weight",
    HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE: "weight",
}


# `supported_platforms` is a structural compatibility mirror only. Platform repositories
# own actual selectable/enabled status, and should only expose runtime-enabled profiles.
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
    HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE: _build_strategy_definition(
        HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE,
        component_name="signal_logic",
        module_path="hk_equity_strategies.strategies.hk_listed_global_etf_rotation",
    ),
    HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE: _build_strategy_definition(
        HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE,
        component_name="signal_logic",
        module_path="hk_equity_strategies.strategies.hk_high_dividend_low_vol_trend",
    ),
}

STRATEGY_METADATA: dict[str, StrategyMetadata] = {
    HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE: StrategyMetadata(
        canonical_profile=HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE,
        display_name="HK-listed Global ETF Rotation",
        description=(
            "Runtime-enabled volatility-targeted rotation across HK-listed local, global equity, "
            "gold, and crude-oil ETFs using daily market history."
        ),
        aliases=("hk_global_etf_rotation", "hk_listed_global_rotation"),
        cadence="monthly review",
        asset_scope="hk_listed_global_etfs",
        benchmark="02800",
        role="hk_non_snapshot_global_etf_rotation",
        status="runtime_enabled",
    ),
    HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE: StrategyMetadata(
        canonical_profile=HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE,
        display_name="HK High Dividend Low-Volatility Trend",
        description=(
            "Runtime-enabled monthly trend rotation between HK-listed high-dividend and gold ETFs "
            "with a 12% annual volatility target."
        ),
        aliases=("hk_high_dividend_trend", "hk_hd_gold_trend", "hk_high_dividend_low_vol"),
        cadence="monthly review",
        asset_scope="hk_high_dividend_gold_etfs",
        benchmark="03110",
        role="hk_non_snapshot_high_dividend_low_vol_trend",
        status="runtime_enabled",
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


def get_direct_market_history_profiles() -> frozenset[str]:
    return HK_DIRECT_MARKET_HISTORY_PROFILES


def get_snapshot_backed_profiles() -> frozenset[str]:
    return HK_SNAPSHOT_BACKED_PROFILES


def get_external_snapshot_scaffold_profiles() -> frozenset[str]:
    return HK_EXTERNAL_SNAPSHOT_SCAFFOLD_PROFILES


def get_research_backtest_only_profiles() -> frozenset[str]:
    return HK_RESEARCH_BACKTEST_ONLY_PROFILES


def get_strategy_metadata(profile: str) -> StrategyMetadata:
    return get_catalog_strategy_metadata(STRATEGY_CATALOG, profile)


def get_profile_aliases() -> dict[str, str]:
    return dict(PROFILE_ALIASES)
