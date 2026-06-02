from __future__ import annotations

from quant_platform_kit.strategy_contracts import CallableStrategyEntrypoint, StrategyContext, StrategyDecision

from hk_equity_strategies.manifests import (
    hk_high_dividend_low_vol_trend_manifest,
    hk_listed_global_etf_rotation_manifest,
    hk_low_vol_dividend_quality_manifest,
)
from hk_equity_strategies.strategies import hk_high_dividend_low_vol_trend as high_dividend_strategy
from hk_equity_strategies.strategies import hk_listed_global_etf_rotation as global_etf_strategy
from hk_equity_strategies.strategies import hk_low_vol_dividend_quality as low_vol_dividend_strategy

from ._common import get_current_holdings, merge_runtime_config, require_market_data, weights_to_positions


def evaluate_hk_listed_global_etf_rotation(ctx: StrategyContext) -> StrategyDecision:
    config = merge_runtime_config(hk_listed_global_etf_rotation_manifest.default_config, ctx)
    config.pop("execution_cash_reserve_ratio", None)
    config.pop("rebalance_frequency", None)
    weights, signal_desc, has_cash_residual, status_desc, metadata = global_etf_strategy.compute_signals(
        require_market_data(ctx, "market_history"),
        get_current_holdings(ctx),
        **config,
    )
    diagnostics = {
        **metadata,
        "signal_description": signal_desc,
        "status_description": status_desc,
        "signal_source": global_etf_strategy.SIGNAL_SOURCE,
        "actionable": True,
    }
    risk_flags: tuple[str, ...] = ()
    if has_cash_residual:
        risk_flags += ("cash_residual",)
    return StrategyDecision(
        positions=weights_to_positions(weights),
        risk_flags=risk_flags,
        diagnostics=diagnostics,
    )


hk_listed_global_etf_rotation_entrypoint = CallableStrategyEntrypoint(
    manifest=hk_listed_global_etf_rotation_manifest,
    _evaluate=evaluate_hk_listed_global_etf_rotation,
)


def evaluate_hk_high_dividend_low_vol_trend(ctx: StrategyContext) -> StrategyDecision:
    config = merge_runtime_config(hk_high_dividend_low_vol_trend_manifest.default_config, ctx)
    config.pop("execution_cash_reserve_ratio", None)
    config.pop("rebalance_frequency", None)
    weights, signal_desc, has_cash_residual, status_desc, metadata = high_dividend_strategy.compute_signals(
        require_market_data(ctx, "market_history"),
        get_current_holdings(ctx),
        **config,
    )
    diagnostics = {
        **metadata,
        "signal_description": signal_desc,
        "status_description": status_desc,
        "signal_source": high_dividend_strategy.SIGNAL_SOURCE,
        "actionable": True,
    }
    risk_flags: tuple[str, ...] = ()
    if has_cash_residual:
        risk_flags += ("cash_residual",)
    return StrategyDecision(
        positions=weights_to_positions(weights),
        risk_flags=risk_flags,
        diagnostics=diagnostics,
    )


hk_high_dividend_low_vol_trend_entrypoint = CallableStrategyEntrypoint(
    manifest=hk_high_dividend_low_vol_trend_manifest,
    _evaluate=evaluate_hk_high_dividend_low_vol_trend,
)


def evaluate_hk_low_vol_dividend_quality(ctx: StrategyContext) -> StrategyDecision:
    config = merge_runtime_config(hk_low_vol_dividend_quality_manifest.default_config, ctx)
    config.pop("execution_cash_reserve_ratio", None)
    config.pop("rebalance_frequency", None)
    weights, signal_desc, has_cash_residual, status_desc, metadata = low_vol_dividend_strategy.compute_signals(
        require_market_data(ctx, "feature_snapshot"),
        get_current_holdings(ctx),
        **config,
    )
    diagnostics = {
        **metadata,
        "signal_description": signal_desc,
        "status_description": status_desc,
        "signal_source": low_vol_dividend_strategy.SIGNAL_SOURCE,
        "actionable": True,
    }
    risk_flags: tuple[str, ...] = ()
    if has_cash_residual:
        risk_flags += ("cash_residual",)
    return StrategyDecision(
        positions=weights_to_positions(weights),
        risk_flags=risk_flags,
        diagnostics=diagnostics,
    )


hk_low_vol_dividend_quality_entrypoint = CallableStrategyEntrypoint(
    manifest=hk_low_vol_dividend_quality_manifest,
    _evaluate=evaluate_hk_low_vol_dividend_quality,
)


__all__ = [
    "evaluate_hk_high_dividend_low_vol_trend",
    "evaluate_hk_listed_global_etf_rotation",
    "evaluate_hk_low_vol_dividend_quality",
    "hk_high_dividend_low_vol_trend_entrypoint",
    "hk_listed_global_etf_rotation_entrypoint",
    "hk_low_vol_dividend_quality_entrypoint",
]
