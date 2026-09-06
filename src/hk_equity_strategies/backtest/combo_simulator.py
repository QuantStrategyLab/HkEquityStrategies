"""Research combo backtest for HK ETF rotation + dividend proxy."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Literal, Mapping

import pandas as pd

from hk_equity_strategies.backtest.etf_rotation_simulator import (
    HkRotationBacktestConfig,
    HkRotationBacktestResult,
    StrategySignalFn,
    build_rebalance_dates,
    compute_backtest_metrics,
    rebalance_holdings,
)
from hk_equity_strategies.strategies.etf_rotation_core import build_close_matrix
from hk_equity_strategies.strategies.hk_equity_combo import (
    DEFAULT_DIVIDEND_WEIGHT,
    DEFAULT_ETF_WEIGHT,
    _apply_dividend_regime,
)

ComboMode = Literal["static", "dynamic"]
DIVIDEND_SYMBOL = "03110"
DIVIDEND_ANNUAL_VOL_SCALE = 0.85


@dataclass(frozen=True)
class HkComboBacktestConfig:
    etf_weight: float = DEFAULT_ETF_WEIGHT
    dividend_weight: float = DEFAULT_DIVIDEND_WEIGHT
    combo_mode: ComboMode = "dynamic"
    min_history_days: int = 260
    cost_bps: float = 10.0
    rebalance_frequency: str = "monthly"
    volatility_window_days: int = 63


def _simulate_dividend_returns(close: pd.DataFrame, *, volatility_window_days: int) -> pd.Series:
    returns = close.pct_change().fillna(0.0)
    if DIVIDEND_SYMBOL in close.columns:
        raw = returns[DIVIDEND_SYMBOL]
    else:
        raw = returns.mean(axis=1)
    rolling_vol = raw.rolling(volatility_window_days).std(ddof=0) * math.sqrt(252)
    target_vol = rolling_vol * DIVIDEND_ANNUAL_VOL_SCALE
    scale = target_vol / rolling_vol.replace(0.0, pd.NA)
    return raw * scale.fillna(1.0).clip(upper=2.0)


def _breadth_regime(close: pd.DataFrame, as_of: pd.Timestamp) -> str:
    window = close.loc[:as_of]
    if len(window) < 100:
        return "risk_on"
    sma200 = window.rolling(200, min_periods=100).mean()
    above_sma = (window.iloc[-1] > sma200.iloc[-1]).sum()
    breadth = above_sma / max(len(close.columns), 1)
    if breadth < 0.30:
        return "hard_defense"
    if breadth < 0.45:
        return "soft_defense"
    return "risk_on"


def _history_slice(market_history: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    frame = market_history.copy()
    frame["date"] = pd.to_datetime(frame["date"], utc=False).dt.tz_localize(None).dt.normalize()
    return frame.loc[frame["date"] <= as_of]


def _combo_target_weights(
    market_history: pd.DataFrame,
    close: pd.DataFrame,
    *,
    signal_fn: StrategySignalFn,
    rotation_config: HkRotationBacktestConfig,
    combo_config: HkComboBacktestConfig,
    strategy_kwargs: Mapping[str, Any],
    asset_columns: pd.Index,
) -> pd.DataFrame:
    """Build event targets only; NaN means hold prior shares/cash (no free reset)."""
    rebalance_dates = build_rebalance_dates(
        pd.DatetimeIndex(close.index),
        frequency=combo_config.rebalance_frequency,
    )
    rebalance_dates = rebalance_dates[rebalance_dates <= close.index[-1]]
    rows: list[dict[str, Any]] = []
    for target_date in rebalance_dates:
        position = close.index.searchsorted(target_date, side="right") - 1
        if position < 0:
            continue
        as_of = pd.Timestamp(close.index[position])
        history = _history_slice(market_history, as_of)
        if len(history["date"].drop_duplicates()) < int(rotation_config.min_history_days):
            etf_weights: dict[str, float] = {}
        else:
            etf_weights, _metadata = signal_fn(history, **dict(strategy_kwargs))

        if combo_config.combo_mode == "static":
            etf_target_weight = combo_config.etf_weight
            div_target_weight = combo_config.dividend_weight
        else:
            regime = _breadth_regime(close, as_of)
            etf_target_weight, div_target_weight, _ = _apply_dividend_regime(
                combo_config.etf_weight,
                regime,
            )

        selected = {symbol: float(etf_weights.get(symbol, 0.0)) for symbol in close.columns}
        if any(not math.isfinite(weight) or weight < 0.0 for weight in selected.values()) or math.fsum(
            selected.values()
        ) > 1.0:
            raise ValueError("target weights must be finite, non-negative and sum to at most one")
        etf_gross = math.fsum(selected.values())
        if etf_gross > 0.0:
            scaled = {
                symbol: weight * etf_target_weight / etf_gross for symbol, weight in selected.items()
            }
        else:
            scaled = {symbol: 0.0 for symbol in close.columns}

        row = {symbol: float(scaled.get(symbol, 0.0)) for symbol in asset_columns}
        row[DIVIDEND_SYMBOL] = float(row.get(DIVIDEND_SYMBOL, 0.0)) + float(div_target_weight)
        if any(not math.isfinite(weight) or weight < 0.0 for weight in row.values()) or math.fsum(
            row.values()
        ) > 1.0:
            raise ValueError("combo target weights must be finite, non-negative and sum to at most one")
        rows.append({"date": as_of, **row})

    targets = pd.DataFrame(rows, columns=["date", *asset_columns]).set_index("date")
    return targets.reindex(close.index).shift(1)


def _combo_strategy_returns(
    market_history: pd.DataFrame,
    close: pd.DataFrame,
    *,
    signal_fn: StrategySignalFn,
    rotation_config: HkRotationBacktestConfig,
    combo_config: HkComboBacktestConfig,
    strategy_kwargs: Mapping[str, Any],
) -> pd.Series:
    dividend_returns = _simulate_dividend_returns(
        close,
        volatility_window_days=combo_config.volatility_window_days,
    )
    prices = close.copy()
    if DIVIDEND_SYMBOL not in prices.columns:
        prices[DIVIDEND_SYMBOL] = 1.0
    prices[DIVIDEND_SYMBOL] = (1.0 + dividend_returns.reindex(prices.index).fillna(0.0)).cumprod()

    cost_rate = float(combo_config.cost_bps) / 10_000.0
    if not math.isfinite(cost_rate) or not 0.0 <= cost_rate < 1.0:
        raise ValueError("cost_bps must be finite and in [0, 10000)")

    targets = _combo_target_weights(
        market_history,
        close,
        signal_fn=signal_fn,
        rotation_config=rotation_config,
        combo_config=combo_config,
        strategy_kwargs=strategy_kwargs,
        asset_columns=prices.columns,
    )
    shares = pd.Series(0.0, index=prices.columns)
    cash = equity = 1.0
    net = pd.Series(0.0, index=prices.index)
    for position in range(1, len(prices)):
        target = targets.iloc[position]
        if target.notna().any():
            shares, cash, _fees = rebalance_holdings(
                shares,
                cash,
                prices.iloc[position - 1],
                target.fillna(0.0),
                cost_rate=cost_rate,
            )
        held = shares > 0.0
        mark_prices = prices.iloc[position][held]
        if any(not math.isfinite(price) or price <= 0.0 for price in mark_prices):
            raise ValueError("held assets require positive finite mark prices")
        marked_equity = cash + float((shares[held] * mark_prices).sum())
        net.iloc[position] = marked_equity / equity - 1.0
        equity = marked_equity
    return net


def run_combo_backtest(
    market_history: pd.DataFrame,
    strategy_signal_fn: StrategySignalFn,
    *,
    combo_config: HkComboBacktestConfig | None = None,
    rotation_config: HkRotationBacktestConfig | None = None,
    universe_symbols: Any = None,
    strategy_kwargs: Mapping[str, Any] | None = None,
) -> HkRotationBacktestResult:
    combo = combo_config or HkComboBacktestConfig()
    rotation = rotation_config or HkRotationBacktestConfig(
        min_history_days=combo.min_history_days,
        cost_bps=combo.cost_bps,
        rebalance_frequency=combo.rebalance_frequency,
    )
    close = build_close_matrix(market_history, universe_symbols=universe_symbols)
    if len(close) < int(combo.min_history_days):
        raise ValueError(
            f"market_history requires at least {int(combo.min_history_days)} overlapping trading days"
        )
    net = _combo_strategy_returns(
        market_history,
        close,
        signal_fn=strategy_signal_fn,
        rotation_config=rotation,
        combo_config=combo,
        strategy_kwargs=dict(strategy_kwargs or {}),
    )
    return HkRotationBacktestResult(daily_returns=net, metrics=compute_backtest_metrics(net))


__all__ = [
    "DIVIDEND_SYMBOL",
    "HkComboBacktestConfig",
    "run_combo_backtest",
]
