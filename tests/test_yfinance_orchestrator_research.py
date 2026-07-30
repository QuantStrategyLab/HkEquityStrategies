from __future__ import annotations

import unittest
import sys
import types
from unittest.mock import patch

import pandas as pd

from hk_equity_strategies.backtest.orchestrator_research import (
    run_combo_profile_backtest,
    run_etf_rotation_profile_backtest,
)
from hk_equity_strategies.strategies.hk_equity_combo import PROFILE_NAME as HK_EQUITY_COMBO_PROFILE
from hk_equity_strategies.backtest.yfinance_market_data import (
    download_close_matrix,
    download_market_history,
)
from hk_equity_strategies.strategies.hk_global_etf_tactical_rotation import (
    DEFAULT_MIN_HISTORY_DAYS,
    DEFAULT_UNIVERSE_SYMBOLS,
    PROFILE_NAME,
)


class YfinanceMarketDataTests(unittest.TestCase):
    def test_download_close_matrix_does_not_forward_fill_missing_quotes(self) -> None:
        index = pd.bdate_range("2026-07-27", periods=3)
        columns = pd.MultiIndex.from_product(
            [["Close"], ["2800.HK", "2822.HK"]]
        )
        raw = pd.DataFrame(
            [
                [20.0, 10.0],
                [20.1, None],
                [20.2, None],
            ],
            index=index,
            columns=columns,
        )
        fake_yfinance = types.SimpleNamespace(download=lambda *_args, **_kwargs: raw)

        with patch.dict(sys.modules, {"yfinance": fake_yfinance}):
            close = download_close_matrix(
                start="2026-07-27",
                end="2026-07-31",
                symbols=("02800", "02822"),
            )

        self.assertEqual(len(close), 1)
        self.assertEqual(close.index[-1], index[0])

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


class ComboOrchestratorResearchTests(unittest.TestCase):
    def test_run_combo_profile_backtest_with_fixture_history(self) -> None:
        rows = []
        for day in pd.bdate_range("2022-01-03", periods=400):
            for symbol in DEFAULT_UNIVERSE_SYMBOLS:
                rows.append({"date": day, "symbol": symbol, "close": 10.0 + hash(symbol) % 5})
        history = pd.DataFrame(rows)
        payload = run_combo_profile_backtest(
            HK_EQUITY_COMBO_PROFILE,
            market_history=history,
            params={"min_history_days": DEFAULT_MIN_HISTORY_DAYS, "combo_mode": "static"},
        )
        self.assertEqual(payload["profile"], HK_EQUITY_COMBO_PROFILE)
        self.assertEqual(payload["source"], "HkEquityComboBacktestRunner")
        self.assertGreater(payload["metrics"]["days"], 0)


if __name__ == "__main__":
    unittest.main()
