from __future__ import annotations

from quant_platform_kit.strategy_contracts import StrategyManifest

from hk_equity_strategies.strategies import hk_high_dividend_low_vol_trend as high_dividend_strategy
from hk_equity_strategies.strategies import hk_listed_global_etf_rotation as global_etf_strategy

HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE = global_etf_strategy.PROFILE_NAME
HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE = high_dividend_strategy.PROFILE_NAME


def _manifest(
    *,
    profile: str,
    display_name: str,
    description: str,
    aliases: tuple[str, ...] = (),
    required_inputs: frozenset[str] = frozenset(),
    default_config: dict[str, object] | None = None,
) -> StrategyManifest:
    return StrategyManifest(
        profile=profile,
        domain=global_etf_strategy.HK_EQUITY_DOMAIN,
        display_name=display_name,
        description=description,
        aliases=aliases,
        required_inputs=required_inputs,
        default_config=default_config or {},
    )


hk_listed_global_etf_rotation_manifest = _manifest(
    profile=HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE,
    display_name="HK-listed Global ETF Rotation",
    description=(
        "Monthly volatility-targeted rotation across HK-listed local, global equity, "
        "gold, and crude-oil ETFs using daily market history."
    ),
    aliases=("hk_global_etf_rotation", "hk_listed_global_rotation"),
    required_inputs=frozenset({"market_history"}),
    default_config={
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
)

hk_high_dividend_low_vol_trend_manifest = _manifest(
    profile=HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE,
    display_name="HK High Dividend Low-Volatility Trend",
    description=(
        "Monthly trend rotation between HK-listed high-dividend and gold ETFs "
        "with a 12% annual volatility target."
    ),
    aliases=("hk_high_dividend_trend", "hk_hd_gold_trend", "hk_high_dividend_low_vol"),
    required_inputs=frozenset({"market_history"}),
    default_config={
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
)

MANIFESTS = {
    hk_listed_global_etf_rotation_manifest.profile: hk_listed_global_etf_rotation_manifest,
    hk_high_dividend_low_vol_trend_manifest.profile: hk_high_dividend_low_vol_trend_manifest,
}

MANIFEST_ALIASES = {
    str(alias).strip().lower(): manifest.profile
    for manifest in MANIFESTS.values()
    for alias in manifest.aliases
}


def get_strategy_manifest(profile: str) -> StrategyManifest:
    normalized = str(profile or "").strip().lower().replace("-", "_")
    return MANIFESTS[MANIFEST_ALIASES.get(normalized, normalized)]


__all__ = [
    "HK_HIGH_DIVIDEND_LOW_VOL_TREND_PROFILE",
    "HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE",
    "MANIFESTS",
    "get_strategy_manifest",
    "hk_high_dividend_low_vol_trend_manifest",
    "hk_listed_global_etf_rotation_manifest",
]
