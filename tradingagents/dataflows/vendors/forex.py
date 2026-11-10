"""Provider contract and snapshot assembly for spot-FX data.

Concrete vendors implement this small interface. The core framework owns
normalization, timestamp validation, spread calculation, and data-quality
flags so vendor payloads cannot bypass the same checks.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from tradingagents.dataflows.forex import (
    DEFAULT_CANDLE_MAX_AGE_SECONDS,
    DEFAULT_QUOTE_MAX_AGE_SECONDS,
    ForexCandle,
    ForexDataQuality,
    ForexQuote,
    assess_data_quality,
    normalize_candle_rows,
    normalize_pair,
    normalize_quote_payload,
)


class ForexProvider(Protocol):
    """Minimal interface required from a concrete market-data vendor."""

    name: str

    def get_m5_candles(
        self, pair: str, *, limit: int
    ) -> Sequence[Mapping[str, object]]:
        """Return raw M5 OHLC rows with timezone-aware timestamps."""

    def get_quote(self, pair: str) -> Mapping[str, object] | None:
        """Return explicit bid/ask quote, or None when unavailable."""


@dataclass(frozen=True, slots=True)
class ForexSnapshot:
    pair: str
    provider: str
    candles: tuple[ForexCandle, ...]
    quote: ForexQuote | None
    quality: ForexDataQuality


def load_forex_snapshot(
    provider: ForexProvider,
    pair: str,
    *,
    as_of: datetime,
    candle_limit: int = 300,
    candle_max_age_seconds: int = DEFAULT_CANDLE_MAX_AGE_SECONDS,
    quote_max_age_seconds: int = DEFAULT_QUOTE_MAX_AGE_SECONDS,
) -> ForexSnapshot:
    """Fetch and validate one pair without substituting missing/stale values.

    Vendor/network errors are intentionally allowed to propagate to the
    calling orchestration layer, which can record the failed source. A missing
    quote remains None and is marked stale/unavailable by quality assessment.
    """
    normalized_pair = normalize_pair(pair)
    if candle_limit < 1:
        raise ValueError("candle_limit must be at least 1")

    raw_candles = provider.get_m5_candles(normalized_pair, limit=candle_limit)
    candles = normalize_candle_rows(normalized_pair, raw_candles)
    raw_quote = provider.get_quote(normalized_pair)
    quote = normalize_quote_payload(normalized_pair, raw_quote) if raw_quote else None
    quality = assess_data_quality(
        candles,
        quote,
        as_of=as_of,
        candle_max_age_seconds=candle_max_age_seconds,
        quote_max_age_seconds=quote_max_age_seconds,
    )
    return ForexSnapshot(
        pair=normalized_pair,
        provider=getattr(provider, "name", provider.__class__.__name__),
        candles=tuple(candles),
        quote=quote,
        quality=quality,
    )
