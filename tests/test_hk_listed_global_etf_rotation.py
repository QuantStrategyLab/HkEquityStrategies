from __future__ import annotations

import pandas as pd
import pytest

from hk_equity_strategies.strategies.hk_listed_global_etf_rotation import (
    DEFAULT_TARGET_ANNUAL_VOLATILITY,
    DEFAULT_UNIVERSE_SYMBOLS,
    HIGH_DIVIDEND_ETF_SYMBOL,
    NASDAQ100_ETF_SYMBOL,
    build_target_weights,
    compute_latest_signal,
    extract_managed_symbols,
)


def _history() -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-02", periods=320)
    rates = {
        "02800": 1.0002,
        "02822": 1.0001,
        "03188": 1.0003,
        "03033": 0.9998,
        NASDAQ100_ETF_SYMBOL: 1.0009,
        "02840": 1.0004,
        "03175": 1.0005,
        HIGH_DIVIDEND_ETF_SYMBOL: 1.0007,
    }
    rows = []
    for symbol in DEFAULT_UNIVERSE_SYMBOLS:
        price = 20.0
        for idx, date in enumerate(dates):
            price *= rates[symbol]
            close = price * (1.0 + 0.04 * ((idx % 5) - 2) / 5)
            rows.append({"date": date, "symbol": symbol, "close": close})
    return pd.DataFrame(rows)


def test_global_etf_rotation_selects_top_two_and_applies_volatility_target():
    signal = compute_latest_signal(_history(), min_history_days=260)

    assert signal["signal_state"] == "risk_on"
    assert set(signal["selected_symbols"]) == {NASDAQ100_ETF_SYMBOL, HIGH_DIVIDEND_ETF_SYMBOL}
    assert signal["target_annual_volatility"] == pytest.approx(DEFAULT_TARGET_ANNUAL_VOLATILITY)
    assert signal["realized_portfolio_volatility"] > DEFAULT_TARGET_ANNUAL_VOLATILITY
    assert 0.0 < signal["gross_exposure"] < 1.0
    assert signal["cash_weight"] == pytest.approx(1.0 - signal["gross_exposure"])


def test_global_etf_rotation_can_disable_volatility_target():
    weights, metadata = build_target_weights(
        _history(),
        min_history_days=260,
        target_annual_volatility=None,
    )

    assert set(weights) == {NASDAQ100_ETF_SYMBOL, HIGH_DIVIDEND_ETF_SYMBOL}
    assert sum(weights.values()) == pytest.approx(1.0)
    assert metadata["target_annual_volatility"] is None
    assert metadata["cash_weight"] == pytest.approx(0.0)


def test_global_etf_rotation_managed_symbols_default_to_global_hk_listed_universe():
    assert extract_managed_symbols() == DEFAULT_UNIVERSE_SYMBOLS
