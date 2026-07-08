#!/usr/bin/env python3
"""Pilot: run hk_global_etf_tactical_rotation through BacktestOrchestrator.walk_forward()."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

from hk_equity_strategies.backtest.orchestrator_runner import HkEtfRotationBacktestRunner
from hk_equity_strategies.strategies.hk_global_etf_tactical_rotation import (
    DEFAULT_MIN_HISTORY_DAYS,
    PROFILE_NAME,
)

DEFAULT_WINDOWS: tuple[tuple[date, date], ...] = (
    (date(2023, 6, 1), date(2024, 5, 31)),
    (date(2024, 6, 1), date(2025, 5, 31)),
)


def main() -> int:
    parser = argparse.ArgumentParser(description="HK global ETF walk-forward pilot")
    parser.add_argument("--output", type=Path, default=Path("hk_walk_forward_pilot.json"))
    parser.add_argument("--synthetic-days", type=int, default=700)
    args = parser.parse_args()

    from quant_platform_kit.strategy_lifecycle.backtest_orchestrator import BacktestOrchestrator
    from quant_platform_kit.strategy_lifecycle.performance_store import PerformanceStore

    runner = HkEtfRotationBacktestRunner(synthetic_days=args.synthetic_days)
    params: dict[str, Any] = {"min_history_days": DEFAULT_MIN_HISTORY_DAYS}
    store = PerformanceStore(local_root=args.output.parent / ".wf_store")
    orchestrator = BacktestOrchestrator(store=store)
    orchestrator.register_runner("hk_equity", runner)

    baseline = runner.run(PROFILE_NAME, params)
    results = orchestrator.walk_forward(
        PROFILE_NAME,
        domain="hk_equity",
        params=params,
        windows=DEFAULT_WINDOWS,
    )
    payload = {
        "profile": PROFILE_NAME,
        "baseline": {
            "sharpe_ratio": baseline.sharpe_ratio,
            "max_drawdown": baseline.max_drawdown,
            "cagr": baseline.cagr,
        },
        "windows": [
            {
                "start": item.start_date.isoformat() if item.start_date else None,
                "end": item.end_date.isoformat() if item.end_date else None,
                "sharpe_ratio": item.sharpe_ratio,
                "max_drawdown": item.max_drawdown,
                "cagr": item.cagr,
            }
            for item in results
        ],
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
