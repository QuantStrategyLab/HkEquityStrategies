from __future__ import annotations

import pandas as pd
import pytest

from hk_equity_strategies.strategies.hk_etf_regime_rotation import (
    CSI300_ETF_SYMBOL,
    DEFAULT_UNIVERSE_SYMBOLS,
    HIGH_DIVIDEND_ETF_SYMBOL,
    build_close_matrix,
    build_target_weights,
    compute_latest_signal,
    normalize_symbol,
    normalize_universe_symbols,
)


def _history(*, falling: bool = False) -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-02", periods=320)
    rates = {
        "02800": 0.9995 if falling else 1.0002,
        "02822": 0.9994 if falling else 1.0001,
        "02840": 0.9996 if falling else 1.0004,
        "03033": 0.9993 if falling else 0.9998,
        HIGH_DIVIDEND_ETF_SYMBOL: 0.9995 if falling else 1.0007,
        CSI300_ETF_SYMBOL: 0.9994 if falling else 1.0006,
    }
    rows = []
    for symbol in DEFAULT_UNIVERSE_SYMBOLS:
        price = 20.0
        for idx, date in enumerate(dates):
            price *= rates[symbol]
            # Add a tiny deterministic wiggle so volatility is non-zero and stable.
            close = price * (1.0 + 0.002 * ((idx % 5) - 2) / 5)
            rows.append({"date": date, "symbol": symbol, "close": close})
    return pd.DataFrame(rows)


def test_normalize_universe_symbols_preserves_hk_etf_codes():
    assert normalize_symbol("3110.HK") == "03110"
    assert normalize_universe_symbols(["2800.HK", "02800", "3033"]) == ("02800", "03033")


def test_build_close_matrix_accepts_long_market_history():
    close = build_close_matrix(_history())

    assert tuple(close.columns) == DEFAULT_UNIVERSE_SYMBOLS
    assert len(close) == 320


def test_compute_latest_signal_selects_top_two_positive_regimes():
    signal = compute_latest_signal(_history(), min_history_days=260)

    assert signal["signal_state"] == "risk_on"
    assert set(signal["selected_symbols"]) == {HIGH_DIVIDEND_ETF_SYMBOL, CSI300_ETF_SYMBOL}
    assert signal["cash_weight"] == pytest.approx(0.0)
    assert sum(signal["weights"].values()) == pytest.approx(1.0)


def test_build_target_weights_moves_to_cash_when_no_etf_is_eligible():
    weights, metadata = build_target_weights(_history(falling=True), min_history_days=260)

    assert weights == {}
    assert metadata["signal_state"] == "cash"
    assert metadata["cash_weight"] == pytest.approx(1.0)


def test_missing_market_history_columns_fail_fast():
    with pytest.raises(ValueError, match="market_history missing required columns"):
        build_close_matrix(pd.DataFrame({"date": ["2026-01-01"], "symbol": ["02800"]}))
