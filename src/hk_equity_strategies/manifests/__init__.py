from __future__ import annotations

from quant_platform_kit.strategy_contracts import StrategyManifest

from hk_equity_strategies.strategies import hk_dividend_gold_defensive_rotation as high_dividend_strategy
from hk_equity_strategies.strategies import hk_global_etf_tactical_rotation as global_etf_strategy
from hk_equity_strategies.strategies import hk_low_vol_dividend_quality_snapshot as low_vol_dividend_strategy

HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE = global_etf_strategy.PROFILE_NAME
HK_DIVIDEND_GOLD_DEFENSIVE_ROTATION_PROFILE = high_dividend_strategy.PROFILE_NAME
HK_LOW_VOL_DIVIDEND_QUALITY_SNAPSHOT_PROFILE = low_vol_dividend_strategy.PROFILE_NAME


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


hk_global_etf_tactical_rotation_manifest = _manifest(
    profile=HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE,
    display_name="HK Global ETF Tactical Rotation",
    description=(
        "Monthly volatility-targeted rotation across HK-listed local, global equity, "
        "gold, and crude-oil ETFs using daily market history."
    ),
    aliases=(),
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

hk_dividend_gold_defensive_rotation_manifest = _manifest(
    profile=HK_DIVIDEND_GOLD_DEFENSIVE_ROTATION_PROFILE,
    display_name="HK Dividend-Gold Defensive Rotation",
    description=(
        "Monthly trend rotation between HK-listed high-dividend and gold ETFs "
        "with a 12% annual volatility target."
    ),
    aliases=(),
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

hk_low_vol_dividend_quality_snapshot_manifest = _manifest(
    profile=HK_LOW_VOL_DIVIDEND_QUALITY_SNAPSHOT_PROFILE,
    display_name="HK Low-Vol Dividend Quality Snapshot",
    description=(
        "Snapshot-backed monthly single-name HK equity selector using low-volatility, "
        "sustainable dividend, quality, and trend controls."
    ),
    aliases=(),
    required_inputs=frozenset({"feature_snapshot"}),
    default_config={
        "safe_haven": low_vol_dividend_strategy.SAFE_HAVEN,
        "holdings_count": low_vol_dividend_strategy.DEFAULT_HOLDINGS_COUNT,
        "single_name_cap": low_vol_dividend_strategy.DEFAULT_SINGLE_NAME_CAP,
        "sector_cap": low_vol_dividend_strategy.DEFAULT_SECTOR_CAP,
        "min_adv20_hkd": low_vol_dividend_strategy.DEFAULT_MIN_ADV20_HKD,
        "min_market_cap_hkd": low_vol_dividend_strategy.DEFAULT_MIN_MARKET_CAP_HKD,
        "min_dividend_yield": low_vol_dividend_strategy.DEFAULT_MIN_DIVIDEND_YIELD,
        "max_dividend_yield": low_vol_dividend_strategy.DEFAULT_MAX_DIVIDEND_YIELD,
        "min_dividend_stability": low_vol_dividend_strategy.DEFAULT_MIN_DIVIDEND_STABILITY,
        "max_payout_ratio": low_vol_dividend_strategy.DEFAULT_MAX_PAYOUT_RATIO,
        "max_suspension_days_63": low_vol_dividend_strategy.DEFAULT_MAX_SUSPENSION_DAYS_63,
        "hold_buffer": low_vol_dividend_strategy.DEFAULT_HOLD_BUFFER,
        "hold_bonus": low_vol_dividend_strategy.DEFAULT_HOLD_BONUS,
        "risk_on_exposure": low_vol_dividend_strategy.DEFAULT_RISK_ON_EXPOSURE,
        "soft_defense_exposure": low_vol_dividend_strategy.DEFAULT_SOFT_DEFENSE_EXPOSURE,
        "hard_defense_exposure": low_vol_dividend_strategy.DEFAULT_HARD_DEFENSE_EXPOSURE,
        "soft_breadth_threshold": low_vol_dividend_strategy.DEFAULT_SOFT_BREADTH_THRESHOLD,
        "hard_breadth_threshold": low_vol_dividend_strategy.DEFAULT_HARD_BREADTH_THRESHOLD,
        "execution_cash_reserve_ratio": low_vol_dividend_strategy.DEFAULT_EXECUTION_CASH_RESERVE_RATIO,
        "rebalance_frequency": "monthly",
    },
)

MANIFESTS = {
    hk_global_etf_tactical_rotation_manifest.profile: hk_global_etf_tactical_rotation_manifest,
    hk_dividend_gold_defensive_rotation_manifest.profile: hk_dividend_gold_defensive_rotation_manifest,
    hk_low_vol_dividend_quality_snapshot_manifest.profile: hk_low_vol_dividend_quality_snapshot_manifest,
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
    "HK_DIVIDEND_GOLD_DEFENSIVE_ROTATION_PROFILE",
    "HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE",
    "HK_LOW_VOL_DIVIDEND_QUALITY_SNAPSHOT_PROFILE",
    "MANIFESTS",
    "get_strategy_manifest",
    "hk_dividend_gold_defensive_rotation_manifest",
    "hk_global_etf_tactical_rotation_manifest",
    "hk_low_vol_dividend_quality_snapshot_manifest",
]
