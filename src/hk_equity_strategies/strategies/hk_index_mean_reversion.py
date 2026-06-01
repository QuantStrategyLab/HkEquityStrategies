from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

import pandas as pd

HK_EQUITY_DOMAIN = "hk_equity"
SIGNAL_SOURCE = "daily_market_history"
STATUS_ICON = "🇭🇰"
PROFILE_NAME = "hk_index_mean_reversion"
HSI_ETF_SYMBOL = "02800"
HSTECH_ETF_SYMBOL = "03033"
DEFAULT_ANCHOR_SYMBOL = HSI_ETF_SYMBOL
DEFAULT_SATELLITE_SYMBOL = HSTECH_ETF_SYMBOL
DEFAULT_LOOKBACK_DAYS = 80
DEFAULT_ENTRY_Z = 1.0
DEFAULT_EXIT_Z = 0.25
DEFAULT_NEUTRAL_SATELLITE_WEIGHT = 0.50
DEFAULT_OVERSOLD_SATELLITE_WEIGHT = 0.65
DEFAULT_RICH_SATELLITE_WEIGHT = 0.05
DEFAULT_TREND_WINDOW_DAYS = 200
DEFAULT_DEFENSIVE_GROSS_EXPOSURE = 0.35
DEFAULT_DEFENSIVE_SATELLITE_WEIGHT = 0.0
DEFAULT_MIN_HISTORY_DAYS = 260
DEFAULT_REBALANCE_FREQUENCY = "weekly"
DEFAULT_EXECUTION_CASH_RESERVE_RATIO = 0.02

REQUIRED_MARKET_HISTORY_COLUMNS = frozenset({"date", "symbol", "close"})
OPTIONAL_MARKET_HISTORY_COLUMNS = frozenset({"open", "high", "low", "volume"})


def normalize_symbol(value: Any) -> str:
    text = str(value or "").strip().upper()
    if not text:
        return ""
    text = text.removesuffix(".HK")
    if text.isdigit():
        return text.zfill(5)
    return text


def _history_to_frame(market_history: Any) -> pd.DataFrame:
    if isinstance(market_history, pd.DataFrame):
        frame = market_history.copy()
    elif isinstance(market_history, Mapping):
        frame = _mapping_history_to_frame(market_history)
    else:
        frame = pd.DataFrame(list(market_history))
    if frame.empty:
        raise ValueError("market_history must contain at least one row")

    # Accept a wide close matrix indexed by date with symbols as columns.
    if "date" not in frame.columns and "symbol" not in frame.columns and "close" not in frame.columns:
        frame = frame.reset_index(names="date").melt(id_vars="date", var_name="symbol", value_name="close")

    missing = REQUIRED_MARKET_HISTORY_COLUMNS - set(frame.columns)
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ValueError(f"market_history missing required columns: {missing_text}")

    output_columns = ["date", "symbol", "close", *sorted(OPTIONAL_MARKET_HISTORY_COLUMNS)]
    frame = frame.loc[:, [column for column in output_columns if column in frame.columns]].copy()
    frame["date"] = pd.to_datetime(frame["date"], utc=False).dt.tz_localize(None).dt.normalize()
    frame["symbol"] = frame["symbol"].map(normalize_symbol)
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    frame = frame.dropna(subset=["date", "symbol", "close"])
    frame = frame.loc[frame["symbol"] != ""]
    if frame.empty:
        raise ValueError("market_history has no valid date/symbol/close rows")
    return frame.sort_values(["date", "symbol"]).reset_index(drop=True)


def _mapping_history_to_frame(market_history: Mapping[Any, Any]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for raw_symbol, raw_history in market_history.items():
        symbol = normalize_symbol(raw_symbol)
        if isinstance(raw_history, pd.DataFrame):
            item_frame = raw_history.copy()
            if "date" not in item_frame.columns:
                item_frame = item_frame.reset_index(names="date")
            close_column = (
                "close"
                if "close" in item_frame.columns
                else "Close" if "Close" in item_frame.columns else None
            )
            if close_column is None:
                raise ValueError(f"market_history[{raw_symbol!r}] missing close column")
            for row in item_frame.itertuples(index=False):
                rows.append(
                    {"date": getattr(row, "date"), "symbol": symbol, "close": getattr(row, close_column)}
                )
            continue
        for item in raw_history:
            if isinstance(item, Mapping):
                date_value = item.get("date") or item.get("as_of") or item.get("timestamp")
                close_value = item.get("close") or item.get("Close")
            else:
                date_value = (
                    getattr(item, "date", None)
                    or getattr(item, "as_of", None)
                    or getattr(item, "timestamp", None)
                )
                close_value = getattr(item, "close", None) or getattr(item, "Close", None)
            rows.append({"date": date_value, "symbol": symbol, "close": close_value})
    return pd.DataFrame(rows)


def build_close_matrix(
    market_history: Any,
    *,
    anchor_symbol: str = DEFAULT_ANCHOR_SYMBOL,
    satellite_symbol: str = DEFAULT_SATELLITE_SYMBOL,
) -> pd.DataFrame:
    frame = _history_to_frame(market_history)
    anchor_symbol = normalize_symbol(anchor_symbol)
    satellite_symbol = normalize_symbol(satellite_symbol)
    close = (
        frame.loc[frame["symbol"].isin({anchor_symbol, satellite_symbol})]
        .pivot_table(index="date", columns="symbol", values="close", aggfunc="last")
        .sort_index()
    )
    close = close.rename(columns={anchor_symbol: "anchor", satellite_symbol: "satellite"})
    missing = {"anchor", "satellite"} - set(close.columns)
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ValueError(f"market_history missing required strategy symbols: {missing_text}")
    close = close.loc[:, ["anchor", "satellite"]].dropna(how="any")
    close = close.loc[(close["anchor"] > 0) & (close["satellite"] > 0)]
    if close.empty:
        raise ValueError("market_history has no overlapping close history for anchor/satellite symbols")
    return close


def compute_latest_signal(
    market_history: Any,
    *,
    anchor_symbol: str = DEFAULT_ANCHOR_SYMBOL,
    satellite_symbol: str = DEFAULT_SATELLITE_SYMBOL,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    entry_z: float = DEFAULT_ENTRY_Z,
    exit_z: float = DEFAULT_EXIT_Z,
    neutral_satellite_weight: float = DEFAULT_NEUTRAL_SATELLITE_WEIGHT,
    oversold_satellite_weight: float = DEFAULT_OVERSOLD_SATELLITE_WEIGHT,
    rich_satellite_weight: float = DEFAULT_RICH_SATELLITE_WEIGHT,
    trend_window_days: int = DEFAULT_TREND_WINDOW_DAYS,
    defensive_gross_exposure: float = DEFAULT_DEFENSIVE_GROSS_EXPOSURE,
    defensive_satellite_weight: float = DEFAULT_DEFENSIVE_SATELLITE_WEIGHT,
    min_history_days: int = DEFAULT_MIN_HISTORY_DAYS,
) -> dict[str, object]:
    if lookback_days <= 1:
        raise ValueError("lookback_days must be greater than 1")
    if trend_window_days <= 1:
        raise ValueError("trend_window_days must be greater than 1")
    if min_history_days <= max(lookback_days, trend_window_days):
        raise ValueError("min_history_days must be greater than lookback_days and trend_window_days")

    close = build_close_matrix(
        market_history,
        anchor_symbol=anchor_symbol,
        satellite_symbol=satellite_symbol,
    )
    if len(close) < int(min_history_days):
        raise ValueError(f"market_history requires at least {int(min_history_days)} overlapping trading days")

    ratio = (close["satellite"] / close["anchor"]).map(math.log)
    ratio_mean = ratio.rolling(int(lookback_days)).mean()
    ratio_std = ratio.rolling(int(lookback_days)).std(ddof=0)
    latest_z = float(((ratio - ratio_mean) / ratio_std).iloc[-1])
    if pd.isna(latest_z) or not math.isfinite(latest_z):
        latest_z = 0.0

    latest_anchor = float(close["anchor"].iloc[-1])
    latest_satellite = float(close["satellite"].iloc[-1])
    anchor_ma = float(close["anchor"].rolling(int(trend_window_days)).mean().iloc[-1])
    satellite_ma = float(close["satellite"].rolling(int(trend_window_days)).mean().iloc[-1])
    anchor_trend_positive = latest_anchor >= anchor_ma
    satellite_trend_positive = latest_satellite >= satellite_ma
    broad_risk_off = not anchor_trend_positive

    satellite_weight = float(neutral_satellite_weight)
    signal_state = "neutral"
    if latest_z <= -float(entry_z):
        satellite_weight = float(oversold_satellite_weight)
        signal_state = "satellite_oversold"
    elif latest_z >= float(entry_z):
        satellite_weight = float(rich_satellite_weight)
        signal_state = "satellite_rich"
    elif abs(latest_z) <= float(exit_z):
        satellite_weight = float(neutral_satellite_weight)
        signal_state = "spread_normalized"

    gross_exposure = 1.0
    if broad_risk_off:
        gross_exposure = float(defensive_gross_exposure)
        satellite_weight = min(satellite_weight, float(defensive_satellite_weight))
        signal_state = f"defensive_{signal_state}"

    satellite_weight = min(max(satellite_weight, 0.0), 1.0)
    gross_exposure = min(max(gross_exposure, 0.0), 1.0)
    anchor_weight = max(0.0, gross_exposure * (1.0 - satellite_weight))
    realized_satellite_weight = max(0.0, gross_exposure * satellite_weight)
    cash_weight = max(0.0, 1.0 - anchor_weight - realized_satellite_weight)
    as_of = pd.Timestamp(close.index[-1]).date().isoformat()
    return {
        "as_of": as_of,
        "anchor_symbol": normalize_symbol(anchor_symbol),
        "satellite_symbol": normalize_symbol(satellite_symbol),
        "anchor_close": latest_anchor,
        "satellite_close": latest_satellite,
        "spread_z": latest_z,
        "signal_state": signal_state,
        "anchor_trend_positive": anchor_trend_positive,
        "satellite_trend_positive": satellite_trend_positive,
        "broad_risk_off": broad_risk_off,
        "gross_exposure": gross_exposure,
        "anchor_weight": anchor_weight,
        "satellite_weight": realized_satellite_weight,
        "cash_weight": cash_weight,
        "history_days": int(len(close)),
        "lookback_days": int(lookback_days),
        "trend_window_days": int(trend_window_days),
    }


def build_target_weights(market_history: Any, **kwargs: Any) -> tuple[dict[str, float], dict[str, object]]:
    signal = compute_latest_signal(market_history, **kwargs)
    weights: dict[str, float] = {}
    if signal["anchor_weight"] > 1e-12:
        weights[str(signal["anchor_symbol"])] = float(signal["anchor_weight"])
    if signal["satellite_weight"] > 1e-12:
        weights[str(signal["satellite_symbol"])] = float(signal["satellite_weight"])
    return weights, signal


def extract_managed_symbols(*_args: Any, **kwargs: Any) -> tuple[str, ...]:
    return (
        normalize_symbol(kwargs.get("anchor_symbol", DEFAULT_ANCHOR_SYMBOL)),
        normalize_symbol(kwargs.get("satellite_symbol", DEFAULT_SATELLITE_SYMBOL)),
    )


def compute_signals(market_history: Any, _current_holdings: Any = None, **kwargs: Any):
    kwargs.pop("translator", None)
    kwargs.pop("signal_text_fn", None)
    kwargs.pop("execution_cash_reserve_ratio", None)
    kwargs.pop("rebalance_frequency", None)
    weights, metadata = build_target_weights(market_history, **kwargs)
    signal_desc = (
        f"hk index mean reversion state={metadata['signal_state']} z={metadata['spread_z']:.2f} "
        f"gross={metadata['gross_exposure']:.0%} anchor={metadata['anchor_weight']:.0%} "
        f"satellite={metadata['satellite_weight']:.0%} cash={metadata['cash_weight']:.0%}"
    )
    status_desc = (
        f"state={metadata['signal_state']} | z={metadata['spread_z']:.2f} | "
        f"anchor_trend={'up' if metadata['anchor_trend_positive'] else 'down'} | "
        f"satellite_trend={'up' if metadata['satellite_trend_positive'] else 'down'}"
    )
    return (
        weights,
        signal_desc,
        bool(metadata["broad_risk_off"]),
        status_desc,
        {
            **metadata,
            "managed_symbols": extract_managed_symbols(**kwargs),
            "status_icon": STATUS_ICON,
            "signal_source": SIGNAL_SOURCE,
            "actionable": True,
        },
    )
