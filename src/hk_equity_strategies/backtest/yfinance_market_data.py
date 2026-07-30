"""Yahoo Finance market history helpers for HK ETF research backtests."""

from __future__ import annotations

from typing import Mapping

import pandas as pd

from hk_equity_strategies.strategies.hk_global_etf_tactical_rotation import DEFAULT_UNIVERSE_SYMBOLS

YAHOO_SYMBOLS: Mapping[str, str] = {
    "02800": "2800.HK",
    "02822": "2822.HK",
    "03188": "3188.HK",
    "03033": "3033.HK",
    "02834": "2834.HK",
    "02840": "2840.HK",
    "03175": "3175.HK",
    "03110": "3110.HK",
}

ETF_DESCRIPTIONS: Mapping[str, str] = {
    "02800": "Tracker Fund of Hong Kong / HSI",
    "02822": "CSOP FTSE China A50 ETF",
    "03188": "ChinaAMC CSI 300 ETF",
    "03033": "CSOP Hang Seng TECH Index ETF",
    "02834": "iShares NASDAQ 100 ETF",
    "02840": "SPDR Gold Shares",
    "03175": "Samsung S&P GSCI Crude Oil ER Futures ETF",
    "03110": "Global X Hang Seng High Dividend Yield ETF",
}


def download_close_matrix(
    *,
    start: str,
    end: str,
    symbols: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    """Download adjusted close prices (wide matrix, HK symbol columns)."""
    try:
        import yfinance as yf
    except ImportError as exc:  # pragma: no cover - research helper only
        raise RuntimeError(
            "yfinance is required for live HK ETF backtests; pip install yfinance"
        ) from exc

    universe = tuple(symbols or DEFAULT_UNIVERSE_SYMBOLS)
    tickers = [YAHOO_SYMBOLS[symbol] for symbol in universe]
    raw = yf.download(
        tickers,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        threads=False,
    )
    close = raw["Close"]
    if isinstance(close, pd.Series):
        close = close.to_frame()
    close = close.rename(columns={yahoo: symbol for symbol, yahoo in YAHOO_SYMBOLS.items()})
    ordered = [symbol for symbol in universe if symbol in close.columns]
    # Keep only dates with real observations for the whole configured universe.
    # Forward-filling here would hide a ticker that stopped publishing quotes.
    close = close.loc[:, ordered].dropna(how="any")
    return close


def download_market_history(
    *,
    start: str,
    end: str,
    symbols: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    """Return long-format market history for orchestrator runners."""
    close = download_close_matrix(start=start, end=end, symbols=symbols)
    rows: list[dict[str, object]] = []
    for day, values in close.iterrows():
        day_norm = pd.Timestamp(day).tz_localize(None).normalize()
        for symbol, price in values.items():
            rows.append({"date": day_norm, "symbol": str(symbol), "close": float(price)})
    return pd.DataFrame(rows).sort_values(["date", "symbol"]).reset_index(drop=True)


__all__ = [
    "ETF_DESCRIPTIONS",
    "YAHOO_SYMBOLS",
    "download_close_matrix",
    "download_market_history",
]
