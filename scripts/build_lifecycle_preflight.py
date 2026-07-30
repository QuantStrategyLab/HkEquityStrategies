#!/usr/bin/env python3
"""Build HK lifecycle baselines and return matrices from real market history."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from hk_equity_strategies.backtest.combo_simulator import (
    HkComboBacktestConfig,
    run_combo_backtest,
)
from hk_equity_strategies.backtest.etf_rotation_simulator import (
    HkRotationBacktestConfig,
    run_etf_rotation_backtest,
)
from hk_equity_strategies.backtest.orchestrator_runner import SUPPORTED_PROFILES
from hk_equity_strategies.backtest.yfinance_market_data import download_market_history
from hk_equity_strategies.strategies.hk_equity_combo import (
    PROFILE_NAME as HK_EQUITY_COMBO_PROFILE,
)
from hk_equity_strategies.strategies.hk_global_etf_tactical_rotation import (
    DEFAULT_MIN_HISTORY_DAYS,
    DEFAULT_UNIVERSE_SYMBOLS,
    PROFILE_NAME as HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE,
    build_target_weights,
)
try:
    from .run_walk_forward_backtest import PROFILE_DEFAULTS, run_walk_forward
except ImportError:  # Direct execution: python scripts/build_lifecycle_preflight.py
    from run_walk_forward_backtest import PROFILE_DEFAULTS, run_walk_forward


DOMAIN = "hk_equity"
SNAPSHOT_REPOSITORY = "HkEquitySnapshotPipelines"
BENCHMARK_SYMBOL = "02800"
BENCHMARK_COLUMN = "buy_hold_2800"
MAX_INPUT_AGE_DAYS = 10


def _normalized_market_history(market_history: pd.DataFrame) -> pd.DataFrame:
    required = {"date", "symbol", "close"}
    if not isinstance(market_history, pd.DataFrame) or market_history.empty:
        raise ValueError("market history must be a non-empty DataFrame")
    missing_columns = required - set(market_history.columns)
    if missing_columns:
        raise ValueError(
            f"market history is missing columns: {', '.join(sorted(missing_columns))}"
        )
    frame = market_history.loc[:, ["date", "symbol", "close"]].copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce").dt.tz_localize(
        None
    ).dt.normalize()
    frame["symbol"] = frame["symbol"].astype(str).str.strip().str.removesuffix(".HK")
    frame["symbol"] = frame["symbol"].map(
        lambda value: value.zfill(5) if value.isdigit() else value
    )
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    if frame[["date", "symbol", "close"]].isna().any().any():
        raise ValueError("market history contains invalid date, symbol, or close values")
    if (frame["close"] <= 0.0).any() or not frame["close"].map(math.isfinite).all():
        raise ValueError("market history close values must be positive and finite")
    if frame.duplicated(["date", "symbol"]).any():
        raise ValueError("market history contains duplicate date/symbol rows")
    return frame.sort_values(["date", "symbol"]).reset_index(drop=True)


def validate_market_history(
    market_history: pd.DataFrame,
    *,
    reference_date: date | None = None,
) -> pd.DataFrame:
    """Validate the complete configured universe and optional freshness boundary."""

    frame = _normalized_market_history(market_history)
    required_symbols = set(DEFAULT_UNIVERSE_SYMBOLS)
    available_symbols = set(frame["symbol"])
    missing_symbols = sorted(required_symbols - available_symbols)
    if missing_symbols:
        raise ValueError(
            f"market history is missing required symbols: {', '.join(missing_symbols)}"
        )
    overlap = (
        frame.loc[frame["symbol"].isin(required_symbols)]
        .pivot(index="date", columns="symbol", values="close")
        .loc[:, list(DEFAULT_UNIVERSE_SYMBOLS)]
        .ffill()
        .dropna(how="any")
    )
    if len(overlap) < DEFAULT_MIN_HISTORY_DAYS:
        raise ValueError(
            f"market history requires at least {DEFAULT_MIN_HISTORY_DAYS} "
            "overlapping trading days"
        )
    if reference_date is not None:
        latest = pd.Timestamp(overlap.index.max()).date()
        age = reference_date - latest
        if age < timedelta(0):
            raise ValueError("market history contains a future trading date")
        if age > timedelta(days=MAX_INPUT_AGE_DAYS):
            raise ValueError(
                f"market history is stale: latest={latest.isoformat()} age_days={age.days}"
            )
    return frame


def _signal_fn(history: Any, **kwargs: Any):
    return build_target_weights(history, **kwargs)


def build_profile_return_matrix(
    profile: str,
    market_history: pd.DataFrame,
) -> pd.DataFrame:
    if profile not in SUPPORTED_PROFILES:
        raise ValueError(f"unsupported profile={profile!r}")
    frame = validate_market_history(market_history)
    params = dict(
        PROFILE_DEFAULTS.get(
            profile,
            {"min_history_days": DEFAULT_MIN_HISTORY_DAYS},
        )
    )
    min_history_days = int(params.get("min_history_days", DEFAULT_MIN_HISTORY_DAYS))
    rotation_config = HkRotationBacktestConfig(min_history_days=min_history_days)
    if profile == HK_EQUITY_COMBO_PROFILE:
        result = run_combo_backtest(
            frame,
            _signal_fn,
            combo_config=HkComboBacktestConfig(
                combo_mode=str(params.get("combo_mode", "dynamic")),
                min_history_days=min_history_days,
            ),
            rotation_config=rotation_config,
            strategy_kwargs={"min_history_days": min_history_days},
        )
    elif profile == HK_GLOBAL_ETF_TACTICAL_ROTATION_PROFILE:
        result = run_etf_rotation_backtest(
            frame,
            _signal_fn,
            config=rotation_config,
            strategy_kwargs={"min_history_days": min_history_days},
        )
    else:  # Defensive boundary if SUPPORTED_PROFILES gains a new runner type.
        raise ValueError(f"no lifecycle return builder registered for profile={profile!r}")

    benchmark = (
        frame.loc[frame["symbol"] == BENCHMARK_SYMBOL]
        .set_index("date")["close"]
        .sort_index()
        .pct_change(fill_method=None)
        .fillna(0.0)
        .rename(BENCHMARK_COLUMN)
    )
    strategy = result.daily_returns.rename(profile)
    matrix = pd.concat([strategy, benchmark], axis=1, join="inner").sort_index()
    matrix = matrix.replace([float("inf"), float("-inf")], pd.NA).dropna()
    if len(matrix) < DEFAULT_MIN_HISTORY_DAYS:
        raise ValueError(
            f"return matrix for profile={profile!r} has insufficient observations"
        )
    matrix.index = pd.DatetimeIndex(matrix.index).tz_localize(None).normalize()
    matrix.index.name = "as_of"
    return matrix.reset_index()


def build_lifecycle_preflight_bundle(
    market_history: pd.DataFrame,
    *,
    bundle_root: Path,
) -> dict[str, Any]:
    frame = validate_market_history(market_history)
    profiles = sorted(SUPPORTED_PROFILES)
    store_root = bundle_root / "data" / "lifecycle_store"
    matrix_rows: dict[str, int] = {}
    for profile in profiles:
        run_walk_forward(
            profile=profile,
            store_root=store_root,
            market_history=frame.copy(deep=True),
        )
        backtest_dir = store_root / "backtest" / DOMAIN / profile
        if len(list(backtest_dir.glob("backtest_*.json"))) != 1:
            raise RuntimeError(
                f"expected one persisted lifecycle baseline for profile={profile!r}"
            )
        matrix = build_profile_return_matrix(profile, frame.copy(deep=True))
        output_path = (
            bundle_root
            / "external"
            / SNAPSHOT_REPOSITORY
            / "data"
            / "output"
            / profile
            / "portfolio_and_tracker_returns.csv"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        matrix.to_csv(output_path, index=False, date_format="%Y-%m-%d")
        matrix_rows[profile] = len(matrix)
    return {"profiles": profiles, "matrix_rows": matrix_rows}


def write_market_input_artifact(
    market_history: pd.DataFrame,
    *,
    output_dir: Path,
    source: str,
    requested_start: str,
    requested_end: str,
    retrieved_at: str,
    yfinance_version: str | None = None,
) -> dict[str, Any]:
    frame = validate_market_history(market_history)
    serializable = frame.copy()
    serializable["date"] = serializable["date"].dt.strftime("%Y-%m-%d")
    output_dir.mkdir(parents=True, exist_ok=True)
    data_path = output_dir / "market_history.csv.gz"
    serializable.to_csv(
        data_path,
        index=False,
        compression={"method": "gzip", "compresslevel": 9, "mtime": 0},
    )
    manifest = {
        "schema_version": "hk_lifecycle_market_input.v1",
        "source": source,
        "requested_start": requested_start,
        "requested_end": requested_end,
        "retrieved_at": retrieved_at,
        "row_count": len(serializable),
        "trading_day_count": int(serializable["date"].nunique()),
        "symbols": sorted(serializable["symbol"].unique().tolist()),
        "first_date": str(serializable["date"].min()),
        "last_date": str(serializable["date"].max()),
        "profiles": sorted(SUPPORTED_PROFILES),
        "sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(),
    }
    if yfinance_version:
        manifest["yfinance_version"] = yfinance_version
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle-root", type=Path, required=True)
    parser.add_argument("--input-artifact-root", type=Path, required=True)
    parser.add_argument("--start", default="2020-08-27")
    parser.add_argument("--end", required=True)
    parser.add_argument("--market-history", type=Path)
    args = parser.parse_args(argv)

    retrieved_at = datetime.now(timezone.utc).isoformat()
    if args.market_history:
        market_history = pd.read_csv(args.market_history)
        source = "provided_file"
        yfinance_version = None
    else:
        market_history = download_market_history(start=args.start, end=args.end)
        source = "yfinance"
        yfinance_version = importlib.metadata.version("yfinance")
    validated = validate_market_history(
        market_history,
        reference_date=datetime.now(timezone.utc).date(),
    )
    manifest = write_market_input_artifact(
        validated,
        output_dir=args.input_artifact_root,
        source=source,
        requested_start=args.start,
        requested_end=args.end,
        retrieved_at=retrieved_at,
        yfinance_version=yfinance_version,
    )
    bundle = build_lifecycle_preflight_bundle(
        validated,
        bundle_root=args.bundle_root,
    )
    print(
        json.dumps(
            {
                "source": source,
                "last_date": manifest["last_date"],
                "row_count": manifest["row_count"],
                **bundle,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
