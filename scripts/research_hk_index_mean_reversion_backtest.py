#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from hk_equity_strategies.strategies import hk_index_mean_reversion as strategy


@dataclass(frozen=True)
class BacktestConfig:
    start: str = "2020-08-27"
    end: str = "2026-06-01"
    anchor_yahoo: str = "2800.HK"
    satellite_yahoo: str = "3033.HK"
    cost_bps: float = 10.0
    train_end: str = "2023-12-29"
    oos_start: str = "2024-01-01"


def _download_close(config: BacktestConfig) -> pd.DataFrame:
    try:
        import yfinance as yf
    except Exception as exc:  # pragma: no cover - research helper only
        raise SystemExit("yfinance is required for this research script; install it outside production deps") from exc
    raw = yf.download(
        [config.anchor_yahoo, config.satellite_yahoo],
        start=config.start,
        end=config.end,
        auto_adjust=True,
        progress=False,
        threads=False,
    )
    close = raw["Close"][[config.anchor_yahoo, config.satellite_yahoo]].dropna(how="any")
    close.columns = ["anchor", "satellite"]
    return close


def _metrics(returns: pd.Series) -> dict[str, float | int]:
    returns = returns.dropna()
    equity = (1.0 + returns).cumprod()
    years = len(returns) / 252.0
    annual_return = float(equity.iloc[-1] ** (1 / years) - 1) if years > 0 else 0.0
    drawdown = equity / equity.cummax() - 1.0
    annual_vol = float(returns.std(ddof=0) * math.sqrt(252))
    return {
        "days": int(len(returns)),
        "annual_return": annual_return,
        "max_drawdown": float(drawdown.min()),
        "annual_volatility": annual_vol,
        "total_return": float(equity.iloc[-1] - 1.0),
    }


def _target_weights(close: pd.DataFrame) -> pd.DataFrame:
    market_history = (
        close.rename(columns={"anchor": strategy.DEFAULT_ANCHOR_SYMBOL, "satellite": strategy.DEFAULT_SATELLITE_SYMBOL})
        .reset_index(names="date")
        .melt(id_vars="date", var_name="symbol", value_name="close")
    )
    rows: list[dict[str, Any]] = []
    for as_of in close.index:
        partial_history = market_history.loc[market_history["date"] <= as_of]
        if partial_history["date"].nunique() < strategy.DEFAULT_MIN_HISTORY_DAYS:
            rows.append({"date": as_of, "anchor": 0.50, "satellite": 0.50})
            continue
        weights, metadata = strategy.build_target_weights(partial_history)
        rows.append(
            {
                "date": as_of,
                "anchor": float(weights.get(strategy.DEFAULT_ANCHOR_SYMBOL, 0.0)),
                "satellite": float(weights.get(strategy.DEFAULT_SATELLITE_SYMBOL, 0.0)),
                "signal_state": metadata["signal_state"],
                "spread_z": metadata["spread_z"],
            }
        )
    targets = pd.DataFrame(rows).set_index("date")
    if strategy.DEFAULT_REBALANCE_FREQUENCY == "weekly":
        targets = targets.resample("W-FRI").last().reindex(targets.index, method="ffill").bfill()
    elif strategy.DEFAULT_REBALANCE_FREQUENCY == "monthly":
        targets = targets.resample("ME").last().reindex(targets.index, method="ffill").bfill()
    return targets[["anchor", "satellite"]].shift(1).fillna({"anchor": 0.50, "satellite": 0.50})


def _strategy_returns(close: pd.DataFrame, *, cost_bps: float) -> tuple[pd.Series, pd.DataFrame]:
    returns = close.pct_change().fillna(0.0)
    targets = _target_weights(close)
    turnover = targets.diff().abs().sum(axis=1).fillna(0.0)
    net = (targets * returns).sum(axis=1) - turnover * float(cost_bps) / 10_000.0
    return net, targets


def _slice(series: pd.Series, start: str | None, end: str | None) -> pd.Series:
    output = series
    if start:
        output = output.loc[pd.Timestamp(start):]
    if end:
        output = output.loc[: pd.Timestamp(end)]
    return output


def run(config: BacktestConfig) -> dict[str, Any]:
    close = _download_close(config)
    strategy_returns, targets = _strategy_returns(close, cost_bps=config.cost_bps)
    benchmark_returns = {
        "strategy": strategy_returns,
        "hsi_etf_02800": close["anchor"].pct_change().fillna(0.0),
        "hstech_etf_03033": close["satellite"].pct_change().fillna(0.0),
        "static_50_50": close.pct_change().fillna(0.0).mean(axis=1),
    }
    periods = {
        "full": (None, None),
        "train_2020_2023": (config.start, config.train_end),
        "oos_2024_2026": (config.oos_start, "2026-05-29"),
        "trailing_1y": ("2025-05-30", "2026-05-29"),
        "trailing_3y": ("2023-05-30", "2026-05-29"),
        "2021": ("2021-01-01", "2021-12-31"),
        "2022": ("2022-01-01", "2022-12-31"),
        "2023": ("2023-01-01", "2023-12-31"),
        "2024": ("2024-01-01", "2024-12-31"),
        "2025": ("2025-01-01", "2025-12-31"),
        "2026_ytd": ("2026-01-01", "2026-05-29"),
    }
    return {
        "config": asdict(config),
        "strategy_defaults": {
            "lookback_days": strategy.DEFAULT_LOOKBACK_DAYS,
            "entry_z": strategy.DEFAULT_ENTRY_Z,
            "exit_z": strategy.DEFAULT_EXIT_Z,
            "neutral_satellite_weight": strategy.DEFAULT_NEUTRAL_SATELLITE_WEIGHT,
            "oversold_satellite_weight": strategy.DEFAULT_OVERSOLD_SATELLITE_WEIGHT,
            "rich_satellite_weight": strategy.DEFAULT_RICH_SATELLITE_WEIGHT,
            "trend_window_days": strategy.DEFAULT_TREND_WINDOW_DAYS,
            "defensive_gross_exposure": strategy.DEFAULT_DEFENSIVE_GROSS_EXPOSURE,
            "rebalance_frequency": strategy.DEFAULT_REBALANCE_FREQUENCY,
            "cost_bps": config.cost_bps,
        },
        "data": {
            "start": close.index.min().date().isoformat(),
            "end": close.index.max().date().isoformat(),
            "rows": int(len(close)),
            "last_weights": targets.tail(1).to_dict("records")[0],
            "average_gross_exposure": float(targets.sum(axis=1).mean()),
            "average_daily_turnover": float(targets.diff().abs().sum(axis=1).mean()),
        },
        "metrics": {
            name: {period: _metrics(_slice(series, start, end)) for period, (start, end) in periods.items()}
            for name, series in benchmark_returns.items()
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Backtest HK index mean-reversion research candidate.")
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()
    payload = run(BacktestConfig())
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.json_output:
        args.json_output.write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
