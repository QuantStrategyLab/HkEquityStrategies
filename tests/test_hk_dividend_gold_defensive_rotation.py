from __future__ import annotations

import pandas as pd
import pytest

from hk_equity_strategies.strategies.hk_dividend_gold_defensive_rotation import (
    DEFAULT_UNIVERSE_SYMBOLS,
    GOLD_ETF_SYMBOL,
    HIGH_DIVIDEND_ETF_SYMBOL,
    build_target_weights,
    compute_latest_signal,
    normalize_universe_symbols,
)


def _history(*, falling: bool = False) -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-02", periods=180)
    rates = {
        GOLD_ETF_SYMBOL: 0.9997 if falling else 1.0004,
        HIGH_DIVIDEND_ETF_SYMBOL: 0.9996 if falling else 1.0007,
    }
    rows = []
    for symbol in DEFAULT_UNIVERSE_SYMBOLS:
        price = 20.0
        for idx, date in enumerate(dates):
            price *= rates[symbol]
            close = price * (1.0 + 0.002 * ((idx % 5) - 2) / 5)
            rows.append({"date": date, "symbol": symbol, "close": close})
    return pd.DataFrame(rows)


def test_normalize_universe_symbols_preserves_hk_codes():
    assert normalize_universe_symbols(["3110.HK", "2840"]) == ("03110", "02840")


def test_compute_latest_signal_selects_high_dividend_and_gold_when_trending():
    signal = compute_latest_signal(_history(), min_history_days=126)

    assert signal["signal_state"] == "risk_on"
    assert set(signal["selected_symbols"]) == {GOLD_ETF_SYMBOL, HIGH_DIVIDEND_ETF_SYMBOL}
    assert signal["cash_weight"] == pytest.approx(0.0)
    assert sum(signal["weights"].values()) == pytest.approx(1.0)
    assert signal["target_annual_volatility"] == pytest.approx(0.12)


def test_compute_latest_signal_applies_volatility_target_when_realized_volatility_is_high():
    signal = compute_latest_signal(
        _history(),
        min_history_days=126,
        target_annual_volatility=0.01,
    )

    assert signal["signal_state"] == "risk_on"
    assert 0.0 < sum(signal["weights"].values()) < 1.0
    assert signal["cash_weight"] > 0.0


def test_build_target_weights_moves_to_cash_when_no_symbol_is_eligible():
    weights, metadata = build_target_weights(_history(falling=True), min_history_days=126)

    assert weights == {}
    assert metadata["signal_state"] == "cash"
    assert metadata["cash_weight"] == pytest.approx(1.0)
