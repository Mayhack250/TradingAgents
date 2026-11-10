"""Tests for the read-only MetaTrader 5 FX adapter."""
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from tradingagents.dataflows.vendors.metatrader5 import MetaTrader5ForexProvider


class FakeMT5:
    TIMEFRAME_M5 = 5

    def __init__(self):
        self.initialized = False
        self.selected = []
        self.rates_args = None
        self.shutdown_called = False

    def initialize(self, *args):
        self.initialized = True
        return True

    def shutdown(self):
        self.shutdown_called = True
        self.initialized = False

    def last_error(self):
        return (1, "fake error")

    def symbol_select(self, symbol, enable):
        self.selected.append((symbol, enable))
        return True

    def copy_rates_from_pos(self, symbol, timeframe, start_pos, count):
        self.rates_args = (symbol, timeframe, start_pos, count)
        stamp = int(datetime(2026, 11, 9, 10, 0, tzinfo=UTC).timestamp())
        return [{
            "time": stamp, "open": 1.1, "high": 1.2,
            "low": 1.0, "close": 1.15,
        }]

    def symbol_info_tick(self, symbol):
        return SimpleNamespace(
            time=1794218685, time_msc=1794218685123, bid=1.1001, ask=1.1002
        )


def test_provider_reads_closed_m5_bars_and_actual_bid_ask():
    mt5 = FakeMT5()
    provider = MetaTrader5ForexProvider(
        symbol_map={"EURUSD": "EURUSD.a"}, mt5_module=mt5
    )
    with provider:
        candles = provider.get_m5_candles("eur/usd", limit=120)
        quote = provider.get_quote("EURUSD")
    assert mt5.rates_args == ("EURUSD.a", mt5.TIMEFRAME_M5, 1, 120)
    assert candles[0]["timestamp"] == "2026-11-09T10:00:00+00:00"
    assert quote is not None
    assert quote["bid"] == "1.1001"
    assert quote["ask"] == "1.1002"
    assert mt5.shutdown_called is True


def test_provider_requires_connection_and_valid_limit():
    provider = MetaTrader5ForexProvider(mt5_module=FakeMT5())
    with pytest.raises(RuntimeError, match="not connected"):
        provider.get_quote("EURUSD")
    provider.connect()
    with pytest.raises(ValueError, match="at least 1"):
        provider.get_m5_candles("EURUSD", limit=0)
    provider.close()


def test_provider_surfaces_terminal_initialization_error():
    class BrokenMT5(FakeMT5):
        def initialize(self, *args):
            return False

    provider = MetaTrader5ForexProvider(mt5_module=BrokenMT5())
    with pytest.raises(RuntimeError, match="initialize failed"):
        provider.connect()
