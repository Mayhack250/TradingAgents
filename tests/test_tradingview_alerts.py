"""Tests for TradingView alert parsing and M5 enforcement."""

import pytest

from tradingagents.dataflows.tradingview import parse_tradingview_alert


VALID = {
    "alert_id": "eurusd-m5-001",
    "pair": "EUR/USD",
    "timeframe": "5",
    "event": "CHOCH",
    "direction": "LONG",
    "timestamp": "2026-11-09T10:05:00Z",
    "price": "1.15320",
}


def test_parses_valid_m5_alert():
    alert = parse_tradingview_alert(VALID)
    assert alert.pair == "EURUSD"
    assert alert.event == "CHOCH"
    assert alert.direction == "LONG"
    assert str(alert.price) == "1.15320"
    assert alert.timeframe_seconds == 300


def test_rejects_non_m5_alert():
    payload = {**VALID, "timeframe": "15"}
    with pytest.raises(ValueError, match="M5"):
        parse_tradingview_alert(payload)


def test_rejects_unsupported_event_and_direction():
    with pytest.raises(ValueError, match="unsupported TradingView event"):
        parse_tradingview_alert({**VALID, "event": "BUY"})
    with pytest.raises(ValueError, match="unsupported TradingView direction"):
        parse_tradingview_alert({**VALID, "direction": "UP"})


def test_rejects_naive_timestamp_and_bad_price():
    with pytest.raises(ValueError, match="timezone-aware"):
        parse_tradingview_alert({**VALID, "timestamp": "2026-11-09T10:05:00"})
    with pytest.raises(ValueError, match="positive"):
        parse_tradingview_alert({**VALID, "price": "0"})


def test_rejects_invalid_json_and_missing_fields():
    with pytest.raises(ValueError, match="valid JSON"):
        parse_tradingview_alert("{not-json")
    with pytest.raises(ValueError, match="missing required fields"):
        parse_tradingview_alert({"pair": "EURUSD"})
