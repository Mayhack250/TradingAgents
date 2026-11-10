"""Unit tests for provider-neutral FX market-data normalization."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from tradingagents.dataflows.forex import (
    ForexCandle,
    ForexQuote,
    assess_data_quality,
    find_m5_gaps,
    is_fresh,
    normalize_candle_rows,
    normalize_pair,
    normalize_quote_payload,
    parse_timestamp,
    pip_size,
    validate_m5_series,
)


def test_pair_normalization_and_pip_size():
    assert normalize_pair("eur/usd") == "EURUSD"
    assert normalize_pair("GBP_USD") == "GBPUSD"
    assert pip_size("USDJPY") == Decimal("0.01")
    assert pip_size("EURUSD") == Decimal("0.0001")


@pytest.mark.parametrize("pair", ["EUR", "EURUSDD", "EUR/EUR", "123456", ""])
def test_rejects_invalid_pairs(pair):
    with pytest.raises(ValueError):
        normalize_pair(pair)


def test_timestamp_requires_timezone():
    with pytest.raises(ValueError, match="timezone-aware"):
        parse_timestamp("2026-11-09T10:00:00")
    assert parse_timestamp("2026-11-09T10:00:00Z") == datetime(
        2026, 11, 9, 10, 0, tzinfo=UTC
    )


def test_normalizes_provider_candles_and_orders_them():
    rows = [
        {"datetime": "2026-11-09T10:05:00Z", "open": "1.1001", "high": "1.1004",
         "low": "1.1000", "close": "1.1002"},
        {"datetime": "2026-11-09T10:00:00Z", "open": "1.1000", "high": "1.1003",
         "low": "1.0999", "close": "1.1001"},
    ]
    candles = normalize_candle_rows("EUR/USD", rows)
    assert [c.timestamp.minute for c in candles] == [0, 5]
    assert candles[0].close == Decimal("1.1001")


def test_rejects_non_m5_boundary_and_invalid_ohlc():
    with pytest.raises(ValueError, match="5-minute boundary"):
        ForexCandle("EURUSD", datetime(2026, 11, 9, 10, 1, tzinfo=UTC),
                    Decimal("1"), Decimal("1.1"), Decimal(".9"), Decimal("1"))
    with pytest.raises(ValueError, match="high is inconsistent"):
        ForexCandle("EURUSD", datetime(2026, 11, 9, 10, 0, tzinfo=UTC),
                    Decimal("1"), Decimal("1"), Decimal(".9"), Decimal("1.1"))


def test_quote_requires_real_bid_and_ask_and_calculates_spread():
    quote = normalize_quote_payload(
        "EURUSD",
        {"timestamp": "2026-11-09T10:00:00Z", "bid": "1.10000", "ask": "1.10012"},
    )
    assert quote.spread == Decimal("0.00012")
    assert quote.spread_pips == Decimal("1.2")
    with pytest.raises(ValueError, match="missing required field"):
        normalize_quote_payload(
            "EURUSD", {"timestamp": "2026-11-09T10:00:00Z", "price": "1.1"}
        )


def test_quote_rejects_crossed_market():
    with pytest.raises(ValueError, match="ask cannot be below bid"):
        ForexQuote("EURUSD", datetime(2026, 11, 9, 10, 0, tzinfo=UTC),
                   Decimal("1.2"), Decimal("1.1"))


def test_gap_is_reported_not_mistaken_for_invalid_weekend_data():
    start = datetime(2026, 11, 6, 21, 55, tzinfo=UTC)
    candles = [
        ForexCandle("EURUSD", start, Decimal("1.1"), Decimal("1.2"),
                    Decimal("1.0"), Decimal("1.1")),
        ForexCandle("EURUSD", start + timedelta(days=2), Decimal("1.1"),
                    Decimal("1.2"), Decimal("1.0"), Decimal("1.1")),
    ]
    assert len(validate_m5_series(candles)) == 2
    assert len(find_m5_gaps(candles)) == 1
    with pytest.raises(ValueError, match="contains a gap"):
        validate_m5_series(candles, require_contiguous=True)


def test_duplicate_timestamps_are_rejected():
    stamp = datetime(2026, 11, 9, 10, 0, tzinfo=UTC)
    candle = ForexCandle("EURUSD", stamp, Decimal("1.1"), Decimal("1.2"),
                         Decimal("1.0"), Decimal("1.1"))
    with pytest.raises(ValueError, match="duplicate"):
        validate_m5_series([candle, candle])


def test_freshness_rejects_stale_and_future_data():
    now = datetime(2026, 11, 9, 10, 10, tzinfo=UTC)
    assert is_fresh(now - timedelta(seconds=30), as_of=now, max_age_seconds=30)
    assert not is_fresh(now - timedelta(seconds=31), as_of=now, max_age_seconds=30)
    assert not is_fresh(now + timedelta(seconds=1), as_of=now, max_age_seconds=30)


def test_quality_assessment_marks_missing_quote_and_stale_candle():
    now = datetime(2026, 11, 9, 10, 30, tzinfo=UTC)
    candle = ForexCandle(
        "EURUSD", now - timedelta(minutes=20), Decimal("1.1"), Decimal("1.2"),
        Decimal("1.0"), Decimal("1.1")
    )
    quality = assess_data_quality([candle], None, as_of=now)
    assert quality.candle_fresh is False
    assert quality.quote_fresh is False
    assert quality.candle_count == 1
    assert quality.gap_count == 0
    assert quality.quote_at is None


def test_quality_assessment_rejects_quote_for_different_pair():
    now = datetime(2026, 11, 9, 10, 0, tzinfo=UTC)
    candle = ForexCandle("EURUSD", now, Decimal("1.1"), Decimal("1.2"),
                         Decimal("1.0"), Decimal("1.1"))
    quote = ForexQuote("GBPUSD", now, Decimal("1.2"), Decimal("1.2001"))
    with pytest.raises(ValueError, match="does not match"):
        assess_data_quality([candle], quote, as_of=now)
