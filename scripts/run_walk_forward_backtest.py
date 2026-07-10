#!/usr/bin/env python3
"""Run walk-forward backtests via QuantPlatformKit BacktestOrchestrator."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from hk_equity_strategies.backtest.orchestrator_runner import SUPPORTED_PROFILES, build_backtest_runner
from hk_equity_strategies.backtest.orchestrator_runner import _synthetic_market_history as _runner_synthetic_market_history
from hk_equity_strategies.strategies.hk_equity_combo import PROFILE_NAME as HK_EQUITY_COMBO_PROFILE
from hk_equity_strategies.strategies.hk_global_etf_tactical_rotation import DEFAULT_MIN_HISTORY_DAYS

DEFAULT_WINDOWS: tuple[tuple[date, date], ...] = (
    (date(2023, 6, 1), date(2024, 5, 31)),
    (date(2024, 6, 1), date(2025, 5, 31)),
)

PROFILE_DEFAULTS: dict[str, dict[str, Any]] = {
    "hk_global_etf_tactical_rotation": {"min_history_days": DEFAULT_MIN_HISTORY_DAYS},
    HK_EQUITY_COMBO_PROFILE: {
        "min_history_days": DEFAULT_MIN_HISTORY_DAYS,
        "combo_mode": "dynamic",
    },
}
MIN_SYNTHETIC_DAYS = 700


def _result_payload(item: Any) -> dict[str, Any]:
    return {
        "start_date": item.start_date.isoformat() if item.start_date else None,
        "end_date": item.end_date.isoformat() if item.end_date else None,
        "sharpe_ratio": item.sharpe_ratio,
        "max_drawdown": item.max_drawdown,
        "cagr": item.cagr,
        "total_return": item.total_return,
        "observation_count": item.observation_count,
        "run_id": getattr(item, "run_id", None),
    }


def _baseline_param_set_id(
    profile: str,
    params: dict[str, Any],
) -> str:
    fingerprint = hashlib.sha256(json.dumps(params, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]
    return f"{profile}_baseline_{fingerprint}"


def _baseline_identity_params(
    params: dict[str, Any],
    *,
    synthetic_days: int | None,
) -> dict[str, Any]:
    identity = copy.deepcopy(params)
    if synthetic_days is not None:
        identity["_synthetic_days"] = synthetic_days
    return identity


def _clone_market_history(market_history: pd.DataFrame | None) -> pd.DataFrame | None:
    return market_history.copy(deep=True) if market_history is not None else None


def _shared_market_history(params: dict[str, Any], synthetic_days: int, market_history: pd.DataFrame | None) -> pd.DataFrame:
    if market_history is not None:
        return _clone_market_history(market_history)
    min_history_days = int(params.get("min_history_days", DEFAULT_MIN_HISTORY_DAYS))
    if int(synthetic_days) < min_history_days:
        raise ValueError(f"synthetic_days must be >= {min_history_days} for profile={params!r}")
    return _runner_synthetic_market_history(days=int(synthetic_days))


def _build_runner(*, profile: str, synthetic_days: int, market_history: pd.DataFrame | None = None):
    return build_backtest_runner(
        profile,
        market_history=market_history,
        synthetic_days=synthetic_days,
    )


def run_walk_forward(
    *,
    profile: str,
    windows: tuple[tuple[date, date], ...] = DEFAULT_WINDOWS,
    synthetic_days: int = 700,
    store_root: Path | None = None,
    market_history: pd.DataFrame | None = None,
) -> dict[str, Any]:
    from quant_platform_kit.strategy_lifecycle.backtest_orchestrator import BacktestOrchestrator
    from quant_platform_kit.strategy_lifecycle.performance_store import PerformanceStore

    if profile not in SUPPORTED_PROFILES:
        raise ValueError(f"unsupported profile={profile!r}; supported={sorted(SUPPORTED_PROFILES)}")

    params = dict(PROFILE_DEFAULTS.get(profile, {"min_history_days": DEFAULT_MIN_HISTORY_DAYS}))
    store_root = store_root or Path("/tmp/hk_equity_wf_store")
    store_root.mkdir(parents=True, exist_ok=True)
    baseline_params = copy.deepcopy(params)
    shared_market_history = _shared_market_history(baseline_params, synthetic_days, market_history)
    with tempfile.TemporaryDirectory(prefix=f"{profile}_wf_", dir=store_root) as scratch_dir:
        scratch_store = PerformanceStore(local_root=Path(scratch_dir))
        scratch_orchestrator = BacktestOrchestrator(store=scratch_store)
        scratch_orchestrator.register_runner(
            "hk_equity",
            _build_runner(
                profile=profile,
                market_history=_clone_market_history(shared_market_history),
                synthetic_days=synthetic_days,
            ),
        )
        baseline_runner = _build_runner(
            profile=profile,
            market_history=_clone_market_history(shared_market_history),
            synthetic_days=synthetic_days,
        )
        baseline_raw = baseline_runner.run(
            profile,
            copy.deepcopy(baseline_params),
            start_date=None,
            end_date=None,
        )
        via_orch = scratch_orchestrator.run(
            profile,
            domain="hk_equity",
            params=copy.deepcopy(baseline_params),
            param_set_id=f"{profile}_full_compare",
            start_date=None,
            end_date=None,
        )
        wf_params = copy.deepcopy(baseline_params)
        wf_results = scratch_orchestrator.walk_forward(
            profile,
            domain="hk_equity",
            params=wf_params,
            windows=windows,
            param_set_id=f"{profile}_wf",
        )
    baseline_store_params = _baseline_identity_params(
        baseline_params,
        synthetic_days=synthetic_days if market_history is None else None,
    )
    store = PerformanceStore(local_root=store_root)
    orchestrator = BacktestOrchestrator(store=store)
    baseline = orchestrator.persist_result(
        baseline_raw,
        strategy_profile=profile,
        domain="hk_equity",
        params=baseline_params,
        param_set_id=_baseline_param_set_id(
            profile,
            baseline_store_params,
        ),
    )
    return {
        "strategy_profile": profile,
        "domain": "hk_equity",
        "baseline": _result_payload(baseline),
        "orchestrator_full_window": _result_payload(via_orch),
        "walk_forward_folds": [_result_payload(item) for item in wf_results],
        "source": "BacktestOrchestrator.walk_forward",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="HK walk-forward backtest via BacktestOrchestrator.")
    parser.add_argument("--profile", default="hk_global_etf_tactical_rotation")
    parser.add_argument("--list-profiles", action="store_true")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--synthetic-days", type=int, default=700)
    parser.add_argument("--store-root", type=Path)
    parser.add_argument("--use-yfinance", action="store_true", help="Load live ETF history via yfinance.")
    parser.add_argument("--start", default="2020-08-27", help="yfinance start date (YYYY-MM-DD).")
    parser.add_argument("--end", default="2026-06-01", help="yfinance end date (YYYY-MM-DD).")
    args = parser.parse_args()

    if args.list_profiles:
        print(json.dumps({"profiles": sorted(SUPPORTED_PROFILES)}, indent=2))
        return 0

    market_history = None
    if args.use_yfinance:
        from hk_equity_strategies.backtest.yfinance_market_data import download_market_history

        market_history = download_market_history(start=args.start, end=args.end)

    payload = run_walk_forward(
        profile=args.profile,
        synthetic_days=args.synthetic_days,
        store_root=args.store_root,
        market_history=market_history,
    )
    text = json.dumps(payload, indent=2, sort_keys=True, default=str)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
