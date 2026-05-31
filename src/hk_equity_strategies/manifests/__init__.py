from __future__ import annotations

from quant_platform_kit.strategy_contracts import StrategyManifest

from hk_equity_strategies.strategies import blue_chip_leader_rotation as blue_chip_strategy
from hk_equity_strategies.strategies import hk_etf_regime_rotation as etf_rotation_strategy
from hk_equity_strategies.strategies import hk_index_mean_reversion as index_mr_strategy
from hk_equity_strategies.strategies import hk_listed_global_etf_rotation as global_etf_strategy

HK_BLUE_CHIP_LEADER_ROTATION_PROFILE = blue_chip_strategy.PROFILE_NAME
HK_INDEX_MEAN_REVERSION_PROFILE = index_mr_strategy.PROFILE_NAME
HK_ETF_REGIME_ROTATION_PROFILE = etf_rotation_strategy.PROFILE_NAME
HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE = global_etf_strategy.PROFILE_NAME


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
        domain=blue_chip_strategy.HK_EQUITY_DOMAIN,
        display_name=display_name,
        description=description,
        aliases=aliases,
        required_inputs=required_inputs,
        default_config=default_config or {},
    )


hk_blue_chip_leader_rotation_manifest = _manifest(
    profile=HK_BLUE_CHIP_LEADER_ROTATION_PROFILE,
    display_name="HK Blue Chip Leader Rotation",
    description="Monthly Hong Kong blue-chip leader rotation using feature snapshots and XHKG execution windows.",
    aliases=("hk_blue_chip_snapshot", "hk_leader_rotation"),
    required_inputs=frozenset({"feature_snapshot"}),
    default_config={
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
)

hk_index_mean_reversion_manifest = _manifest(
    profile=HK_INDEX_MEAN_REVERSION_PROFILE,
    display_name="HK Index Mean Reversion",
    description=(
        "Weekly long-only HSI/Hang Seng TECH ETF relative mean-reversion research candidate "
        "using daily market history."
    ),
    aliases=("hk_hsi_hstech_mean_reversion", "hk_index_reversion"),
    required_inputs=frozenset({"market_history"}),
    default_config={
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
)

hk_etf_regime_rotation_manifest = _manifest(
    profile=HK_ETF_REGIME_ROTATION_PROFILE,
    display_name="HK ETF Regime Rotation",
    description=(
        "Monthly low-turnover HK-listed ETF regime rotation research candidate "
        "using daily market history."
    ),
    aliases=("hk_etf_rotation", "hk_regime_rotation"),
    required_inputs=frozenset({"market_history"}),
    default_config={
        "universe_symbols": etf_rotation_strategy.DEFAULT_UNIVERSE_SYMBOLS,
        "momentum_window_days": etf_rotation_strategy.DEFAULT_MOMENTUM_WINDOW_DAYS,
        "trend_window_days": etf_rotation_strategy.DEFAULT_TREND_WINDOW_DAYS,
        "volatility_window_days": etf_rotation_strategy.DEFAULT_VOLATILITY_WINDOW_DAYS,
        "top_n": etf_rotation_strategy.DEFAULT_TOP_N,
        "min_momentum": etf_rotation_strategy.DEFAULT_MIN_MOMENTUM,
        "rebalance_frequency": etf_rotation_strategy.DEFAULT_REBALANCE_FREQUENCY,
        "weighting_mode": etf_rotation_strategy.DEFAULT_WEIGHTING_MODE,
        "target_annual_volatility": etf_rotation_strategy.DEFAULT_TARGET_ANNUAL_VOLATILITY,
        "max_gross_exposure": etf_rotation_strategy.DEFAULT_MAX_GROSS_EXPOSURE,
        "min_history_days": etf_rotation_strategy.DEFAULT_MIN_HISTORY_DAYS,
        "execution_cash_reserve_ratio": etf_rotation_strategy.DEFAULT_EXECUTION_CASH_RESERVE_RATIO,
    },
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

MANIFESTS = {
    hk_blue_chip_leader_rotation_manifest.profile: hk_blue_chip_leader_rotation_manifest,
    hk_index_mean_reversion_manifest.profile: hk_index_mean_reversion_manifest,
    hk_etf_regime_rotation_manifest.profile: hk_etf_regime_rotation_manifest,
    hk_listed_global_etf_rotation_manifest.profile: hk_listed_global_etf_rotation_manifest,
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
    "HK_BLUE_CHIP_LEADER_ROTATION_PROFILE",
    "HK_INDEX_MEAN_REVERSION_PROFILE",
    "HK_ETF_REGIME_ROTATION_PROFILE",
    "HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE",
    "MANIFESTS",
    "get_strategy_manifest",
    "hk_blue_chip_leader_rotation_manifest",
    "hk_index_mean_reversion_manifest",
    "hk_etf_regime_rotation_manifest",
    "hk_listed_global_etf_rotation_manifest",
]
