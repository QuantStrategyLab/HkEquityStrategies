"""HK equity combo manifests — moved from QuantHkComboStrategies.
"""
from __future__ import annotations

from quant_platform_kit.common.strategy_contracts import StrategyManifest

from hk_equity_strategies.strategies import hk_equity_combo as combo_strategy

HK_EQUITY_COMBO_PROFILE = combo_strategy.PROFILE_NAME


def _manifest(*, profile, domain, display_name, description, aliases=(), required_inputs=frozenset(), default_config=None):
    return StrategyManifest(
        profile=profile, domain=domain, display_name=display_name,
        description=description, aliases=aliases,
        required_inputs=required_inputs, default_config=default_config or {},
    )


hk_equity_combo_manifest = _manifest(
    profile=HK_EQUITY_COMBO_PROFILE,
    domain="hk_equity",
    display_name="HK Equity Combo",
    description="Combined HK equity strategy: Global ETF tactical rotation (60%) + low-vol dividend quality (40%) blended portfolio.",
    aliases=(),
    required_inputs=frozenset({"market_history", "dividend_snapshot"}),
    default_config={
        "etf_weight": 0.60, "dividend_weight": 0.40,
        "execution_cash_reserve_ratio": 0.02, "rebalance_frequency": "monthly",
    },
)

__all__ = ["HK_EQUITY_COMBO_PROFILE", "hk_equity_combo_manifest"]
