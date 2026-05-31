from __future__ import annotations

from quant_platform_kit.strategy_contracts import CallableStrategyEntrypoint, StrategyContext, StrategyDecision

from hk_equity_strategies.manifests import hk_blue_chip_leader_rotation_manifest
from hk_equity_strategies.strategies import blue_chip_leader_rotation as strategy

from ._common import get_current_holdings, merge_runtime_config, require_market_data, weights_to_positions


def evaluate_hk_blue_chip_leader_rotation(ctx: StrategyContext) -> StrategyDecision:
    config = merge_runtime_config(hk_blue_chip_leader_rotation_manifest.default_config, ctx)
    config.pop("execution_cash_reserve_ratio", None)
    if ctx.as_of is not None and "run_as_of" not in config:
        config["run_as_of"] = ctx.as_of
    if ctx.portfolio is not None and "portfolio_total_equity" not in config:
        total_equity = getattr(ctx.portfolio, "total_equity", None)
        if total_equity is not None:
            config["portfolio_total_equity"] = float(total_equity)
    weights, signal_desc, is_hard_defense, status_desc, metadata = strategy.compute_signals(
        require_market_data(ctx, "feature_snapshot"),
        get_current_holdings(ctx),
        **config,
    )
    diagnostics = {
        **metadata,
        "signal_description": signal_desc,
        "status_description": status_desc,
        "signal_source": strategy.SIGNAL_SOURCE,
        "actionable": weights is not None,
    }
    risk_flags: tuple[str, ...] = ()
    if is_hard_defense:
        risk_flags += ("hard_defense",)
    if weights is None:
        risk_flags += ("no_execute",)
    return StrategyDecision(
        positions=weights_to_positions(weights),
        risk_flags=risk_flags,
        diagnostics=diagnostics,
    )


hk_blue_chip_leader_rotation_entrypoint = CallableStrategyEntrypoint(
    manifest=hk_blue_chip_leader_rotation_manifest,
    _evaluate=evaluate_hk_blue_chip_leader_rotation,
)


__all__ = [
    "evaluate_hk_blue_chip_leader_rotation",
    "hk_blue_chip_leader_rotation_entrypoint",
]
