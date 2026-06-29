from __future__ import annotations

from quant_platform_kit.strategy_contracts import CallableStrategyEntrypoint, StrategyContext, StrategyDecision

from hk_equity_strategies.manifests import (
    hk_global_etf_tactical_rotation_manifest,
    hk_low_vol_dividend_quality_snapshot_manifest,
)
from hk_equity_strategies.strategies import hk_global_etf_tactical_rotation as global_etf_strategy
from hk_equity_strategies.strategies import hk_low_vol_dividend_quality_snapshot as low_vol_dividend_strategy

from ._common import get_current_holdings, merge_runtime_config, require_market_data, weights_to_positions


def evaluate_hk_global_etf_tactical_rotation(ctx: StrategyContext) -> StrategyDecision:
    config = merge_runtime_config(hk_global_etf_tactical_rotation_manifest.default_config, ctx)
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


hk_global_etf_tactical_rotation_entrypoint = CallableStrategyEntrypoint(
    manifest=hk_global_etf_tactical_rotation_manifest,
    _evaluate=evaluate_hk_global_etf_tactical_rotation,
)


def evaluate_hk_low_vol_dividend_quality_snapshot(ctx: StrategyContext) -> StrategyDecision:
    config = merge_runtime_config(hk_low_vol_dividend_quality_snapshot_manifest.default_config, ctx)
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


hk_low_vol_dividend_quality_snapshot_entrypoint = CallableStrategyEntrypoint(
    manifest=hk_low_vol_dividend_quality_snapshot_manifest,
    _evaluate=evaluate_hk_low_vol_dividend_quality_snapshot,
)


# ---------------------------------------------------------------------------
# HK Equity Combo entrypoint — delegates to combo_entrypoints
# ---------------------------------------------------------------------------


def evaluate_hk_equity_combo(ctx: StrategyContext) -> StrategyDecision:
    from hk_equity_strategies.combo_entrypoints import evaluate_hk_equity_combo as _eval
    return _eval(ctx)


from hk_equity_strategies.combo_manifests import hk_equity_combo_manifest  # noqa: E402 — intentional late import

hk_equity_combo_entrypoint = CallableStrategyEntrypoint(
    manifest=hk_equity_combo_manifest,
    _evaluate=evaluate_hk_equity_combo,
)


__all__ = [
    "evaluate_hk_global_etf_tactical_rotation",
    "evaluate_hk_low_vol_dividend_quality_snapshot",
    "evaluate_hk_equity_combo",
    "hk_global_etf_tactical_rotation_entrypoint",
    "hk_low_vol_dividend_quality_snapshot_entrypoint",
    "hk_equity_combo_entrypoint",
]
