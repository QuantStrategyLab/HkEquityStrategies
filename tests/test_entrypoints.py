from __future__ import annotations

import pandas as pd
import pytest

from quant_platform_kit.strategy_contracts import StrategyContext

from hk_equity_strategies import get_strategy_entrypoint
from hk_equity_strategies.catalog import HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE
from hk_equity_strategies.strategies.hk_listed_global_etf_rotation import (
    DEFAULT_UNIVERSE_SYMBOLS as GLOBAL_ETF_UNIVERSE_SYMBOLS,
    HIGH_DIVIDEND_ETF_SYMBOL as GLOBAL_HIGH_DIVIDEND_ETF_SYMBOL,
    NASDAQ100_ETF_SYMBOL,
)


def _global_etf_rotation_history() -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-02", periods=320)
    rates = {
        "02800": 1.0002,
        "02822": 1.0001,
        "03188": 1.0003,
        "03033": 0.9998,
        NASDAQ100_ETF_SYMBOL: 1.0009,
        "02840": 1.0004,
        "03175": 1.0005,
        GLOBAL_HIGH_DIVIDEND_ETF_SYMBOL: 1.0007,
    }
    rows = []
    for symbol in GLOBAL_ETF_UNIVERSE_SYMBOLS:
        price = 20.0
        for idx, date in enumerate(dates):
            price *= rates[symbol]
            close = price * (1.0 + 0.04 * ((idx % 5) - 2) / 5)
            rows.append({"date": date, "symbol": symbol, "close": close})
    return pd.DataFrame(rows)


def test_global_etf_rotation_entrypoint_returns_volatility_targeted_weight_targets():
    entrypoint = get_strategy_entrypoint(HK_LISTED_GLOBAL_ETF_ROTATION_PROFILE)

    decision = entrypoint.evaluate(
        StrategyContext(
            as_of="2026-02-25",
            market_data={"market_history": _global_etf_rotation_history()},
            runtime_config={"min_history_days": 260},
        )
    )

    weights = {position.symbol: position.target_weight for position in decision.positions}
    assert set(weights) == {NASDAQ100_ETF_SYMBOL, GLOBAL_HIGH_DIVIDEND_ETF_SYMBOL}
    assert 0.0 < sum(weights.values()) < 1.0
    assert decision.diagnostics["signal_source"] == "daily_market_history"
    assert decision.diagnostics["target_annual_volatility"] == pytest.approx(0.16)
    assert "cash_residual" in decision.risk_flags
