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


def _market_history_frame(close: pd.DataFrame) -> pd.DataFrame:
    return (
        close.rename(columns={"anchor": strategy.DEFAULT_ANCHOR_SYMBOL, "satellite": strategy.DEFAULT_SATELLITE_SYMBOL})
        .reset_index(names="date")
        .melt(id_vars="date", var_name="symbol", value_name="close")
    )


def _apply_rebalance_cadence(targets: pd.DataFrame) -> pd.DataFrame:
    if strategy.DEFAULT_REBALANCE_FREQUENCY == "weekly":
        targets = targets.resample("W-FRI").last().reindex(targets.index, method="ffill").bfill()
    elif strategy.DEFAULT_REBALANCE_FREQUENCY == "monthly":
        targets = targets.resample("ME").last().reindex(targets.index, method="ffill").bfill()
    return targets[["anchor", "satellite"]].shift(1).fillna({"anchor": 0.50, "satellite": 0.50})


def _target_weights(close: pd.DataFrame) -> pd.DataFrame:
    market_history = _market_history_frame(close)
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
    return _apply_rebalance_cadence(targets)


def _mean_reversion_satellite_weight(spread_z: float) -> float:
    if spread_z <= -float(strategy.DEFAULT_ENTRY_Z):
        return float(strategy.DEFAULT_OVERSOLD_SATELLITE_WEIGHT)
    if spread_z >= float(strategy.DEFAULT_ENTRY_Z):
        return float(strategy.DEFAULT_RICH_SATELLITE_WEIGHT)
    if abs(spread_z) <= float(strategy.DEFAULT_EXIT_Z):
        return float(strategy.DEFAULT_NEUTRAL_SATELLITE_WEIGHT)
    return float(strategy.DEFAULT_NEUTRAL_SATELLITE_WEIGHT)


def _custom_target_weights(
    close: pd.DataFrame,
    *,
    variant: str,
    defensive_gross_exposure: float,
) -> pd.DataFrame:
    ratio = (close["satellite"] / close["anchor"]).map(math.log)
    ratio_mean = ratio.rolling(int(strategy.DEFAULT_LOOKBACK_DAYS)).mean()
    ratio_std = ratio.rolling(int(strategy.DEFAULT_LOOKBACK_DAYS)).std(ddof=0)
    spread_z = (ratio - ratio_mean) / ratio_std
    anchor_ma = close["anchor"].rolling(int(strategy.DEFAULT_TREND_WINDOW_DAYS)).mean()
    satellite_ma = close["satellite"].rolling(int(strategy.DEFAULT_TREND_WINDOW_DAYS)).mean()

    rows: list[dict[str, Any]] = []
    for position, as_of in enumerate(close.index):
        if position + 1 < strategy.DEFAULT_MIN_HISTORY_DAYS:
            rows.append({"date": as_of, "anchor": 0.50, "satellite": 0.50})
            continue
        latest_z = float(spread_z.iloc[position])
        if pd.isna(latest_z) or not math.isfinite(latest_z):
            latest_z = 0.0
        satellite_weight = _mean_reversion_satellite_weight(latest_z)
        gross_exposure = 1.0
        anchor_trend_positive = bool(close["anchor"].iloc[position] >= anchor_ma.iloc[position])
        satellite_trend_positive = bool(close["satellite"].iloc[position] >= satellite_ma.iloc[position])
        if variant == "legacy_both_below_trend":
            defensive = not (anchor_trend_positive or satellite_trend_positive)
        elif variant == "no_trend_filter":
            defensive = False
        else:
            raise ValueError(f"unsupported variant: {variant}")
        if defensive:
            gross_exposure = float(defensive_gross_exposure)
            satellite_weight = min(satellite_weight, float(strategy.DEFAULT_DEFENSIVE_SATELLITE_WEIGHT))
        rows.append(
            {
                "date": as_of,
                "anchor": gross_exposure * (1.0 - satellite_weight),
                "satellite": gross_exposure * satellite_weight,
            }
        )
    targets = pd.DataFrame(rows).set_index("date")
    return _apply_rebalance_cadence(targets)


def _strategy_returns(
    close: pd.DataFrame,
    *,
    cost_bps: float,
    targets: pd.DataFrame | None = None,
) -> tuple[pd.Series, pd.DataFrame]:
    returns = close.pct_change().fillna(0.0)
    if targets is None:
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
    legacy_returns, legacy_targets = _strategy_returns(
        close,
        cost_bps=config.cost_bps,
        targets=_custom_target_weights(close, variant="legacy_both_below_trend", defensive_gross_exposure=0.25),
    )
    no_filter_returns, no_filter_targets = _strategy_returns(
        close,
        cost_bps=config.cost_bps,
        targets=_custom_target_weights(close, variant="no_trend_filter", defensive_gross_exposure=1.0),
    )
    benchmark_returns = {
        "strategy": strategy_returns,
        "legacy_both_below_200ma": legacy_returns,
        "no_trend_filter": no_filter_returns,
        "hsi_etf_02800": close["anchor"].pct_change().fillna(0.0),
        "hstech_etf_03033": close["satellite"].pct_change().fillna(0.0),
        "static_50_50": close.pct_change().fillna(0.0).mean(axis=1),
    }
    periods = {
        "full": (None, None),
        "post_warmup_full": ("2021-09-01", "2026-05-29"),
        "train_2020_2023": (config.start, config.train_end),
        "train_2021_2023": ("2021-09-01", config.train_end),
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
            "defensive_trigger": "anchor_below_trend",
            "defensive_gross_exposure": strategy.DEFAULT_DEFENSIVE_GROSS_EXPOSURE,
            "defensive_satellite_weight": strategy.DEFAULT_DEFENSIVE_SATELLITE_WEIGHT,
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
            "post_warmup_average_gross_exposure": float(targets.loc[pd.Timestamp("2021-09-01") :].sum(axis=1).mean()),
            "post_warmup_average_daily_turnover": float(
                targets.loc[pd.Timestamp("2021-09-01") :].diff().abs().sum(axis=1).mean()
            ),
            "legacy_last_weights": legacy_targets.tail(1).to_dict("records")[0],
            "no_filter_last_weights": no_filter_targets.tail(1).to_dict("records")[0],
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
