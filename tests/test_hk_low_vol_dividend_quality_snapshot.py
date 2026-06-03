from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd
import pytest

from hk_equity_strategies.strategies import hk_low_vol_dividend_quality_snapshot as strategy


@dataclass(frozen=True)
class _SnapshotWrapper:
    frame: pd.DataFrame


def sample_factor_snapshot(*, weak_breadth: bool = False) -> pd.DataFrame:
    rows = [
        {
            "symbol": strategy.SAFE_HAVEN,
            "sector": "market",
            "close_hkd": 100.0,
            "adv20_hkd": 500_000_000.0,
            "market_cap_hkd": 2_000_000_000_000.0,
            "dividend_yield_net": 0.03,
            "dividend_stability_3y": 0.9,
            "earnings_positive": True,
            "payout_ratio": 0.4,
            "realized_vol_126": 0.20,
            "beta_252": 1.0,
            "maxdd_252": -0.12,
            "mom_6m": 0.03,
            "mom_12_1": 0.05,
            "sma200_gap": 0.02,
            "suspension_days_63": 0,
            "lot_size": 500,
        }
    ]
    sectors = ("financials", "utilities", "consumer", "telecom")
    for idx in range(12):
        rows.append(
            {
                "symbol": str(100 + idx).zfill(5),
                "sector": sectors[idx % len(sectors)],
                "close_hkd": 10.0 + idx,
                "adv20_hkd": 80_000_000.0 + idx * 5_000_000,
                "market_cap_hkd": 8_000_000_000.0 + idx * 500_000_000,
                "dividend_yield_net": 0.035 + idx * 0.002,
                "dividend_stability_3y": 0.70 + idx * 0.01,
                "earnings_positive": True,
                "payout_ratio": 0.45 + idx * 0.01,
                "realized_vol_126": 0.26 - idx * 0.01,
                "beta_252": 0.95 - idx * 0.02,
                "maxdd_252": -0.18 + idx * 0.005,
                "mom_6m": 0.04 + idx * 0.01,
                "mom_12_1": 0.06 + idx * 0.008,
                "sma200_gap": -0.03 if weak_breadth else 0.05 + idx * 0.001,
                "suspension_days_63": 0,
                "lot_size": 500,
                "eligible": True,
                "corporate_action_flag": False,
                "as_of": "2026-05-29",
            }
        )
    return pd.DataFrame(rows)


def test_low_vol_dividend_quality_selects_capped_single_names_and_safe_haven_residual():
    weights, ranked, metadata = strategy.build_target_weights(sample_factor_snapshot())

    selected = set(metadata["selected_symbols"])
    assert len(selected) == strategy.DEFAULT_HOLDINGS_COUNT
    assert strategy.SAFE_HAVEN not in selected
    assert metadata["regime"] == "risk_on"
    assert metadata["candidate_count"] == 12
    assert ranked.iloc[0]["symbol"] in selected
    assert max(weights.values()) <= strategy.DEFAULT_SINGLE_NAME_CAP + 1e-12
    assert sum(weights.values()) == pytest.approx(1.0)


def test_low_vol_dividend_quality_hard_defense_moves_to_safe_haven():
    weights, _ranked, metadata = strategy.build_target_weights(sample_factor_snapshot(weak_breadth=True))

    assert weights == {strategy.SAFE_HAVEN: 1.0}
    assert metadata["regime"] == "hard_defense"
    assert metadata["safe_haven_weight"] == 1.0


def test_compute_signals_accepts_feature_snapshot_guard_result_shape():
    weights, signal_desc, has_cash_residual, _status_desc, metadata = strategy.compute_signals(
        _SnapshotWrapper(sample_factor_snapshot()),
        current_holdings={"00104"},
    )

    assert weights
    assert "hk low vol dividend quality" in signal_desc
    assert has_cash_residual is False
    assert metadata["signal_source"] == "factor_snapshot"
    assert metadata["snapshot_contract_version"] == strategy.SNAPSHOT_CONTRACT_VERSION
    assert strategy.SAFE_HAVEN in metadata["managed_symbols"]


def test_compute_signals_ignores_runtime_only_config_keys():
    weights, _signal_desc, _has_cash_residual, _status_desc, metadata = strategy.compute_signals(
        _SnapshotWrapper(sample_factor_snapshot()),
        current_holdings={"00104"},
        run_as_of=datetime(2026, 6, 3),
        signal_effective_after_trading_days=1,
        runtime_execution_window_trading_days=1,
    )

    assert weights
    assert metadata["signal_source"] == "factor_snapshot"


def test_extract_managed_symbols_ignores_runtime_adapter_kwargs():
    symbols = strategy.extract_managed_symbols(
        _SnapshotWrapper(sample_factor_snapshot()),
        benchmark_symbol="02800",
        safe_haven=strategy.SAFE_HAVEN,
    )

    assert strategy.SAFE_HAVEN in symbols
    assert "00100" in symbols


def test_low_vol_dividend_quality_rejects_incomplete_snapshot():
    with pytest.raises(ValueError, match="factor_snapshot missing required columns"):
        strategy.build_target_weights(pd.DataFrame({"symbol": ["00001"]}))
