from __future__ import annotations

import pandas as pd
import pytest

from hk_equity_strategies.strategies.blue_chip_leader_rotation import (
    REQUIRED_FEATURE_COLUMNS,
    build_target_weights,
    compute_signals,
    extract_managed_symbols,
    normalize_symbol,
    score_candidates,
)


def _snapshot(*, as_of: str = "2026-04-30") -> pd.DataFrame:
    rows = [
        ("02800", "ETF", 20.0, 120_000_000, 260, 0.02, 0.04, 0.08, 0.00, 0.01, 0.03, 0.12, -0.10),
        ("00700", "Technology", 320.0, 900_000_000, 260, 0.09, 0.20, 0.35, 0.16, 0.04, 0.12, 0.18, -0.18),
        ("03690", "Technology", 120.0, 300_000_000, 260, 0.08, 0.18, 0.22, 0.14, 0.03, 0.10, 0.20, -0.20),
        ("00941", "Telecom", 75.0, 500_000_000, 260, 0.05, 0.10, 0.16, 0.06, 0.02, 0.08, 0.10, -0.08),
        ("02318", "Financials", 48.0, 450_000_000, 260, 0.04, 0.08, 0.12, 0.04, 0.01, 0.05, 0.12, -0.12),
        ("00005", "Financials", 68.0, 320_000_000, 260, -0.02, 0.01, 0.02, -0.03, -0.05, -0.02, 0.09, -0.15),
    ]
    return pd.DataFrame(
        rows,
        columns=[
            "symbol",
            "sector",
            "close_hkd",
            "adv20_hkd",
            "history_days",
            "mom_3m",
            "mom_6m",
            "mom_12_1",
            "rel_mom_6m_vs_benchmark",
            "high_252_gap",
            "sma200_gap",
            "vol_63",
            "maxdd_126",
        ],
    ).assign(as_of=as_of, eligible=True, lot_size=100)


def test_normalize_symbol_preserves_hk_leading_zeroes():
    assert normalize_symbol("700") == "00700"
    assert normalize_symbol("00700.HK") == "00700"
    assert normalize_symbol("HSI") == "HSI"


def test_score_candidates_ranks_positive_relative_momentum():
    ranked = score_candidates(_snapshot(), current_holdings={"00941"})

    assert ranked.iloc[0]["symbol"] in {"00700", "03690"}
    assert "02800" not in set(ranked["symbol"])
    assert ranked["score"].notna().all()


def test_build_target_weights_selects_leaders_and_safe_haven_residual():
    weights, _ranked, metadata = build_target_weights(
        _snapshot(),
        current_holdings={"00941"},
        holdings_count=3,
        single_name_cap=0.2,
        min_adv20_hkd=1,
    )

    assert metadata["regime"] == "risk_on"
    assert metadata["selected_count"] == 3
    assert weights["02800"] == pytest.approx(0.4)
    assert sum(weights.values()) == pytest.approx(1.0)
    assert all(symbol in weights for symbol in metadata["selected_symbols"])


def test_compute_signals_returns_no_execute_outside_snapshot_window():
    weights, signal, is_hard_defense, status, metadata = compute_signals(
        _snapshot(as_of="2026-04-30"),
        current_holdings=set(),
        run_as_of="2026-05-15",
        min_adv20_hkd=1,
    )

    assert weights is None
    assert "waiting" in signal
    assert is_hard_defense is False
    assert "outside_monthly_execution_window" in status
    assert metadata["no_op_reason"].startswith("outside_monthly_execution_window")


def test_extract_managed_symbols_adds_safe_haven():
    symbols = extract_managed_symbols(_snapshot())

    assert "00700" in symbols
    assert "02800" in symbols


def test_missing_feature_columns_fail_fast():
    snapshot = _snapshot().drop(columns=[next(iter(REQUIRED_FEATURE_COLUMNS - {"symbol"}))])

    with pytest.raises(ValueError, match="feature_snapshot missing required columns"):
        score_candidates(snapshot)
