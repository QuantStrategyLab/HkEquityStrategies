#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from hk_equity_strategies.strategies import hk_index_mean_reversion as strategy

YAHOO_SYMBOLS = {
    "hsi": "2800.HK",
    "hstech": "3033.HK",
    "hsi_2x_long": "7200.HK",
    "hsi_2x_short": "7500.HK",
    "hstech_2x_long": "7226.HK",
    "hstech_2x_short": "7552.HK",
}


@dataclass(frozen=True)
class BacktestConfig:
    start: str = "2020-08-27"
    end: str = "2026-06-01"
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
    return close.dropna(how="all")


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
    drawdown = equity / equity.cummax() - 1.0
    return {
        "days": int(len(returns)),
        "annual_return": float(equity.iloc[-1] ** (1 / years) - 1) if years > 0 else 0.0,
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


def _signal_frame(close: pd.DataFrame) -> pd.DataFrame:
    ratio = (close["hstech"] / close["hsi"]).map(math.log)
    ratio_mean = ratio.rolling(strategy.DEFAULT_LOOKBACK_DAYS).mean()
    ratio_std = ratio.rolling(strategy.DEFAULT_LOOKBACK_DAYS).std(ddof=0)
    output = pd.DataFrame(index=close.index)
    output["spread_z"] = ((ratio - ratio_mean) / ratio_std).fillna(0.0)
    output["hsi_bull"] = close["hsi"] >= close["hsi"].rolling(strategy.DEFAULT_TREND_WINDOW_DAYS).mean()
    output["hstech_bull"] = close["hstech"] >= close["hstech"].rolling(strategy.DEFAULT_TREND_WINDOW_DAYS).mean()
    return output


def _apply_weekly_review(targets: pd.DataFrame) -> pd.DataFrame:
    return targets.resample("W-FRI").last().reindex(targets.index, method="ffill").fillna(0.0).shift(1).fillna(0.0)


def _target_weights(close: pd.DataFrame, *, variant: str) -> pd.DataFrame:
    signal = _signal_frame(close)
    columns = ["hsi_2x_long", "hsi_2x_short", "hstech_2x_long", "hstech_2x_short"]
    rows: list[dict[str, float | pd.Timestamp]] = []
    for position, as_of in enumerate(close.index):
        row: dict[str, float | pd.Timestamp] = {"date": as_of, **{column: 0.0 for column in columns}}
        if position + 1 < strategy.DEFAULT_MIN_HISTORY_DAYS:
            rows.append(row)
            continue

        spread_z = float(signal.loc[as_of, "spread_z"])
        hsi_bull = bool(signal.loc[as_of, "hsi_bull"])
        hstech_bull = bool(signal.loc[as_of, "hstech_bull"])
        satellite_cheap = spread_z <= -float(strategy.DEFAULT_ENTRY_Z)
        satellite_rich = spread_z >= float(strategy.DEFAULT_ENTRY_Z)

        if variant == "hstech_2x_directional_anchor_filter":
            if satellite_cheap and hsi_bull:
                row["hstech_2x_long"] = 1.0
            elif satellite_rich:
                row["hstech_2x_short"] = 1.0
        elif variant == "hstech_2x_directional_no_filter":
            if satellite_cheap:
                row["hstech_2x_long"] = 1.0
            elif satellite_rich:
                row["hstech_2x_short"] = 1.0
        elif variant == "relative_pair_2x_anchor_filter":
            if satellite_cheap and hsi_bull:
                row["hstech_2x_long"] = 0.5
                row["hsi_2x_short"] = 0.5
            elif satellite_rich:
                row["hsi_2x_long"] = 0.5
                row["hstech_2x_short"] = 0.5
        elif variant == "relative_pair_2x_no_filter":
            if satellite_cheap:
                row["hstech_2x_long"] = 0.5
                row["hsi_2x_short"] = 0.5
            elif satellite_rich:
                row["hsi_2x_long"] = 0.5
                row["hstech_2x_short"] = 0.5
        elif variant == "relative_pair_2x_both_bull_long":
            if satellite_cheap and hsi_bull and hstech_bull:
                row["hstech_2x_long"] = 0.5
                row["hsi_2x_short"] = 0.5
            elif satellite_rich:
                row["hsi_2x_long"] = 0.5
                row["hstech_2x_short"] = 0.5
        else:
            raise ValueError(f"unsupported variant: {variant}")
        rows.append(row)
    return _apply_weekly_review(pd.DataFrame(rows).set_index("date"))


def _strategy_returns(close: pd.DataFrame, *, variant: str, cost_bps: float) -> tuple[pd.Series, pd.DataFrame]:
    targets = _target_weights(close, variant=variant)
    product_close = close.reindex(columns=targets.columns)
    product_returns = product_close.pct_change().fillna(0.0)
    targets = targets.where(product_close.notna(), 0.0)
    turnover = targets.diff().abs().sum(axis=1).fillna(0.0)
    net = (targets * product_returns).sum(axis=1) - turnover * float(cost_bps) / 10_000.0
    common_index = close.dropna(how="any").index
    return net.loc[common_index], targets.loc[common_index]


def run(config: BacktestConfig) -> dict[str, object]:
    close = _download_close(config)
    periods = {
        "full_common": (None, None),
        "post_warmup_full": ("2021-09-01", "2026-05-29"),
        "train_2021_2023": ("2021-09-01", "2023-12-29"),
        "oos_2024_2026": ("2024-01-01", "2026-05-29"),
        "trailing_1y": ("2025-05-30", "2026-05-29"),
        "trailing_3y": ("2023-05-30", "2026-05-29"),
        "2021": ("2021-01-01", "2021-12-31"),
        "2022": ("2022-01-01", "2022-12-31"),
        "2023": ("2023-01-01", "2023-12-31"),
        "2024": ("2024-01-01", "2024-12-31"),
        "2025": ("2025-01-01", "2025-12-31"),
        "2026_ytd": ("2026-01-01", "2026-05-29"),
    }
    variants = (
        "hstech_2x_directional_anchor_filter",
        "hstech_2x_directional_no_filter",
        "relative_pair_2x_anchor_filter",
        "relative_pair_2x_no_filter",
        "relative_pair_2x_both_bull_long",
    )
    returns: dict[str, pd.Series] = {}
    targets: dict[str, pd.DataFrame] = {}
    for variant in variants:
        returns[variant], targets[variant] = _strategy_returns(close, variant=variant, cost_bps=config.cost_bps)

    common_index = close.dropna(how="any").index
    benchmarks = {
        "hsi_02800": close["hsi"].pct_change().fillna(0.0).loc[common_index],
        "hstech_03033": close["hstech"].pct_change().fillna(0.0).loc[common_index],
        "hstech_2x_long_07226": close["hstech_2x_long"].pct_change().fillna(0.0).loc[common_index],
        "hstech_2x_short_07552": close["hstech_2x_short"].pct_change().fillna(0.0).loc[common_index],
    }
    all_returns = {**returns, **benchmarks}
    return {
        "config": asdict(config),
        "yahoo_symbols": YAHOO_SYMBOLS,
        "data": {
            "start_by_symbol": {
                column: close[column].dropna().index.min().date().isoformat() for column in close.columns
            },
            "end_by_symbol": {
                column: close[column].dropna().index.max().date().isoformat() for column in close.columns
            },
            "common_start": common_index.min().date().isoformat(),
            "common_end": common_index.max().date().isoformat(),
            "common_rows": int(len(common_index)),
        },
        "metrics": {
            name: {period: _metrics(_slice(series, start, end)) for period, (start, end) in periods.items()}
            for name, series in all_returns.items()
        },
        "diagnostics": {
            variant: {
                "average_gross_exposure": float(targets[variant].abs().sum(axis=1).mean()),
                "average_daily_turnover": float(targets[variant].diff().abs().sum(axis=1).mean()),
                "last_weights": targets[variant].tail(1).to_dict("records")[0],
            }
            for variant in variants
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Backtest HK index mean-reversion leveraged/inverse research variants.")
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()
    payload = run(BacktestConfig())
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.json_output:
        args.json_output.write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
