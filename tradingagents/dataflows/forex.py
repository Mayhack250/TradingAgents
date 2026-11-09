"""Provider-neutral validation and normalization primitives for spot-FX data.

All timestamps are timezone-aware UTC. Provider adapters normalize raw payloads
into these immutable records before market data enters the research graph.
Missing observations are surfaced; prices and quotes are never synthesized.
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

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
    return value.astimezone(UTC)


def parse_timestamp(value: object, field: str = "timestamp") -> datetime:
    """Parse an ISO-8601 timestamp and reject timezone-naive values."""
    if isinstance(value, datetime):
        return _utc(value, field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be an ISO-8601 timestamp")
    raw = value.strip()
    if raw.endswith(("Z", "z")):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from exc
    return _utc(parsed, field)


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


@dataclass(frozen=True, slots=True)
class ForexDataQuality:
    """Explicit freshness and coverage facts; never a synthetic quality score."""

    candle_fresh: bool
    quote_fresh: bool
    candle_count: int
    gap_count: int
    latest_candle_at: datetime | None
    quote_at: datetime | None


def _pick(row: Mapping[str, object], *names: str) -> object:
    for name in names:
        if name in row and row[name] not in (None, ""):
            return row[name]
    raise ValueError(f"missing required field; expected one of: {', '.join(names)}")


def normalize_candle_rows(
    pair: str,
    rows: Sequence[Mapping[str, object]],
) -> list[ForexCandle]:
    """Normalize common provider OHLC row shapes and return chronological M5 bars.

    Accepted timestamp keys: timestamp, datetime, time, date.
    OHLC keys are case-insensitive. Provider intervals must already be M5.
    """
    normalized_pair = normalize_pair(pair)
    if not rows:
        raise ValueError(f"provider returned no M5 candles for {normalized_pair}")
    candles = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise ValueError(f"candle row {index} must be a mapping")
        lower = {str(key).lower(): value for key, value in row.items()}
        timestamp = parse_timestamp(
            _pick(lower, "timestamp", "datetime", "time", "date"),
            f"candle row {index} timestamp",
        )
        candles.append(
            ForexCandle(
                pair=normalized_pair,
                timestamp=timestamp,
                open=_pick(lower, "open", "o"),
                high=_pick(lower, "high", "h"),
                low=_pick(lower, "low", "l"),
                close=_pick(lower, "close", "c"),
            )
        )
    candles.sort(key=lambda candle: candle.timestamp)
    return validate_m5_series(candles)


def normalize_quote_payload(
    pair: str,
    payload: Mapping[str, object],
) -> ForexQuote:
    """Normalize an explicit bid/ask quote; midpoint/last-price-only data is rejected."""
    if not isinstance(payload, Mapping):
        raise ValueError("quote payload must be a mapping")
    lower = {str(key).lower(): value for key, value in payload.items()}
    return ForexQuote(
        pair=normalize_pair(pair),
        timestamp=parse_timestamp(
            _pick(lower, "timestamp", "datetime", "time", "date"),
            "quote timestamp",
        ),
        bid=_pick(lower, "bid", "best_bid"),
        ask=_pick(lower, "ask", "best_ask"),
    )


def is_fresh(timestamp: datetime, *, as_of: datetime, max_age_seconds: int) -> bool:
    """False for stale or future-dated observations; timestamps must be aware."""
    observed = _utc(timestamp)
    reference = _utc(as_of, "as_of")
    if max_age_seconds < 0:
        raise ValueError("max_age_seconds cannot be negative")
    age = (reference - observed).total_seconds()
    return 0 <= age <= max_age_seconds


def find_m5_gaps(candles: Iterable[ForexCandle]) -> list[tuple[datetime, datetime]]:
    """Return missing M5 intervals between adjacent bars.

    Gaps are reported rather than rejected because FX weekends and market
    holidays create legitimate closures. A caller must interpret gaps against
    the relevant trading calendar before classifying them as feed failures.
    """
    items = list(candles)
    if not items:
        return []
    pair = items[0].pair
    if any(item.pair != pair for item in items):
        raise ValueError("all candles must belong to the same FX pair")
    ordered = sorted(items, key=lambda item: item.timestamp)
    gaps = []
    for previous, current in zip(ordered, ordered[1:], strict=False):
        delta = (current.timestamp - previous.timestamp).total_seconds()
        if delta <= 0:
            raise ValueError("duplicate or out-of-order candle timestamp")
        if delta > M5_SECONDS:
            gaps.append((previous.timestamp, current.timestamp))
    return gaps


def validate_m5_series(
    candles: Iterable[ForexCandle],
    *,
    require_contiguous: bool = False,
) -> list[ForexCandle]:
    """Validate one-pair M5 candles; optionally require every 5-minute interval."""
    items = list(candles)
    if not items:
        raise ValueError("at least one candle is required")
    pair = items[0].pair
    if any(item.pair != pair for item in items):
        raise ValueError("all candles must belong to the same FX pair")
    ordered = sorted(items, key=lambda item: item.timestamp)
    for previous, current in zip(ordered, ordered[1:]):
        delta = (current.timestamp - previous.timestamp).total_seconds()
        if delta <= 0:
            raise ValueError("duplicate candle timestamp")
        if require_contiguous and delta != M5_SECONDS:
            raise ValueError("M5 candle series contains a gap")
    return ordered


def assess_data_quality(
    candles: Sequence[ForexCandle],
    quote: ForexQuote | None,
    *,
    as_of: datetime,
    candle_max_age_seconds: int = DEFAULT_CANDLE_MAX_AGE_SECONDS,
    quote_max_age_seconds: int = DEFAULT_QUOTE_MAX_AGE_SECONDS,
) -> ForexDataQuality:
    """Assess freshness and observed gaps without hiding missing/stale data."""
    reference = _utc(as_of, "as_of")
    series = validate_m5_series(candles)
    if quote is not None and quote.pair != series[-1].pair:
        raise ValueError("quote pair does not match candle pair")
    latest = series[-1].timestamp
    return ForexDataQuality(
        candle_fresh=is_fresh(latest, as_of=reference, max_age_seconds=candle_max_age_seconds),
        quote_fresh=(
            is_fresh(quote.timestamp, as_of=reference, max_age_seconds=quote_max_age_seconds)
            if quote is not None
            else False
        ),
        candle_count=len(series),
        gap_count=len(find_m5_gaps(series)),
        latest_candle_at=latest,
        quote_at=quote.timestamp if quote is not None else None,
    )
