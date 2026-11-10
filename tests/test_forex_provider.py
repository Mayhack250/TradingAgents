"""Tests for the vendor-neutral FX provider adapter."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from tradingagents.dataflows.vendors.forex import load_forex_snapshot

AS_OF = datetime(2026, 11, 9, 10, 5, tzinfo=UTC)


class FakeForexProvider:
    name = "fixture"

    def __init__(self, quote=None):
        self.quote = quote
        self.requested_pair = None
        self.requested_limit = None

    def get_m5_candles(self, pair, *, limit):
        self.requested_pair = pair
        self.requested_limit = limit
        return [
            {
                "timestamp": "2026-11-09T10:00:00Z",
                "open": "1.1000",
                "high": "1.1003",
                "low": "1.0999",
                "close": "1.1002",
            }
        ]

    def get_quote(self, pair):
        return self.quote


def test_snapshot_uses_normalized_pair_and_marks_absent_quote():
    provider = FakeForexProvider()
    snapshot = load_forex_snapshot(provider, "eur/usd", as_of=AS_OF, candle_limit=120)
    assert snapshot.pair == "EURUSD"
    assert snapshot.provider == "fixture"
    assert provider.requested_pair == "EURUSD"
    assert provider.requested_limit == 120
    assert snapshot.quote is None
    assert snapshot.quality.quote_fresh is False
    assert snapshot.quality.candle_fresh is True


def test_snapshot_normalizes_explicit_bid_ask_quote():
    provider = FakeForexProvider(
        {
            "timestamp": "2026-11-09T10:04:45Z",
            "bid": "1.10010",
            "ask": "1.10020",
        }
    )
    snapshot = load_forex_snapshot(provider, "EURUSD", as_of=AS_OF)
    assert snapshot.quote is not None
    assert snapshot.quote.spread_pips == Decimal("1")
    assert snapshot.quality.quote_fresh is True


def test_snapshot_does_not_accept_last_price_as_a_quote():
    provider = FakeForexProvider(
        {"timestamp": "2026-11-09T10:04:45Z", "price": "1.10015"}
    )
    with pytest.raises(ValueError, match="missing required field"):
        load_forex_snapshot(provider, "EURUSD", as_of=AS_OF)


def test_snapshot_rejects_zero_candle_limit():
    with pytest.raises(ValueError, match="at least 1"):
        load_forex_snapshot(FakeForexProvider(), "EURUSD", as_of=AS_OF, candle_limit=0)


def test_provider_errors_are_not_hidden():
    class BrokenProvider(FakeForexProvider):
        def get_m5_candles(self, pair, *, limit):
            raise TimeoutError("feed timeout")

    with pytest.raises(TimeoutError, match="feed timeout"):
        load_forex_snapshot(BrokenProvider(), "EURUSD", as_of=AS_OF)
