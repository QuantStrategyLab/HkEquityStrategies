"""HK equity combo entrypoints — moved from QuantHkComboStrategies.
"""
from __future__ import annotations

from typing import Any

from quant_platform_kit.strategy_contracts import (
    CallableStrategyEntrypoint, PositionTarget, StrategyContext, StrategyDecision,
)

from hk_equity_strategies.combo_manifests import hk_equity_combo_manifest
from hk_equity_strategies.strategies import hk_equity_combo


def _require_market_data(ctx: StrategyContext, key: str) -> Any:
    if key not in ctx.market_data:
        raise ValueError(f"StrategyContext.market_data[{key!r}] is required")
    return ctx.market_data[key]


def evaluate_hk_equity_combo(ctx: StrategyContext) -> StrategyDecision:
    config = {**hk_equity_combo_manifest.default_config, **ctx.runtime_config or {}}
    config.pop("execution_cash_reserve_ratio", None)
    config.pop("rebalance_frequency", None)
    combined, metadata = hk_equity_combo.build_target_weights(
        market_history=_require_market_data(ctx, "market_history"),
        dividend_snapshot=_require_market_data(ctx, "dividend_snapshot"),
        config=config,
    )
    diagnostics = {
        **metadata, "signal_description": f"etf={config.get('etf_weight', 0.60):.0%} div={config.get('dividend_weight', 0.40):.0%}",
        "status_description": f"etf={config.get('etf_weight', 0.60):.0%} div={config.get('dividend_weight', 0.40):.0%}",
        "signal_source": hk_equity_combo.SIGNAL_SOURCE, "actionable": True,
    }
    return StrategyDecision(
        positions=tuple(
            PositionTarget(symbol=str(s), target_weight=float(w), role="target")
            for s, w in sorted(combined.items()) if abs(float(w)) > 1e-12
        ),
        risk_flags=(), diagnostics=diagnostics,
    )


hk_equity_combo_entrypoint = CallableStrategyEntrypoint(
    manifest=hk_equity_combo_manifest, _evaluate=evaluate_hk_equity_combo,
)

__all__ = ["evaluate_hk_equity_combo", "hk_equity_combo_entrypoint"]
