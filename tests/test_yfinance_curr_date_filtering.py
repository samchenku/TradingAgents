import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from tradingagents.dataflows import stockstats_utils, y_finance
from tradingagents.dataflows.config import get_config, set_config
from tradingagents.dataflows.stockstats_utils import StockstatsUtils


class YFinanceCurrDateFilteringTests(unittest.TestCase):
    def test_stockstats_filters_future_rows_before_indicator_calculation(self):
        original_config = get_config()
        with tempfile.TemporaryDirectory() as tmpdir:
            updated_config = original_config.copy()
            updated_config["data_cache_dir"] = tmpdir
            updated_config["data_vendors"] = dict(original_config["data_vendors"])
            updated_config["data_vendors"]["technical_indicators"] = "yfinance"
            set_config(updated_config)

            downloaded = pd.DataFrame(
                {
                    "Open": [100.0, 110.0],
                    "High": [101.0, 111.0],
                    "Low": [99.0, 109.0],
                    "Close": [100.5, 110.5],
                    "Volume": [1000, 1200],
                },
                index=pd.to_datetime(["2024-01-03", "2024-01-04"]),
            )
            downloaded.index.name = "Date"

            def fake_wrap(df):
                self.assertTrue(
                    (pd.to_datetime(df["Date"]) <= pd.Timestamp("2024-01-03")).all()
                )
                wrapped = df.copy()
                wrapped["rsi"] = 45.0
                return wrapped

            try:
                with patch.object(
                    stockstats_utils.yf, "download", return_value=downloaded
                ), patch.object(stockstats_utils, "wrap", side_effect=fake_wrap):
                    value = StockstatsUtils.get_stock_stats("AAPL", "rsi", "2024-01-03")
            finally:
                set_config(original_config)

        self.assertEqual(value, 45.0)

    def test_balance_sheet_filters_future_reporting_columns(self):
        quarterly_balance_sheet = pd.DataFrame(
            {
                pd.Timestamp("2024-03-31"): [100],
                pd.Timestamp("2024-06-30"): [200],
            },
            index=["Total Assets"],
        )

        class FakeTicker:
            def __init__(self, balance_sheet):
                self.balance_sheet = balance_sheet
                self.quarterly_balance_sheet = balance_sheet

        with patch.object(
            y_finance.yf,
            "Ticker",
            return_value=FakeTicker(quarterly_balance_sheet),
        ):
            output = y_finance.get_balance_sheet(
                "AAPL",
                freq="quarterly",
                curr_date="2024-03-31",
            )

        self.assertIn("2024-03-31", output)
        self.assertNotIn("2024-06-30", output)


if __name__ == "__main__":
    unittest.main()
