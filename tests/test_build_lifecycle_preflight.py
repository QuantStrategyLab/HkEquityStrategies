from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from hk_equity_strategies.backtest.orchestrator_runner import (
    SUPPORTED_PROFILES,
    _synthetic_market_history,
)
from scripts import build_lifecycle_preflight as lifecycle


def _persist_test_baseline(profile, store_root, *, layout="store", fault=None):
    from quant_platform_kit.strategy_lifecycle.contracts import BacktestResult
    from quant_platform_kit.strategy_lifecycle.performance_store import PerformanceStore

    run_id = f"{profile}-baseline"
    if fault != "missing":
        result = BacktestResult(
            strategy_profile=profile,
            domain="hk_equity",
            param_set_id=f"{profile}_baseline",
            params={},
            run_id=run_id,
            computed_at="2026-01-01T00:00:00+00:00",
            periods_per_year=252.0,
            calendar_id="XHKG",
        )
        PerformanceStore(local_root=store_root).save_backtest_result(result)
        directory = store_root / "backtest" / "hk_equity" / profile
        path = next(directory.rglob("backtest_*.json"))
        if layout == "flat":
            target = directory / "backtest_v1.json"
            if path != target:
                path.replace(target)
            path = target
        payload = json.loads(path.read_text())
        if fault == "run_id":
            payload["run_id"] = "another-run"
        elif fault == "profile":
            payload["strategy_profile"] = "another-profile"
        elif fault == "domain":
            payload["domain"] = "another-domain"
        path.write_text(json.dumps(payload), encoding="utf-8")
        if fault == "duplicate":
            (directory / "backtest_v1_duplicate.json").write_text(
                json.dumps(payload), encoding="utf-8"
            )
    return {"baseline": {"run_id": run_id}}


def _stub_preflight_matrix(monkeypatch):
    monkeypatch.setattr(
        lifecycle,
        "build_profile_return_matrix",
        lambda profile, _history: pd.DataFrame(
            {"as_of": ["2026-01-01"], profile: [0.0], "buy_hold_2800": [0.0]}
        ),
    )


@pytest.mark.parametrize("layout", ["store", "flat"])
def test_preflight_accepts_persisted_run_id_in_supported_store_layouts(
    tmp_path: Path, monkeypatch, layout
) -> None:
    _stub_preflight_matrix(monkeypatch)
    monkeypatch.setattr(
        lifecycle, "run_walk_forward",
        lambda *, profile, store_root, **_kwargs: _persist_test_baseline(
            profile, store_root, layout=layout
        ),
    )

    result = lifecycle.build_lifecycle_preflight_bundle(
        _synthetic_market_history(days=320), bundle_root=tmp_path
    )

    assert result["profiles"] == sorted(SUPPORTED_PROFILES)


@pytest.mark.parametrize("fault", ["missing", "duplicate", "run_id", "profile", "domain"])
def test_preflight_rejects_missing_duplicate_or_mismatched_baseline(
    tmp_path: Path, monkeypatch, fault
) -> None:
    _stub_preflight_matrix(monkeypatch)
    monkeypatch.setattr(
        lifecycle, "run_walk_forward",
        lambda *, profile, store_root, **_kwargs: _persist_test_baseline(
            profile, store_root, layout="flat", fault=fault
        ),
    )

    with pytest.raises(RuntimeError, match="expected one persisted lifecycle baseline"):
        lifecycle.build_lifecycle_preflight_bundle(
            _synthetic_market_history(days=320), bundle_root=tmp_path
        )


def test_script_entrypoint_loads_from_repository_root() -> None:
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, str(root / "scripts" / "build_lifecycle_preflight.py"), "--help"],
        cwd=root,
        env={**os.environ, "PYTHONPATH": str(root / "src")},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_builds_lifecycle_contract_for_every_configured_profile(
    tmp_path: Path,
    monkeypatch,
) -> None:
    history = _synthetic_market_history(days=320)
    bundle_root = tmp_path / "bundle"

    def persist_baseline(*, profile, store_root, **_kwargs):
        return _persist_test_baseline(profile, store_root)

    monkeypatch.setattr(lifecycle, "run_walk_forward", persist_baseline)

    result = lifecycle.build_lifecycle_preflight_bundle(
        history,
        bundle_root=bundle_root,
    )

    assert result["profiles"] == sorted(SUPPORTED_PROFILES)
    for profile in SUPPORTED_PROFILES:
        backtests = list(
            (
                bundle_root
                / "data"
                / "lifecycle_store"
                / "backtest"
                / "hk_equity"
                / profile
            ).rglob("backtest_*.json")
        )
        assert len(backtests) == 1
        matrix = pd.read_csv(
            bundle_root
            / "external"
            / "HkEquitySnapshotPipelines"
            / "data"
            / "output"
            / profile
            / "portfolio_and_tracker_returns.csv"
        )
        assert list(matrix.columns) == ["as_of", profile, "buy_hold_2800"]
        assert len(matrix) >= 260
        assert matrix[[profile, "buy_hold_2800"]].notna().all().all()


def test_writes_auditable_normalized_market_input(tmp_path: Path) -> None:
    history = _synthetic_market_history(days=320)

    manifest = lifecycle.write_market_input_artifact(
        history,
        output_dir=tmp_path,
        source="yfinance",
        requested_start="2020-08-27",
        requested_end="2026-07-31",
        retrieved_at="2026-07-30T07:00:00+00:00",
        yfinance_version="1.2.2",
    )

    data_path = tmp_path / "market_history.csv.gz"
    assert data_path.is_file()
    assert manifest["schema_version"] == "hk_lifecycle_market_input.v1"
    assert manifest["source"] == "yfinance"
    assert manifest["yfinance_version"] == "1.2.2"
    assert manifest["sha256"] == hashlib.sha256(data_path.read_bytes()).hexdigest()
    assert manifest["profiles"] == sorted(SUPPORTED_PROFILES)
    assert json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8")) == manifest


def test_rejects_stale_or_incomplete_market_input() -> None:
    history = _synthetic_market_history(days=320)
    latest = pd.Timestamp(history["date"].max()).date()

    lifecycle.validate_market_history(history, reference_date=latest)

    incomplete = history.loc[history["symbol"] != "02800"]
    try:
        lifecycle.validate_market_history(incomplete, reference_date=latest)
    except ValueError as exc:
        assert "02800" in str(exc)
    else:
        raise AssertionError("missing benchmark symbol must fail closed")

    try:
        lifecycle.validate_market_history(
            history,
            reference_date=date.fromordinal(latest.toordinal() + 11),
        )
    except ValueError as exc:
        assert "stale" in str(exc)
    else:
        raise AssertionError("stale market input must fail closed")

    stale_symbol = history.loc[
        ~(
            (history["symbol"] == "02822")
            & (
                pd.to_datetime(history["date"])
                > pd.Timestamp(latest) - pd.Timedelta(days=11)
            )
        )
    ]
    try:
        lifecycle.validate_market_history(
            stale_symbol,
            reference_date=latest,
        )
    except ValueError as exc:
        assert "02822" in str(exc)
    else:
        raise AssertionError("a stale individual symbol must fail closed")
