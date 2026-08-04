from __future__ import annotations

import pandas as pd
import pytest

from quant_platform_kit.strategy_contracts import StrategyContext

from hk_equity_strategies import get_strategy_entrypoint
from hk_equity_strategies.catalog import (
    HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE,
    HK_LOW_VOL_DIVIDEND_QUALITY_SNAPSHOT_PROFILE,
)
from hk_equity_strategies.strategies.hk_global_etf_tactical_rotation import (
    DEFAULT_UNIVERSE_SYMBOLS as GLOBAL_ETF_UNIVERSE_SYMBOLS,
    HIGH_DIVIDEND_ETF_SYMBOL as GLOBAL_HIGH_DIVIDEND_ETF_SYMBOL,
    NASDAQ100_ETF_SYMBOL,
)
from test_hk_low_vol_dividend_quality_snapshot import sample_factor_snapshot


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


def _assert_no_order(decision) -> None:
    assert decision.positions == ()
    assert decision.budgets == ()
    assert decision.risk_flags == ("rejected:too_many_positions",)
    assert decision.diagnostics["risk_gate"] == "REJECT"
    assert "仅允许一个非零持仓" in decision.diagnostics["reason"]


def test_global_etf_rotation_entrypoint_preserves_signal_but_fails_closed_without_snapshot():
    entrypoint = get_strategy_entrypoint(HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE)

    decision = entrypoint.evaluate(
        StrategyContext(
            as_of="2026-02-25",
            market_data={"market_history": _global_etf_rotation_history()},
            runtime_config={"min_history_days": 260},
        )
    )

    _assert_no_order(decision)
    assert decision.diagnostics["signal_source"] == "daily_market_history"
    assert decision.diagnostics["target_annual_volatility"] == pytest.approx(0.16)
    assert set(decision.diagnostics["selected_symbols"]) == {
        NASDAQ100_ETF_SYMBOL,
        GLOBAL_HIGH_DIVIDEND_ETF_SYMBOL,
    }


def test_low_vol_dividend_quality_entrypoint_preserves_signal_but_fails_closed_without_snapshot():
    entrypoint = get_strategy_entrypoint(HK_LOW_VOL_DIVIDEND_QUALITY_SNAPSHOT_PROFILE)

    decision = entrypoint.evaluate(
        StrategyContext(
            as_of="2026-05-29",
            market_data={"feature_snapshot": sample_factor_snapshot()},
            state={"current_holdings": {"00104": 1000}},
        )
    )

    _assert_no_order(decision)
    assert decision.diagnostics["signal_source"] == "factor_snapshot"
    assert decision.diagnostics["snapshot_contract_version"] == "hk_low_vol_dividend_quality_snapshot.factor_snapshot.v1"
