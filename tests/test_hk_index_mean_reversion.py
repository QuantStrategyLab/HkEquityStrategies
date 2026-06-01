from __future__ import annotations

import pandas as pd
import pytest

from hk_equity_strategies.strategies.hk_index_mean_reversion import (
    HSI_ETF_SYMBOL,
    HSTECH_ETF_SYMBOL,
    build_close_matrix,
    build_target_weights,
    compute_latest_signal,
    normalize_symbol,
)


def _history(*, ratio_tail: float = 0.70, anchor_last: float = 25.0, satellite_trend: str = "up") -> pd.DataFrame:
    dates = pd.bdate_range("2025-01-02", periods=300)
    anchor = pd.Series([20.0 + idx * (anchor_last - 20.0) / 299 for idx in range(300)], index=dates)
    ratio = pd.Series(0.20, index=dates)
    ratio.iloc[-5:] = 0.20 * ratio_tail
    satellite = anchor * ratio
    if satellite_trend == "down":
        satellite.iloc[-120:] = list(pd.Series(satellite.iloc[-120]).repeat(120) * 0.8)
    rows = []
    for date, anchor_close in anchor.items():
        rows.append({"date": date, "symbol": HSI_ETF_SYMBOL, "close": anchor_close})
    for date, satellite_close in satellite.items():
        rows.append({"date": date, "symbol": HSTECH_ETF_SYMBOL, "close": satellite_close})
    return pd.DataFrame(rows)


def test_normalize_symbol_preserves_hk_index_etf_codes():
    assert normalize_symbol("2800.HK") == "02800"
    assert normalize_symbol("3033") == "03033"


def test_build_close_matrix_accepts_long_market_history():
    close = build_close_matrix(_history())

    assert list(close.columns) == ["anchor", "satellite"]
    assert len(close) == 300


def test_compute_latest_signal_overweights_hstech_when_spread_is_cheap():
    signal = compute_latest_signal(_history(ratio_tail=0.70), min_history_days=260)

    assert signal["signal_state"] == "satellite_oversold"
    assert signal["satellite_weight"] == pytest.approx(0.65)
    assert signal["anchor_weight"] == pytest.approx(0.35)
    assert signal["cash_weight"] == pytest.approx(0.0)


def test_compute_latest_signal_uses_anchor_when_hstech_is_rich():
    signal = compute_latest_signal(_history(ratio_tail=1.30), min_history_days=260)

    assert signal["signal_state"] == "satellite_rich"
    assert signal["satellite_weight"] == pytest.approx(0.05)
    assert signal["anchor_weight"] == pytest.approx(0.95)


def test_compute_latest_signal_treats_flat_ratio_as_neutral():
    signal = compute_latest_signal(_history(ratio_tail=1.0), min_history_days=260)

    assert signal["signal_state"] == "spread_normalized"
    assert signal["satellite_weight"] == pytest.approx(0.50)
    assert signal["anchor_weight"] == pytest.approx(0.50)


def test_compute_latest_signal_uses_defensive_anchor_when_hsi_is_below_trend():
    signal = compute_latest_signal(_history(anchor_last=18.0, ratio_tail=0.70), min_history_days=260)

    assert signal["broad_risk_off"] is True
    assert signal["signal_state"] == "defensive_satellite_oversold"
    assert signal["anchor_weight"] == pytest.approx(0.35)
    assert signal["satellite_weight"] == pytest.approx(0.0)
    assert signal["cash_weight"] == pytest.approx(0.65)


def test_build_target_weights_keeps_small_satellite_underweight():
    weights, metadata = build_target_weights(_history(ratio_tail=1.30), min_history_days=260)

    assert weights[HSI_ETF_SYMBOL] == pytest.approx(0.95)
    assert weights[HSTECH_ETF_SYMBOL] == pytest.approx(0.05)
    assert metadata["satellite_symbol"] == HSTECH_ETF_SYMBOL


def test_missing_market_history_columns_fail_fast():
    with pytest.raises(ValueError, match="market_history missing required columns"):
        build_close_matrix(pd.DataFrame({"date": ["2026-01-01"], "symbol": ["02800"]}))
