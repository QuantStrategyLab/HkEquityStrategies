from __future__ import annotations

import unittest
from unittest.mock import patch

import pandas as pd

from hk_equity_strategies.backtest.orchestrator_research import run_etf_rotation_profile_backtest
from hk_equity_strategies.backtest.yfinance_market_data import download_market_history
from hk_equity_strategies.strategies.hk_global_etf_tactical_rotation import (
    DEFAULT_MIN_HISTORY_DAYS,
    DEFAULT_UNIVERSE_SYMBOLS,
    PROFILE_NAME,
)


class YfinanceMarketDataTests(unittest.TestCase):
    def test_download_market_history_returns_long_format(self) -> None:
        index = pd.bdate_range("2023-01-03", periods=300)
        wide = pd.DataFrame(
            {symbol: float(idx) for idx, symbol in enumerate(("02800", "02822"))},
            index=index,
        )
        with patch(
            "hk_equity_strategies.backtest.yfinance_market_data.download_close_matrix",
            return_value=wide,
        ):
            history = download_market_history(start="2023-01-01", end="2024-01-01", symbols=("02800", "02822"))
        self.assertEqual({"date", "symbol", "close"}, set(history.columns))
        self.assertGreater(len(history), 0)
        self.assertTrue(history["symbol"].isin(["02800", "02822"]).all())


class OrchestratorResearchTests(unittest.TestCase):
    def test_run_etf_rotation_profile_backtest_with_fixture_history(self) -> None:
        rows = []
        for day in pd.bdate_range("2022-01-03", periods=400):
            for symbol in DEFAULT_UNIVERSE_SYMBOLS:
                rows.append({"date": day, "symbol": symbol, "close": 10.0 + hash(symbol) % 5})
        history = pd.DataFrame(rows)
        payload = run_etf_rotation_profile_backtest(
            PROFILE_NAME,
            market_history=history,
            params={"min_history_days": DEFAULT_MIN_HISTORY_DAYS},
        )
        self.assertEqual(payload["profile"], PROFILE_NAME)
        self.assertEqual(payload["source"], "HkEtfRotationBacktestRunner")
        self.assertGreater(payload["metrics"]["days"], 0)


if __name__ == "__main__":
    unittest.main()
