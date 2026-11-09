"""Provider-neutral validation primitives for spot-FX market data.

All timestamps are timezone-aware UTC. Provider adapters should normalize raw
payloads into these immutable records before market data enters the research
graph. This module never fetches prices or fills missing observations.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import re
from typing import Iterable

M5_SECONDS = 300
DEFAULT_CANDLE_MAX_AGE_SECONDS = 600
DEFAULT_QUOTE_MAX_AGE_SECONDS = 30


def _decimal(value: object, field: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{field} must be a valid decimal") from exc
    if not result.is_finite():
        raise ValueError(f"{field} must be finite")
    return result


def _utc(value: datetime, field: str = "timestamp") -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value.astimezone(timezone.utc)


def normalize_pair(pair: str) -> str:
    """Normalize EUR/USD, EUR_USD, EUR-USD, or EURUSD to EURUSD."""
    if not isinstance(pair, str):
        raise ValueError("pair must be a string")
    normalized = re.sub(r"[/_\s-]", "", pair).upper()
    if not re.fullmatch(r"[A-Z]{6}", normalized):
        raise ValueError(f"invalid FX pair: {pair!r}")
    if normalized[:3] == normalized[3:]:
        raise ValueError("base and quote currencies must differ")
    return normalized


def pip_size(pair: str) -> Decimal:
    """Return conventional spot-FX pip size."""
    return Decimal("0.01") if normalize_pair(pair).endswith("JPY") else Decimal("0.0001")


@dataclass(frozen=True, slots=True)
class ForexCandle:
    pair: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    timeframe_seconds: int = M5_SECONDS

    def __post_init__(self) -> None:
        object.__setattr__(self, "pair", normalize_pair(self.pair))
        object.__setattr__(self, "timestamp", _utc(self.timestamp))
        for field in ("open", "high", "low", "close"):
            value = _decimal(getattr(self, field), field)
            if value <= 0:
                raise ValueError(f"{field} must be positive")
            object.__setattr__(self, field, value)
        if self.timeframe_seconds != M5_SECONDS:
            raise ValueError("execution candles must be M5 (300 seconds)")
        if self.timestamp.second or self.timestamp.microsecond or self.timestamp.minute % 5:
            raise ValueError("M5 candle timestamp must be on a 5-minute boundary")
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("high is inconsistent with OHLC values")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("low is inconsistent with OHLC values")


@dataclass(frozen=True, slots=True)
class ForexQuote:
    pair: str
    timestamp: datetime
    bid: Decimal
    ask: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "pair", normalize_pair(self.pair))
        object.__setattr__(self, "timestamp", _utc(self.timestamp))
        object.__setattr__(self, "bid", _decimal(self.bid, "bid"))
        object.__setattr__(self, "ask", _decimal(self.ask, "ask"))
        if self.bid <= 0 or self.ask <= 0:
            raise ValueError("bid and ask must be positive")
        if self.ask < self.bid:
            raise ValueError("ask cannot be below bid")

    @property
    def spread(self) -> Decimal:
        return self.ask - self.bid

    @property
    def spread_pips(self) -> Decimal:
        return self.spread / pip_size(self.pair)


def is_fresh(timestamp: datetime, *, as_of: datetime, max_age_seconds: int) -> bool:
    """False for stale or future-dated observations; timestamps must be aware."""
    observed = _utc(timestamp)
    reference = _utc(as_of, "as_of")
    if max_age_seconds < 0:
        raise ValueError("max_age_seconds cannot be negative")
    age = (reference - observed).total_seconds()
    return 0 <= age <= max_age_seconds


def validate_m5_series(candles: Iterable[ForexCandle]) -> list[ForexCandle]:
    """Validate a chronological, continuous, duplicate-free M5 series."""
    items = list(candles)
    if not items:
        raise ValueError("at least one candle is required")
    pair = items[0].pair
    if any(item.pair != pair for item in items):
        raise ValueError("all candles must belong to the same FX pair")
    ordered = sorted(items, key=lambda item: item.timestamp)
    if ordered != items:
        raise ValueError("candles must be supplied in chronological order")
    for previous, current in zip(ordered, ordered[1:]):
        delta = (current.timestamp - previous.timestamp).total_seconds()
        if delta == 0:
            raise ValueError("duplicate candle timestamp")
        if delta != M5_SECONDS:
            raise ValueError("M5 candle series contains a gap")
    return ordered
