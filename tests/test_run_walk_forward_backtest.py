from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
QPK_SRC = ROOT.parent / "QuantPlatformKit" / "src"
if str(QPK_SRC) not in sys.path:
    sys.path.insert(0, str(QPK_SRC))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from hk_equity_strategies.backtest.orchestrator_runner import _synthetic_market_history
from scripts.run_walk_forward_backtest import _baseline_param_set_id, _clone_market_history, run_walk_forward


def test_run_walk_forward_persists_lifecycle_baseline(tmp_path: Path) -> None:
    payload = run_walk_forward(
        profile="hk_global_etf_tactical_rotation",
        synthetic_days=700,
        store_root=tmp_path,
    )

    records = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in (tmp_path / "backtest" / "hk_equity" / "hk_global_etf_tactical_rotation").glob("*.json")
    ]

    assert payload["baseline"]["sharpe_ratio"] is not None
    baseline_records = [record for record in records if "_baseline_" in record["param_set_id"]]
    assert baseline_records
    assert all(record["params"] == {"min_history_days": 260} for record in baseline_records)
    assert not any("_wf" in record["param_set_id"] for record in records)
    assert payload["orchestrator_full_window"]["sharpe_ratio"] is not None
    assert payload["walk_forward_folds"]


def test_clone_market_history_returns_independent_dataframe() -> None:
    history = _synthetic_market_history(days=10)

    cloned = _clone_market_history(history)

    assert cloned is not history
    assert cloned is not None
    cloned.loc[:, "close"] = 0.0
    assert not cloned["close"].equals(history["close"])


def test_run_walk_forward_accepts_explicit_market_history(tmp_path: Path) -> None:
    history = _synthetic_market_history(days=1200)

    payload = run_walk_forward(
        profile="hk_global_etf_tactical_rotation",
        synthetic_days=700,
        store_root=tmp_path,
        market_history=history,
    )

    assert payload["baseline"]["sharpe_ratio"] is not None
    assert isinstance(history, pd.DataFrame)


def test_baseline_param_set_id_tracks_runner_inputs() -> None:
    first = _baseline_param_set_id(
        "hk_global_etf_tactical_rotation",
        {"min_history_days": 260, "_synthetic_days": 700},
    )
    second = _baseline_param_set_id(
        "hk_global_etf_tactical_rotation",
        {"min_history_days": 260, "_synthetic_days": 900},
    )

    assert first != second


def test_run_walk_forward_rejects_too_short_synthetic_history(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="synthetic_days must be >= 260"):
        run_walk_forward(
            profile="hk_global_etf_tactical_rotation",
            synthetic_days=220,
            store_root=tmp_path,
        )
