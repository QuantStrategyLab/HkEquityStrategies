#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

import pandas as pd


YAHOO_SYMBOLS = {
    "02800": "2800.HK",  # Tracker Fund of Hong Kong, HSI exposure
    "02822": "2822.HK",  # CSOP FTSE China A50 ETF
    "03188": "3188.HK",  # ChinaAMC CSI 300 ETF
    "03033": "3033.HK",  # CSOP Hang Seng TECH Index ETF
    "02834": "2834.HK",  # iShares NASDAQ 100 ETF
    "02840": "2840.HK",  # SPDR Gold Shares
    "03175": "3175.HK",  # Samsung S&P GSCI Crude Oil ER Futures ETF
    "03110": "3110.HK",  # Global X Hang Seng High Dividend Yield ETF
}

ETF_DESCRIPTIONS = {
    "02800": "Tracker Fund of Hong Kong / HSI",
    "02822": "CSOP FTSE China A50 ETF",
    "03188": "ChinaAMC CSI 300 ETF",
    "03033": "CSOP Hang Seng TECH Index ETF",
    "02834": "iShares NASDAQ 100 ETF",
    "02840": "SPDR Gold Shares",
    "03175": "Samsung S&P GSCI Crude Oil ER Futures ETF",
    "03110": "Global X Hang Seng High Dividend Yield ETF",
}

WATCHLIST_SYMBOLS = {
    "03010": "iShares Core MSCI AC Asia ex Japan Index ETF; yfinance adjusted series had a large discontinuity in this run.",
    "03195": "Hang Seng S&P 500 Index ETF; history starts in 2024, too short for 2021-2026 walk-forward comparison.",
    "03040": "Global X MSCI China ETF; history starts in 2024, too short for this baseline run.",
    "03442": "CSOP Hang Seng HK-US TECH ETF; history starts in 2025, too short for this baseline run.",
}

WeightingMode = Literal["equal", "inverse_volatility"]
RebalanceFrequency = Literal["monthly", "weekly"]


@dataclass(frozen=True)
class BacktestConfig:
    start: str = "2020-08-27"
    end: str = "2026-06-01"
    analysis_start: str = "2021-09-01"
    train_end: str = "2023-12-29"
    oos_start: str = "2024-01-01"
    data_end: str = "2026-05-29"


@dataclass(frozen=True)
class RotationConfig:
    momentum_window_days: int = 252
    trend_window_days: int = 200
    volatility_window_days: int = 63
    top_n: int = 2
    weighting_mode: WeightingMode = "inverse_volatility"
    rebalance_frequency: RebalanceFrequency = "monthly"
    min_momentum: float = 0.0
    min_history_days: int = 260
    cost_bps: float = 10.0


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
    close = close.loc[:, list(YAHOO_SYMBOLS)].ffill().dropna(how="any")
    return close


def _eligible_scores(close: pd.DataFrame, rotation: RotationConfig) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    returns = close.pct_change().fillna(0.0)
    momentum = close.pct_change(rotation.momentum_window_days)
    trend = close / close.rolling(rotation.trend_window_days).mean() - 1.0
    volatility = returns.rolling(rotation.volatility_window_days).std(ddof=0) * math.sqrt(252)
    score = momentum / volatility.replace(0.0, pd.NA)
    return momentum, trend, volatility, score


def _finite_float(value: Any, *, default: float = float("nan")) -> float:
    try:
        output = float(value)
    except (TypeError, ValueError):
        return default
    return output if math.isfinite(output) else default


def _weights_for_date(close: pd.DataFrame, as_of: pd.Timestamp, rotation: RotationConfig) -> dict[str, float]:
    history = close.loc[:as_of]
    if len(history) < rotation.min_history_days:
        return {}

    momentum, trend, volatility, score = _eligible_scores(history, rotation)
    rows: list[tuple[str, float, float]] = []
    for symbol in close.columns:
        symbol_momentum = _finite_float(momentum[symbol].iloc[-1])
        symbol_trend = _finite_float(trend[symbol].iloc[-1])
        symbol_volatility = _finite_float(volatility[symbol].iloc[-1])
        symbol_score = _finite_float(score[symbol].iloc[-1], default=float("-inf"))
        eligible = (
            math.isfinite(symbol_momentum)
            and math.isfinite(symbol_trend)
            and math.isfinite(symbol_volatility)
            and math.isfinite(symbol_score)
            and symbol_momentum > rotation.min_momentum
            and symbol_trend > 0.0
            and symbol_volatility > 0.0
        )
        if eligible:
            rows.append((symbol, symbol_score, symbol_volatility))

    ranked = sorted(rows, key=lambda row: row[1], reverse=True)[: rotation.top_n]
    if not ranked:
        return {}
    if rotation.weighting_mode == "equal":
        return {symbol: 1.0 / len(ranked) for symbol, _score, _vol in ranked}
    if rotation.weighting_mode != "inverse_volatility":
        raise ValueError("weighting_mode must be 'inverse_volatility' or 'equal'")
    inverse_vols = [(symbol, 1.0 / max(volatility_value, 1e-12)) for symbol, _score, volatility_value in ranked]
    total_inverse_vol = sum(value for _symbol, value in inverse_vols)
    return {symbol: value / total_inverse_vol for symbol, value in inverse_vols}


def _rebalance_dates(close: pd.DataFrame, frequency: RebalanceFrequency) -> pd.DatetimeIndex:
    if frequency == "monthly":
        return close.resample("ME").last().index
    if frequency == "weekly":
        return close.resample("W-FRI").last().index
    raise ValueError("rebalance_frequency must be 'monthly' or 'weekly'")


def _target_weights(close: pd.DataFrame, rotation: RotationConfig) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for target_date in _rebalance_dates(close, rotation.rebalance_frequency):
        position = close.index.searchsorted(target_date, side="right") - 1
        if position < 0:
            continue
        as_of = pd.Timestamp(close.index[position])
        weights = _weights_for_date(close, as_of, rotation)
        rows.append({"date": as_of, **{symbol: float(weights.get(symbol, 0.0)) for symbol in close.columns}})
    targets = pd.DataFrame(rows).set_index("date")
    targets = targets.reindex(close.index, method="ffill").fillna(0.0)
    return targets[list(close.columns)].shift(1).fillna(0.0)


def _strategy_returns(close: pd.DataFrame, rotation: RotationConfig) -> tuple[pd.Series, pd.DataFrame]:
    returns = close.pct_change().fillna(0.0)
    targets = _target_weights(close, rotation)
    turnover = targets.diff().abs().sum(axis=1).fillna(0.0)
    net = (targets * returns).sum(axis=1) - turnover * rotation.cost_bps / 10_000.0
    return net, targets


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
    return {
        "days": int(len(returns)),
        "annual_return": annual_return,
        "max_drawdown": float(drawdown.min()),
        "annual_volatility": float(returns.std(ddof=0) * math.sqrt(252)),
        "total_return": float(equity.iloc[-1] - 1.0),
    }


def _slice(series: pd.Series, start: str | None, end: str | None) -> pd.Series:
    output = series
    if start:
        output = output.loc[pd.Timestamp(start) :]
    if end:
        output = output.loc[: pd.Timestamp(end)]
    return output


def run(config: BacktestConfig, rotation: RotationConfig) -> dict[str, Any]:
    close = _download_close(config)
    strategy_returns, targets = _strategy_returns(close, rotation)
    strategy_returns = strategy_returns.loc[pd.Timestamp(config.analysis_start) :]
    targets = targets.loc[strategy_returns.index]
    close = close.loc[strategy_returns.index]

    benchmark_returns = {
        "strategy": strategy_returns,
        "static_equal_weight": close.pct_change().fillna(0.0).mean(axis=1),
        **{
            f"{symbol}_{ETF_DESCRIPTIONS[symbol]}": close[symbol].pct_change().fillna(0.0)
            for symbol in close.columns
        },
    }
    periods = {
        "full": (None, None),
        "train_2021_2023": (config.analysis_start, config.train_end),
        "oos_2024_2026": (config.oos_start, config.data_end),
        "trailing_1y": ("2025-05-30", config.data_end),
        "trailing_3y": ("2023-05-30", config.data_end),
        "2021": ("2021-01-01", "2021-12-31"),
        "2022": ("2022-01-01", "2022-12-31"),
        "2023": ("2023-01-01", "2023-12-31"),
        "2024": ("2024-01-01", "2024-12-31"),
        "2025": ("2025-01-01", "2025-12-31"),
        "2026_ytd": ("2026-01-01", config.data_end),
    }
    return {
        "config": asdict(config),
        "rotation_config": asdict(rotation),
        "yahoo_symbols": YAHOO_SYMBOLS,
        "etf_descriptions": ETF_DESCRIPTIONS,
        "watchlist_symbols": WATCHLIST_SYMBOLS,
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
    parser = argparse.ArgumentParser(description="Backtest a HK-listed global ETF rotation research candidate.")
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()
    payload = run(BacktestConfig(), RotationConfig())
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.json_output:
        args.json_output.write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
