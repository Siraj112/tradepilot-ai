import json
import math
import unittest
from unittest.mock import MagicMock, patch

import main


class HyperliquidTests(unittest.TestCase):

    def mock_response(self, payload):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
        return response

    def test_valid_btc_eth_prices(self):
        payload = {"BTC": "90000", "ETH": "3000"}
        with patch("main.urlopen", return_value=self.mock_response(payload)):
            result = main.crypto_prices()

        self.assertTrue(result["data_connected"])
        self.assertEqual(len(result["markets"]), 2)

    def test_missing_symbol(self):
        payload = {"BTC": "90000"}
        with patch("main.urlopen", return_value=self.mock_response(payload)):
            result = main.crypto_prices()

        self.assertFalse(result["data_connected"])

    def test_reject_infinite_price(self):
        payload = {"BTC": "inf", "ETH": "3000"}
        with patch("main.urlopen", return_value=self.mock_response(payload)):
            result = main.crypto_prices()

        self.assertFalse(result["data_connected"])
        self.assertTrue(
            all(math.isfinite(item["price_usd"]) for item in result["markets"])
        )

    def test_provider_timeout(self):
        with patch("main.urlopen", side_effect=TimeoutError("timeout")):
            with self.assertRaises(main.HTTPException) as error:
                main.crypto_prices()

        self.assertEqual(error.exception.status_code, 502)

    def test_invalid_json(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b"invalid json"

        with patch("main.urlopen", return_value=response):
            with self.assertRaises(main.HTTPException) as error:
                main.crypto_prices()

        self.assertEqual(error.exception.status_code, 502)



class BinanceTests(unittest.TestCase):

    def mock_response(self, payload):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
        return response

    def test_both_symbols_available(self):
        btc = {"bidPrice": "90000", "askPrice": "90010"}
        eth = {"bidPrice": "3000", "askPrice": "3001"}

        with patch(
            "main.urlopen",
            side_effect=[
                self.mock_response(btc),
                self.mock_response(eth),
            ],
        ):
            result = main.binance_prices()

        self.assertTrue(result["data_connected"])
        self.assertEqual(len(result["markets"]), 2)
        self.assertTrue(all(item["status"] == "available" for item in result["markets"]))

    def test_partial_availability(self):
        btc = {"bidPrice": "90000", "askPrice": "90010"}

        with patch(
            "main.urlopen",
            side_effect=[
                self.mock_response(btc),
                TimeoutError("ETH timeout"),
            ],
        ):
            result = main.binance_prices()

        self.assertFalse(result["data_connected"])
        self.assertEqual(result["markets"][0]["status"], "available")
        self.assertEqual(result["markets"][1]["status"], "unavailable")

    def test_invalid_quote_unavailable(self):
        invalid = {"bidPrice": "0", "askPrice": "3001"}

        with patch(
            "main.urlopen",
            side_effect=[
                self.mock_response(invalid),
                TimeoutError("ETH timeout"),
            ],
        ):
            result = main.binance_prices()

        self.assertEqual(result["markets"][0]["status"], "unavailable")

    def test_reject_infinite_quote(self):
        invalid = {"bidPrice": "inf", "askPrice": "90010"}

        with patch(
            "main.urlopen",
            side_effect=[
                self.mock_response(invalid),
                TimeoutError("ETH timeout"),
            ],
        ):
            result = main.binance_prices()

        self.assertEqual(result["markets"][0]["status"], "unavailable")


class ForexGoldTests(unittest.TestCase):

    def mock_response(self, payload):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
        return response

    def valid_quote(self):
        return {
            "mid": "1.1000",
            "bid": "1.0999",
            "ask": "1.1001",
            "quoteAgeSeconds": 5,
            "stale": False,
            "marketState": "open",
            "timestamp": "2026-11-17T15:29:19Z",
            "lastQuoteAt": "2026-11-17T15:29:19Z",
        }

    def test_all_markets_fresh(self):
        payload = {
            symbol: self.valid_quote()
            for symbol in ["EURUSD", "GBPUSD", "XAUUSD"]
        }

        with patch("main.urlopen", return_value=self.mock_response(payload)):
            result = main.forex_gold_prices()

        self.assertTrue(result["data_connected"])
        self.assertEqual(len(result["markets"]), 3)
        self.assertTrue(all(item["status"] == "available" for item in result["markets"]))

    def test_provider_timestamps_are_preserved(self):
        payload = {
            symbol: self.valid_quote()
            for symbol in ["EURUSD", "GBPUSD", "XAUUSD"]
        }

        with patch("main.urlopen", return_value=self.mock_response(payload)):
            result = main.forex_gold_prices()

        for market in result["markets"]:
            self.assertEqual(market["timestamp"], "2026-11-17T15:29:19Z")

    def test_missing_provider_timestamp_does_not_reject_quote(self):
        payload = {
            symbol: self.valid_quote()
            for symbol in ["EURUSD", "GBPUSD", "XAUUSD"]
        }
        for quote in payload.values():
            quote.pop("timestamp")

        with patch("main.urlopen", return_value=self.mock_response(payload)):
            result = main.forex_gold_prices()

        self.assertTrue(all(item["status"] == "available" for item in result["markets"]))
        self.assertTrue(all(item["timestamp"] is None for item in result["markets"]))

    def test_invalid_provider_timestamp_does_not_change_quote_freshness(self):
        payload = {
            symbol: self.valid_quote()
            for symbol in ["EURUSD", "GBPUSD", "XAUUSD"]
        }
        for quote in payload.values():
            quote["timestamp"] = "not-a-valid-timestamp"

        with patch("main.urlopen", return_value=self.mock_response(payload)):
            result = main.forex_gold_prices()

        self.assertTrue(all(item["status"] == "available" for item in result["markets"]))
        self.assertTrue(all(item["timestamp"] == "not-a-valid-timestamp" for item in result["markets"]))

    def test_market_closed_status(self):
        quote = self.valid_quote()
        quote["marketState"] = "closed"
        payload = {
            symbol: quote
            for symbol in ["EURUSD", "GBPUSD", "XAUUSD"]
        }

        with patch("main.urlopen", return_value=self.mock_response(payload)):
            result = main.forex_gold_prices()

        self.assertTrue(all(item["status"] == "market_closed" for item in result["markets"]))
        self.assertTrue(result["data_connected"])

    def test_stale_quote_status(self):
        quote = self.valid_quote()
        quote["stale"] = True
        payload = {
            symbol: quote
            for symbol in ["EURUSD", "GBPUSD", "XAUUSD"]
        }

        with patch("main.urlopen", return_value=self.mock_response(payload)):
            result = main.forex_gold_prices()

        self.assertTrue(all(item["status"] == "stale" for item in result["markets"]))
        self.assertTrue(result["data_connected"])

    def test_malformed_spread_marks_only_affected_quote_invalid(self):
        payload = {
            symbol: self.valid_quote()
            for symbol in ["EURUSD", "GBPUSD", "XAUUSD"]
        }
        payload["EURUSD"]["spread"] = "abc"

        with patch("main.urlopen", return_value=self.mock_response(payload)):
            result = main.forex_gold_prices()

        self.assertTrue(result["data_connected"])
        self.assertEqual(result["markets"][0]["status"], "invalid_data")
        self.assertTrue(
            all(item["status"] == "available" for item in result["markets"][1:])
        )

    def test_quote_age_59_60_61_second_boundaries(self):
        for age, expected in [
            (59, "available"),
            (60, "available"),
            (61, "stale"),
        ]:
            with self.subTest(age=age):
                payload = {
                    symbol: self.valid_quote()
                    for symbol in ["EURUSD", "GBPUSD", "XAUUSD"]
                }
                for quote in payload.values():
                    quote["quoteAgeSeconds"] = age

                with patch("main.urlopen", return_value=self.mock_response(payload)):
                    result = main.forex_gold_prices()

                self.assertTrue(
                    all(item["status"] == expected for item in result["markets"])
                )

    def test_negative_quote_age_invalid(self):
        payload = {
            symbol: self.valid_quote()
            for symbol in ["EURUSD", "GBPUSD", "XAUUSD"]
        }
        for quote in payload.values():
            quote["quoteAgeSeconds"] = -1

        with patch("main.urlopen", return_value=self.mock_response(payload)):
            result = main.forex_gold_prices()

        self.assertTrue(
            all(item["status"] == "invalid_data" for item in result["markets"])
        )

    def test_missing_symbol_unavailable(self):
        payload = {
            "GBPUSD": self.valid_quote(),
            "XAUUSD": self.valid_quote(),
        }

        with patch("main.urlopen", return_value=self.mock_response(payload)):
            result = main.forex_gold_prices()

        self.assertEqual(result["markets"][0]["status"], "unavailable")

    def test_infinite_price_invalid(self):
        quote = self.valid_quote()
        quote["mid"] = "inf"
        payload = {
            symbol: quote
            for symbol in ["EURUSD", "GBPUSD", "XAUUSD"]
        }

        with patch("main.urlopen", return_value=self.mock_response(payload)):
            result = main.forex_gold_prices()

        self.assertTrue(all(item["status"] == "invalid_data" for item in result["markets"]))

    def test_provider_timeout(self):
        with patch("main.urlopen", side_effect=TimeoutError("provider timeout")):
            with self.assertRaises(main.HTTPException) as error:
                main.forex_gold_prices()

        self.assertEqual(error.exception.status_code, 502)


class ComparisonTests(unittest.TestCase):

    def provider_data(self, hyper_price=90000, binance_price=90010):
        timestamp = "2026-11-17T12:00:00+00:00"
        hyper = {
            "markets": [
                {
                    "symbol": symbol,
                    "price_usd": hyper_price,
                    "server_received_at": timestamp,
                }
                for symbol in ["BTC", "ETH"]
            ]
        }
        binance = {
            "markets": [
                {
                    "symbol": symbol,
                    "status": "available",
                    "mid_price": binance_price,
                    "bid": binance_price - 5,
                    "ask": binance_price + 5,
                    "server_received_at": timestamp,
                }
                for symbol in ["BTC", "ETH"]
            ]
        }
        return hyper, binance

    def test_valid_comparison(self):
        hyper, binance = self.provider_data()

        with patch("main.crypto_prices", return_value=hyper), patch(
            "main.binance_prices", return_value=binance
        ):
            result = main.compare_crypto_prices()

        self.assertEqual(result["status"], "comparison_ready")
        self.assertTrue(
            all(item["status"] == "comparison_available" for item in result["markets"])
        )

    def test_server_receive_gap_is_calculated_correctly(self):
        hyper, binance = self.provider_data()

        for item in binance["markets"]:
            item["server_received_at"] = "2026-11-17T12:00:03+00:00"

        with patch("main.crypto_prices", return_value=hyper), patch(
            "main.binance_prices", return_value=binance
        ):
            result = main.compare_crypto_prices()

        for item in result["markets"]:
            self.assertEqual(item["server_receive_gap_seconds"], 3.0)
            self.assertEqual(item["timestamp_gap_seconds"], 3.0)

    def test_one_symbol_unavailable(self):
        hyper, binance = self.provider_data()
        binance["markets"] = binance["markets"][:1]

        with patch("main.crypto_prices", return_value=hyper), patch(
            "main.binance_prices", return_value=binance
        ):
            result = main.compare_crypto_prices()

        self.assertEqual(result["markets"][0]["status"], "comparison_available")
        self.assertEqual(result["markets"][1]["status"], "source_unavailable")

    def test_infinite_price_invalid(self):
        hyper, binance = self.provider_data(hyper_price=float("inf"))

        with patch("main.crypto_prices", return_value=hyper), patch(
            "main.binance_prices", return_value=binance
        ):
            result = main.compare_crypto_prices()

        self.assertEqual(result["markets"][0]["status"], "invalid_data")
        self.assertEqual(result["markets"][1]["status"], "invalid_data")

    def test_provider_http_failure(self):
        with patch(
            "main.crypto_prices",
            side_effect=main.HTTPException(status_code=502, detail="Provider failed"),
        ), patch("main.binance_prices", return_value={"markets": []}):
            result = main.compare_crypto_prices()

        self.assertEqual(result["status"], "comparison_ready")
        self.assertTrue(
            all(item["status"] == "source_unavailable" for item in result["markets"])
        )

if __name__ == "__main__":
    unittest.main()
