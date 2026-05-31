from __future__ import annotations

from quant_platform_kit.strategy_contracts import CallableStrategyEntrypoint, StrategyContext, StrategyDecision

from hk_equity_strategies.manifests import hk_blue_chip_leader_rotation_manifest, hk_index_mean_reversion_manifest
from hk_equity_strategies.strategies import blue_chip_leader_rotation as blue_chip_strategy
from hk_equity_strategies.strategies import hk_index_mean_reversion as index_mr_strategy

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
    weights, signal_desc, is_hard_defense, status_desc, metadata = blue_chip_strategy.compute_signals(
        require_market_data(ctx, "feature_snapshot"),
        get_current_holdings(ctx),
        **config,
    )
    diagnostics = {
        **metadata,
        "signal_description": signal_desc,
        "status_description": status_desc,
        "signal_source": blue_chip_strategy.SIGNAL_SOURCE,
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


def evaluate_hk_index_mean_reversion(ctx: StrategyContext) -> StrategyDecision:
    config = merge_runtime_config(hk_index_mean_reversion_manifest.default_config, ctx)
    config.pop("execution_cash_reserve_ratio", None)
    config.pop("rebalance_frequency", None)
    weights, signal_desc, is_defensive, status_desc, metadata = index_mr_strategy.compute_signals(
        require_market_data(ctx, "market_history"),
        get_current_holdings(ctx),
        **config,
    )
    diagnostics = {
        **metadata,
        "signal_description": signal_desc,
        "status_description": status_desc,
        "signal_source": index_mr_strategy.SIGNAL_SOURCE,
        "actionable": True,
    }
    risk_flags: tuple[str, ...] = ()
    if is_defensive:
        risk_flags += ("broad_risk_off",)
    if float(metadata.get("cash_weight") or 0.0) > 1e-12:
        risk_flags += ("cash_residual",)
    return StrategyDecision(
        positions=weights_to_positions(weights),
        risk_flags=risk_flags,
        diagnostics=diagnostics,
    )


hk_index_mean_reversion_entrypoint = CallableStrategyEntrypoint(
    manifest=hk_index_mean_reversion_manifest,
    _evaluate=evaluate_hk_index_mean_reversion,
)


hk_blue_chip_leader_rotation_entrypoint = CallableStrategyEntrypoint(
    manifest=hk_blue_chip_leader_rotation_manifest,
    _evaluate=evaluate_hk_blue_chip_leader_rotation,
)


__all__ = [
    "evaluate_hk_blue_chip_leader_rotation",
    "evaluate_hk_index_mean_reversion",
    "hk_blue_chip_leader_rotation_entrypoint",
    "hk_index_mean_reversion_entrypoint",
]
