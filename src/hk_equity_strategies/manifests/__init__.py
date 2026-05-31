from __future__ import annotations

from quant_platform_kit.strategy_contracts import StrategyManifest

from hk_equity_strategies.strategies import blue_chip_leader_rotation as strategy

HK_BLUE_CHIP_LEADER_ROTATION_PROFILE = strategy.PROFILE_NAME


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
        domain=strategy.HK_EQUITY_DOMAIN,
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
        "benchmark_symbol": strategy.BENCHMARK_SYMBOL,
        "broad_benchmark_symbol": strategy.BROAD_BENCHMARK_SYMBOL,
        "safe_haven": strategy.SAFE_HAVEN,
        "dynamic_universe_size": strategy.DEFAULT_DYNAMIC_UNIVERSE_SIZE,
        "holdings_count": strategy.DEFAULT_HOLDINGS_COUNT,
        "single_name_cap": strategy.DEFAULT_SINGLE_NAME_CAP,
        "min_position_value_hkd": strategy.DEFAULT_MIN_POSITION_VALUE_HKD,
        "hold_buffer": strategy.DEFAULT_HOLD_BUFFER,
        "hold_bonus": strategy.DEFAULT_HOLD_BONUS,
        "risk_on_exposure": strategy.DEFAULT_RISK_ON_EXPOSURE,
        "soft_defense_exposure": strategy.DEFAULT_SOFT_DEFENSE_EXPOSURE,
        "hard_defense_exposure": strategy.DEFAULT_HARD_DEFENSE_EXPOSURE,
        "soft_breadth_threshold": strategy.DEFAULT_SOFT_BREADTH_THRESHOLD,
        "hard_breadth_threshold": strategy.DEFAULT_HARD_BREADTH_THRESHOLD,
        "min_adv20_hkd": strategy.DEFAULT_MIN_ADV20_HKD,
        "runtime_execution_window_trading_days": strategy.DEFAULT_RUNTIME_EXECUTION_WINDOW_TRADING_DAYS,
        "execution_cash_reserve_ratio": strategy.DEFAULT_EXECUTION_CASH_RESERVE_RATIO,
    },
)

MANIFESTS = {
    hk_blue_chip_leader_rotation_manifest.profile: hk_blue_chip_leader_rotation_manifest,
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
    "MANIFESTS",
    "get_strategy_manifest",
    "hk_blue_chip_leader_rotation_manifest",
]
