"""Read-only MetaTrader 5 adapter for broker-specific spot-FX data.

This adapter intentionally exposes candles and bid/ask quotes only. It does
not import or call order_send, modify positions, or access account credentials.
The MetaTrader5 Python package is an optional Windows-only dependency.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime, timezone

from tradingagents.dataflows.forex import normalize_pair


class MetaTrader5ForexProvider:
    """Read closed M5 bars and live bid/ask quotes from a local MT5 terminal.

    symbol_map maps normalized six-letter pairs to broker symbols, e.g.
    {"EURUSD": "EURUSD.a", "GBPUSD": "GBPUSD-pro"}.
    """

    name = "MetaTrader 5"

    def __init__(
        self,
        *,
        terminal_path: str | None = None,
        symbol_map: Mapping[str, str] | None = None,
        mt5_module: object | None = None,
    ) -> None:
        if mt5_module is None:
            try:
                import MetaTrader5 as mt5_module
            except ImportError as exc:
                raise RuntimeError(
                    "MetaTrader5 is not installed. On Windows install the optional "
                    "dependency with: pip install '.[mt5]'"
                ) from exc
        self._mt5 = mt5_module
        self._terminal_path = terminal_path
        self._symbol_map = {
            normalize_pair(pair): symbol for pair, symbol in (symbol_map or {}).items()
        }
        self._connected = False

    def _symbol(self, pair: str) -> str:
        normalized = normalize_pair(pair)
        return self._symbol_map.get(normalized, normalized)

    def connect(self) -> None:
        """Initialize the local terminal; credentials remain in MT5 itself."""
        if self._connected:
            return
        initialized = (
            self._mt5.initialize(self._terminal_path)
            if self._terminal_path
            else self._mt5.initialize()
        )
        if not initialized:
            raise RuntimeError(f"MetaTrader 5 initialize failed: {self._mt5.last_error()}")
        self._connected = True

    def close(self) -> None:
        """Close this adapter's terminal connection."""
        if self._connected:
            self._mt5.shutdown()
            self._connected = False

    def __enter__(self) -> MetaTrader5ForexProvider:
        self.connect()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def _require_connection(self) -> None:
        if not self._connected:
            raise RuntimeError("MetaTrader 5 provider is not connected; call connect() first")

    def _select_symbol(self, symbol: str) -> None:
        if not self._mt5.symbol_select(symbol, True):
            raise RuntimeError(
                f"Could not select MT5 symbol {symbol!r}: {self._mt5.last_error()}"
            )

    def get_m5_candles(self, pair: str, *, limit: int) -> list[dict[str, object]]:
        """Return closed M5 candles only, newest last; never include the forming bar."""
        self._require_connection()
        if limit < 1:
            raise ValueError("limit must be at least 1")
        symbol = self._symbol(pair)
        self._select_symbol(symbol)
        rates = self._mt5.copy_rates_from_pos(
            symbol, self._mt5.TIMEFRAME_M5, 1, limit
        )
        if rates is None:
            raise RuntimeError(
                f"MT5 returned no candle data for {symbol}: {self._mt5.last_error()}"
            )
        rows: list[dict[str, object]] = []
        for rate in rates:
            stamp = datetime.fromtimestamp(int(rate["time"]), tz=UTC)
            rows.append(
                {
                    "timestamp": stamp.isoformat(),
                    "open": str(rate["open"]),
                    "high": str(rate["high"]),
                    "low": str(rate["low"]),
                    "close": str(rate["close"]),
                }
            )
        return rows

    def get_quote(self, pair: str) -> dict[str, object] | None:
        """Return an actual terminal tick bid/ask; no midpoint or last-price fallback."""
        self._require_connection()
        symbol = self._symbol(pair)
        self._select_symbol(symbol)
        tick = self._mt5.symbol_info_tick(symbol)
        if tick is None:
            return None
        time_msc = getattr(tick, "time_msc", 0)
        timestamp = (
            datetime.fromtimestamp(time_msc / 1000, tz=timezone.utc)
            if time_msc
            else datetime.fromtimestamp(int(tick.time), tz=timezone.utc)
        )
        return {
            "timestamp": timestamp.isoformat(),
            "bid": str(tick.bid),
            "ask": str(tick.ask),
        }
