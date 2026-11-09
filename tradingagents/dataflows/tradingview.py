"""Validation contract for TradingView Pine Script webhook alerts.

This module parses alert payloads but does not host a public webhook endpoint.
A deployment layer must provide HTTPS, request authentication, rate limiting,
and durable delivery before exposing an endpoint to TradingView.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation

from tradingagents.dataflows.forex import M5_SECONDS, normalize_pair, parse_timestamp

SUPPORTED_EVENTS = {
    "BOS",
    "CHOCH",
    "LIQUIDITY_SWEEP",
    "EQUAL_HIGH",
    "EQUAL_LOW",
    "SUPPLY_ZONE",
    "DEMAND_ZONE",
}
SUPPORTED_DIRECTIONS = {"LONG", "SHORT", "NEUTRAL"}


@dataclass(frozen=True, slots=True)
class TradingViewAlert:
    alert_id: str
    pair: str
    timeframe_seconds: int
    event: str
    direction: str
    timestamp: datetime
    source: str
    price: Decimal | None = None


def parse_tradingview_alert(payload: str | bytes | Mapping[str, object]) -> TradingViewAlert:
    """Parse a TradingView JSON message and enforce the M5 FX alert contract.

    Required fields: alert_id, pair, timeframe, event, direction, timestamp.
    timeframe must be the literal 5 or 5m.
    """
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    if isinstance(payload, str):
        try:
            data = json.loads(payload)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError("TradingView alert must be valid JSON") from exc
    else:
        data = payload
    if not isinstance(data, Mapping):
        raise ValueError("TradingView alert payload must be a JSON object")

    required = ("alert_id", "pair", "timeframe", "event", "direction", "timestamp")
    missing = [key for key in required if data.get(key) in (None, "")]
    if missing:
        raise ValueError(f"TradingView alert missing required fields: {', '.join(missing)}")

    timeframe = str(data["timeframe"]).strip().lower()
    if timeframe not in {"5", "5m", "m5"}:
        raise ValueError("TradingView execution alerts must use the M5 timeframe")

    event = str(data["event"]).strip().upper()
    if event not in SUPPORTED_EVENTS:
        raise ValueError(f"unsupported TradingView event: {event}")
    direction = str(data["direction"]).strip().upper()
    if direction not in SUPPORTED_DIRECTIONS:
        raise ValueError(f"unsupported TradingView direction: {direction}")

    price = None
    if data.get("price") not in (None, ""):
        try:
            price = Decimal(str(data["price"]))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("alert price must be a valid decimal") from exc
        if not price.is_finite() or price <= 0:
            raise ValueError("alert price must be finite and positive")

    alert_id = str(data["alert_id"]).strip()
    if not alert_id or len(alert_id) > 128:
        raise ValueError("alert_id must contain 1 to 128 characters")

    return TradingViewAlert(
        alert_id=alert_id,
        pair=normalize_pair(str(data["pair"])),
        timeframe_seconds=M5_SECONDS,
        event=event,
        direction=direction,
        timestamp=parse_timestamp(data["timestamp"], "alert timestamp"),
        source=str(data.get("source") or "TradingView").strip()[:80],
        price=price,
    )
