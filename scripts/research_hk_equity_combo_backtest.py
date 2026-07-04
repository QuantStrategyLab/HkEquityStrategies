#!/usr/bin/env python3
"""
Compare static vs dynamic combo of two HK equity strategies:

  - HK Global ETF Tactical Rotation  (60 %)
  - HK Low-Vol Dividend Quality Snapshot  (40 %)

The ETF leg reuses the backtest runner from the existing ETF rotation script.
The dividend leg is simulated from the same underlying ETF data with a lower
volatility / return profile (defensive dividend stocks).

Dynamic mode applies a "breadth-regime" overlay to the dividend leg weight:
  - risk_on       : full 40 % weight
  - soft_defense  : cut to 20 %
  - hard_defense  : cut to  0 %

Usage:
    python scripts/research_hk_equity_combo_backtest.py [--json-output PATH]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

import pandas as pd

# ---------------------------------------------------------------------------
# Reuse the existing ETF rotation backtest infrastructure
# ---------------------------------------------------------------------------
# We import the function-level utilities so that any future changes to the
# ETF backtest are picked up automatically.
_SCRIPTS_DIR = str(Path(__file__).resolve().parent if "__file__" in dir() else Path.cwd())
sys.path.insert(0, _SCRIPTS_DIR)

from research_hk_global_etf_tactical_rotation_backtest import (  # noqa: E402
    BacktestConfig,
    RotationConfig,
    _download_close,
    _metrics,
    _rebalance_dates,
    _slice,
    _strategy_returns,
    _target_weights,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ETF_WEIGHT = 0.60
DIVIDEND_WEIGHT = 0.40

DYNAMIC_WEIGHT_MAP: dict[str, float] = {
    "risk_on": 0.40,
    "soft_defense": 0.49,
    "hard_defense": 0.70,
}

# Dividend-style simulation parameters applied to the ETF-eligible universe.
# The dividend leg targets a defensive subset (high-dividend / low-beta names),
# approximated here by the existing 03110 (Global X Hang Seng High Dividend
# Yield ETF) or a blended basket.
DIVIDEND_SYMBOL = "03110"  # High-dividend proxy from the ETF universe
DIVIDEND_ANNUAL_VOL_SCALE = 0.85  # Dividend stocks are ~15 % less volatile

# ---------------------------------------------------------------------------
# Dividend-leg simulation helpers
# ---------------------------------------------------------------------------

def _simulate_dividend_returns(
    close: pd.DataFrame,
    config: BacktestConfig,
    rotation: RotationConfig,
) -> pd.Series:
    """Simulate a low-vol dividend stock basket return series.

    Uses the 03110 (High Dividend Yield ETF) from the downloaded universe as
    the proxy for the dividend stock basket. If the symbol is not available,
    falls back to the equal-weighted mean of the entire universe with a
    volatility dampener.
    """
    returns = close.pct_change().fillna(0.0)

    if DIVIDEND_SYMBOL in close.columns:
        raw = returns[DIVIDEND_SYMBOL]
    else:
        # Fallback: equal-weight all names and down-scale vol
        raw = returns.mean(axis=1)

    # Apply a volatility scale to approximate the defensive dividend profile
    rolling_vol = raw.rolling(rotation.volatility_window_days).std(ddof=0) * math.sqrt(252)
    target_vol = rolling_vol * DIVIDEND_ANNUAL_VOL_SCALE
    scale = target_vol / rolling_vol.replace(0.0, pd.NA)
    simulated = raw * scale.fillna(1.0).clip(upper=2.0)

    # Zero out transaction costs at the simulated level (turnover is captured
    # at the combo level where rebalancing occurs).
    return simulated


# ---------------------------------------------------------------------------
# Regime / breadth  (same logic as the dividend snapshot strategy)
# ---------------------------------------------------------------------------

def _breadth_regime(close: pd.DataFrame, as_of: pd.Timestamp) -> str:
    """Classify the current market breadth regime.

    Uses the proportion of ETF constituents trading above their 200-day SMA.
    Thresholds mirror the dividend snapshot strategy:
      - risk_on       : breadth >= 0.45
      - soft_defense  : 0.30 <= breadth < 0.45
      - hard_defense  : breadth <  0.30
    """
    window = close.loc[:as_of]
    if len(window) < 100:
        return "risk_on"

    sma200 = window.rolling(200, min_periods=100).mean()
    above_sma = (window.iloc[-1] > sma200.iloc[-1]).sum()
    total = len(close.columns)
    breadth = above_sma / max(total, 1)

    if breadth < 0.30:
        return "hard_defense"
    if breadth < 0.45:
        return "soft_defense"
    return "risk_on"


def _dynamic_leg_weights(combo: "ComboConfig", regime: str) -> tuple[float, float]:
    """Mirror production combo regime semantics for ETF/dividend weights."""
    if regime == "soft_defense":
        etf_target_weight = min(combo.etf_weight * 0.85, 1.0)
    elif regime == "hard_defense":
        etf_target_weight = min(combo.etf_weight * 0.50, 1.0)
    else:
        etf_target_weight = combo.etf_weight
    return etf_target_weight, 1.0 - etf_target_weight


# ---------------------------------------------------------------------------
# Combo backtest runner
# ---------------------------------------------------------------------------

StatDyn = Literal["static", "dynamic"]


@dataclass(frozen=True)
class ComboConfig:
    etf_weight: float = ETF_WEIGHT
    dividend_weight: float = DIVIDEND_WEIGHT
    rebalance_frequency: str = "monthly"
    cost_bps: float = 10.0
    dynamic_dividend_weights: tuple[tuple[str, float], ...] = tuple(
        sorted(DYNAMIC_WEIGHT_MAP.items())
    )


def _combo_strategy_returns(
    close: pd.DataFrame,
    rotation: RotationConfig,
    combo: ComboConfig,
    mode: StatDyn,
) -> tuple[pd.Series, pd.DataFrame, pd.DataFrame]:
    """Compute combined portfolio returns for a given mode (static or dynamic).

    Returns
    -------
    net_returns : pd.Series
        Daily net returns of the combo portfolio (after turnover costs).
    weights_history : pd.DataFrame
        Daily weight matrix for every asset (ETF-rotation names + dividend
        proxy).
    regimes : pd.DataFrame
        Daily regime assignments (one column "regime") for the dynamic path.
    """
    # -- ETF leg weights (unchanged from standalone backtest) -------------
    etf_targets = _target_weights(close, rotation)

    # -- Dividend simulated returns --------------------------------------
    dividend_returns = _simulate_dividend_returns(close, BacktestConfig(), rotation)

    # -- Regime / blended weight schedule --------------------------------
    rebalance_dates = _rebalance_dates(close, rotation.rebalance_frequency)
    rebalance_dates = rebalance_dates[rebalance_dates <= close.index[-1]]

    weight_schedule: list[dict[str, Any]] = []
    regime_history: list[dict[str, str]] = []

    for target_date in rebalance_dates:
        pos = close.index.searchsorted(target_date, side="right") - 1
        if pos < 0:
            continue
        as_of = pd.Timestamp(close.index[pos])

        if mode == "static":
            etf_target_weight = combo.etf_weight
            div_target_weight = combo.dividend_weight
            regime = "static"
        else:
            regime = _breadth_regime(close, as_of)
            etf_target_weight, div_target_weight = _dynamic_leg_weights(combo, regime)

        regime_history.append({"date": as_of, "regime": regime, "div_weight": div_target_weight})

        # Scale the ETF target weights so they sum to `etf_target_weight`
        base_etf_weights = etf_targets.loc[as_of] if as_of in etf_targets.index else pd.Series(0.0, index=close.columns)
        etf_gross = float(base_etf_weights.sum())
        if etf_gross > 0.0:
            scaled_etf = base_etf_weights.multiply(etf_target_weight / etf_gross)
        else:
            scaled_etf = base_etf_weights * 0.0

        row: dict[str, float] = {symbol: float(scaled_etf.get(symbol, 0.0)) for symbol in close.columns}
        if DIVIDEND_SYMBOL not in row:
            row[DIVIDEND_SYMBOL] = 0.0
        row[DIVIDEND_SYMBOL] += div_target_weight
        weight_schedule.append({"date": as_of, **row})

    weights = pd.DataFrame(weight_schedule).set_index("date")
    weights = weights.reindex(close.index, method="ffill").fillna(0.0)
    weights = weights.shift(1).fillna(0.0)

    regimes_df = pd.DataFrame(regime_history).set_index("date") if regime_history else pd.DataFrame()

    # -- Daily returns & turnover cost -----------------------------------
    all_returns = close.pct_change().fillna(0.0)
    # Combine with the dividend proxy (which may not be in close.columns)
    # Use the dividend_returns series as a column
    asset_returns = all_returns.copy()
    if DIVIDEND_SYMBOL in asset_returns.columns:
        asset_returns[DIVIDEND_SYMBOL] = dividend_returns

    portfolio_returns = (weights * asset_returns).sum(axis=1)

    turnover = weights.diff().abs().sum(axis=1).fillna(0.0)
    net_returns = portfolio_returns - turnover * combo.cost_bps / 10_000.0

    return net_returns, weights, regimes_df


def run_combo(
    config: BacktestConfig | None = None,
    rotation: RotationConfig | None = None,
    combo: ComboConfig | None = None,
) -> dict[str, Any]:
    """Run static and dynamic combo backtests and return full results.

    Parameters
    ----------
    config : BacktestConfig
    rotation : RotationConfig
    combo : ComboConfig

    Returns
    -------
    dict with keys: configs, etf_data, regimes, metrics, comparison.
    """
    config = config or BacktestConfig()
    rotation = rotation or RotationConfig()
    combo = combo or ComboConfig()

    # -- Fetch data (shared) ----------------------------------------------
    close = _download_close(config)
    analysis_close = close.loc[pd.Timestamp(config.analysis_start):]

    # -- Static combo -----------------------------------------------------
    static_returns, static_weights, _static_regimes = _combo_strategy_returns(
        analysis_close, rotation, combo, "static",
    )
    # -- Dynamic combo ----------------------------------------------------
    dynamic_returns, dynamic_weights, regimes_df = _combo_strategy_returns(
        analysis_close, rotation, combo, "dynamic",
    )

    # -- Standalone ETF leg for reference ---------------------------------
    etf_raw, etf_targets = _strategy_returns(analysis_close, rotation)
    # Live 03110 for benchmark
    dividend_raw = _simulate_dividend_returns(analysis_close, config, rotation)
    benchmark_returns: dict[str, pd.Series] = {
        "combo_static": static_returns,
        "combo_dynamic": dynamic_returns,
        "etf_rotation_standalone": etf_raw,
        "dividend_proxy_standalone": dividend_raw,
    }
    # Static 60/40 (no rebalancing) buy-and-hold benchmark
    etf_bh = analysis_close.pct_change().fillna(0.0).mean(axis=1)
    benchmark_returns["static_buy_and_hold_6040"] = etf_bh * combo.etf_weight + dividend_raw * combo.dividend_weight

    # -- Period definitions -----------------------------------------------
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

    # -- Bear market & recent sub-periods ---------------------------------
    # Bear market: defined as the period when the static buy-and-hold 60/40
    # drawdown exceeds -10 %.
    bh_equity = (1.0 + benchmark_returns["static_buy_and_hold_6040"]).cumprod()
    bh_drawdown = bh_equity / bh_equity.cummax() - 1.0
    bear_mask = bh_drawdown < -0.10
    bear_indices = analysis_close.index[bear_mask]
    bear_start = bear_indices[0].date().isoformat() if not bear_indices.empty else None
    bear_end = bear_indices[-1].date().isoformat() if not bear_indices.empty else None
    periods["bear_market"] = (bear_start, bear_end) if bear_start else (None, None)

    # Recent: trailing 1 year
    periods["recent"] = ("2025-06-01", config.data_end)

    # -- Compute metrics --------------------------------------------------
    metrics = {
        name: {period: _metrics(_slice(series, start, end)) for period, (start, end) in periods.items()}
        for name, series in benchmark_returns.items()
    }

    # -- Comparison summary (dynamic - static) ----------------------------
    comparison: dict[str, Any] = {}
    for period_key in periods:
        sm = metrics.get("combo_static", {}).get(period_key, {})
        dm = metrics.get("combo_dynamic", {}).get(period_key, {})
        comparison[period_key] = {
            "diff_annual_return": float(dm.get("annual_return", 0.0)) - float(sm.get("annual_return", 0.0)),
            "diff_max_drawdown": float(dm.get("max_drawdown", 0.0)) - float(sm.get("max_drawdown", 0.0)),
            "diff_annual_volatility": float(dm.get("annual_volatility", 0.0)) - float(sm.get("annual_volatility", 0.0)),
        }

    # -- Regime statistics ------------------------------------------------
    if not regimes_df.empty:
        regime_counts = regimes_df["regime"].value_counts().to_dict()
        regime_pct = regimes_df["regime"].value_counts(normalize=True).mul(100).round(1).to_dict()
    else:
        regime_counts = {}
        regime_pct = {}

    # -- ETF last weights -------------------------------------------------
    last_weights_raw = static_weights.tail(1)
    last_weights_dict = last_weights_raw.to_dict("records")[0] if not last_weights_raw.empty else {}

    return {
        "config": asdict(config),
        "rotation_config": asdict(rotation),
        "combo_config": {
            "etf_weight": combo.etf_weight,
            "dividend_weight": combo.dividend_weight,
            "rebalance_frequency": combo.rebalance_frequency,
            "cost_bps": combo.cost_bps,
            "dynamic_dividend_weights": {k: v for k, v in combo.dynamic_dividend_weights},
        },
        "data": {
            "start": analysis_close.index.min().date().isoformat(),
            "end": analysis_close.index.max().date().isoformat(),
            "rows": int(len(analysis_close)),
            "last_weights": {str(k): float(v) for k, v in last_weights_dict.items()},
        },
        "regimes": {
            "counts": {str(k): int(v) for k, v in regime_counts.items()},
            "pct": {str(k): float(v) for k, v in regime_pct.items()},
        },
        "metrics": metrics,
        "comparison": comparison,
        "periods": {k: v for k, v in periods.items()},
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backtest HK equity combo (ETF rotation + dividend snapshot)."
    )
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()

    payload = run_combo()
    text = json.dumps(payload, indent=2, sort_keys=True)

    if args.json_output:
        args.json_output.write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
