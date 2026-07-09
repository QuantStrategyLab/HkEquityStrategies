"""Shared helpers for HK research scripts calling BacktestOrchestrator adapters."""

from __future__ import annotations

from datetime import date
from typing import Any, Mapping

import pandas as pd

from hk_equity_strategies.backtest.orchestrator_runner import HkEtfRotationBacktestRunner
from hk_equity_strategies.strategies.hk_global_etf_tactical_rotation import (
    DEFAULT_MIN_HISTORY_DAYS,
    PROFILE_NAME,
)


def _result_to_metrics(result: Any) -> dict[str, Any]:
    return {
        "sharpe_ratio": result.sharpe_ratio,
        "max_drawdown": result.max_drawdown,
        "annual_return": result.cagr,
        "total_return": result.total_return,
        "annual_volatility": result.volatility,
        "days": result.observation_count,
    }


def run_etf_rotation_profile_backtest(
    profile: str,
    *,
    market_history: pd.DataFrame | None = None,
    synthetic_days: int = 700,
    start_date: date | None = None,
    end_date: date | None = None,
    params: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Run a single-window HK ETF rotation backtest through HkEtfRotationBacktestRunner."""
    if profile != PROFILE_NAME:
        raise ValueError(f"unsupported profile={profile!r}")

    runner = HkEtfRotationBacktestRunner(
        market_history=market_history,
        synthetic_days=synthetic_days,
    )
    merged_params = {"min_history_days": DEFAULT_MIN_HISTORY_DAYS}
    if params:
        merged_params.update(dict(params))
    result = runner.run(profile, merged_params, start_date=start_date, end_date=end_date)
    return {
        "profile": profile,
        "params": merged_params,
        "start_date": result.start_date.isoformat() if result.start_date else None,
        "end_date": result.end_date.isoformat() if result.end_date else None,
        "metrics": _result_to_metrics(result),
        "source": "HkEtfRotationBacktestRunner",
        "run_id": getattr(result, "run_id", None),
    }


__all__ = ["run_etf_rotation_profile_backtest"]
