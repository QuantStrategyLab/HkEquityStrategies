#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from hk_equity_strategies.strategies import hk_etf_regime_rotation as strategy


YAHOO_SYMBOLS = {
    "02800": "2800.HK",
    "02822": "2822.HK",
    "02840": "2840.HK",
    "03033": "3033.HK",
    "03110": "3110.HK",
    "03188": "3188.HK",
}


@dataclass(frozen=True)
class BacktestConfig:
    start: str = "2020-08-27"
    end: str = "2026-06-01"
    analysis_start: str = "2021-09-01"
    cost_bps: float = 10.0
    train_end: str = "2023-12-29"
    oos_start: str = "2024-01-01"


def _download_close(config: BacktestConfig) -> pd.DataFrame:
    try:
        import yfinance as yf
    except Exception as exc:  # pragma: no cover - research helper only
        raise SystemExit("yfinance is required for this research script; install it outside production deps") from exc
    raw = yf.download(
        list(YAHOO_SYMBOLS.values()),
        start=config.start,
        end=config.end,
        auto_adjust=True,
        progress=False,
        threads=False,
    )
    close = raw["Close"].rename(columns={yahoo: symbol for symbol, yahoo in YAHOO_SYMBOLS.items()})
    close = close.loc[:, list(strategy.DEFAULT_UNIVERSE_SYMBOLS)].ffill().dropna(how="any")
    return close


def _market_history_until(close: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    return (
        close.loc[:as_of]
        .reset_index(names="date")
        .melt(id_vars="date", var_name="symbol", value_name="close")
    )


def _metrics(returns: pd.Series) -> dict[str, float | int]:
    returns = returns.dropna()
    if returns.empty:
        return {
            "days": 0,
            "annual_return": 0.0,
            "max_drawdown": 0.0,
            "annual_volatility": 0.0,
            "total_return": 0.0,
        }
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
    month_end_dates = close.resample("ME").last().index
    rows: list[dict[str, Any]] = []
    for target_date in month_end_dates:
        position = close.index.searchsorted(target_date, side="right") - 1
        if position < 0:
            continue
        as_of = pd.Timestamp(close.index[position])
        partial_history = _market_history_until(close, as_of)
        if partial_history["date"].nunique() < strategy.DEFAULT_MIN_HISTORY_DAYS:
            weights: dict[str, float] = {}
            metadata = {"signal_state": "warmup", "selected_symbols": (), "cash_weight": 1.0}
        else:
            weights, metadata = strategy.build_target_weights(partial_history)
        rows.append(
            {
                "date": as_of,
                **{symbol: float(weights.get(symbol, 0.0)) for symbol in strategy.DEFAULT_UNIVERSE_SYMBOLS},
                "signal_state": metadata["signal_state"],
                "selected_symbols": ",".join(metadata["selected_symbols"]),
                "cash_weight": float(metadata["cash_weight"]),
            }
        )
    targets = pd.DataFrame(rows).set_index("date")
    targets = targets.reindex(close.index, method="ffill").fillna(0.0)
    return targets[list(strategy.DEFAULT_UNIVERSE_SYMBOLS)].shift(1).fillna(0.0)


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
    strategy_returns = strategy_returns.loc[pd.Timestamp(config.analysis_start):]
    targets = targets.loc[strategy_returns.index]
    close = close.loc[strategy_returns.index]
    benchmark_returns = {
        "strategy": strategy_returns,
        "hsi_etf_02800": close["02800"].pct_change().fillna(0.0),
        "hstech_etf_03033": close["03033"].pct_change().fillna(0.0),
        "gold_etf_02840": close["02840"].pct_change().fillna(0.0),
        "high_dividend_etf_03110": close["03110"].pct_change().fillna(0.0),
        "static_equal_weight": close.pct_change().fillna(0.0).mean(axis=1),
    }
    periods = {
        "full": (None, None),
        "train_2021_2023": (config.analysis_start, config.train_end),
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
        "yahoo_symbols": YAHOO_SYMBOLS,
        "strategy_defaults": {
            "universe_symbols": strategy.DEFAULT_UNIVERSE_SYMBOLS,
            "momentum_window_days": strategy.DEFAULT_MOMENTUM_WINDOW_DAYS,
            "trend_window_days": strategy.DEFAULT_TREND_WINDOW_DAYS,
            "volatility_window_days": strategy.DEFAULT_VOLATILITY_WINDOW_DAYS,
            "top_n": strategy.DEFAULT_TOP_N,
            "weighting_mode": strategy.DEFAULT_WEIGHTING_MODE,
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
    parser = argparse.ArgumentParser(description="Backtest HK ETF regime rotation research candidate.")
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()
    payload = run(BacktestConfig())
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.json_output:
        args.json_output.write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
