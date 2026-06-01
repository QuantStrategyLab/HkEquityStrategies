"""Hong Kong equity non-snapshot strategy catalog and runtime adapters."""

__all__ = [
    "HK_EQUITY_DOMAIN",
    "HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE",
    "HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE",
    "HK_DIRECT_MARKET_HISTORY_PROFILES",
    "HK_RESEARCH_BACKTEST_ONLY_PROFILES",
    "HK_SNAPSHOT_BACKED_PROFILES",
    "STRATEGY_CATALOG",
    "STRATEGY_DEFINITIONS",
    "build_hk_runtime_readiness",
    "get_compatible_platforms",
    "get_direct_market_history_profiles",
    "get_platform_runtime_adapter",
    "get_profile_aliases",
    "get_research_backtest_only_profiles",
    "get_runtime_enabled_profiles",
    "get_snapshot_backed_profiles",
    "get_strategy_catalog",
    "get_strategy_definition",
    "get_strategy_definitions",
    "get_strategy_entrypoint",
    "get_strategy_index_rows",
    "get_strategy_metadata",
    "get_strategy_metadata_map",
    "get_strategy_platform_compatibility_map",
    "resolve_canonical_profile",
]


def __getattr__(name: str):
    if name in {
        "HK_EQUITY_DOMAIN",
        "HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE",
        "HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE",
        "HK_DIRECT_MARKET_HISTORY_PROFILES",
        "HK_RESEARCH_BACKTEST_ONLY_PROFILES",
        "HK_SNAPSHOT_BACKED_PROFILES",
        "STRATEGY_CATALOG",
        "STRATEGY_DEFINITIONS",
        "get_compatible_platforms",
        "get_direct_market_history_profiles",
        "get_profile_aliases",
        "get_research_backtest_only_profiles",
        "get_runtime_enabled_profiles",
        "get_snapshot_backed_profiles",
        "get_strategy_catalog",
        "get_strategy_definition",
        "get_strategy_definitions",
        "get_strategy_entrypoint",
        "get_strategy_index_rows",
        "get_strategy_metadata",
        "get_strategy_metadata_map",
        "get_strategy_platform_compatibility_map",
        "resolve_canonical_profile",
    }:
        from . import catalog as _catalog

        return getattr(_catalog, name)
    if name == "get_platform_runtime_adapter":
        from .runtime_adapters import get_platform_runtime_adapter as _get_platform_runtime_adapter

        return _get_platform_runtime_adapter
    if name == "build_hk_runtime_readiness":
        from .runtime_readiness import build_hk_runtime_readiness as _build_hk_runtime_readiness

        return _build_hk_runtime_readiness
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
