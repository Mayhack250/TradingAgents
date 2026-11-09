# Forex platform integrations

This branch adds a read-only MetaTrader 5 data adapter and a validated
TradingView alert payload contract. Neither integration places, modifies, or
closes a broker order.

## Intended flow

1. MetaTrader 5 is the source of broker-specific closed M5 candles and live
   bid/ask quotes. The provider reads the terminal's symbol feed, not a
   TradingView chart's displayed price.
2. TradingView Pine alerts are an optional second signal channel for chart
   events such as BOS, CHOCH, liquidity sweeps, equal highs/lows, and
   supply/demand zones.
3. The FX normalizer validates timestamps, OHLC, pair identity, quote spread,
   freshness, and gaps before data is used downstream.
4. The research engine reconciles both sources and prepares a trade proposal.
   The operator reviews and confirms the proposal. Order routing is a separate,
   disabled-by-default future component.

M5 is the only execution timeframe. Higher timeframes may be added for context
and directional bias, never as the source of M5 entry confirmation.

## MetaTrader 5 setup (Windows)

Install the optional bridge in the repository's Python environment:

```powershell
python -m pip install -e ".[mt5,dev]"
```

Open the MT5 desktop terminal and log in normally. Keep credentials in the
terminal; do not place account passwords in project configuration or webhook
messages.

Example read-only use:

```python
from datetime import datetime, timezone

from tradingagents.dataflows.vendors.forex import load_forex_snapshot
from tradingagents.dataflows.vendors.metatrader5 import MetaTrader5ForexProvider

provider = MetaTrader5ForexProvider(
    # Map broker-specific suffixes/prefixes when necessary:
    symbol_map={"EURUSD": "EURUSD.a", "GBPUSD": "GBPUSD.a"},
)

with provider:
    snapshot = load_forex_snapshot(
        provider,
        "EURUSD",
        as_of=datetime.now(timezone.utc),
        candle_limit=300,
    )

print(snapshot.candles[-1])
print(snapshot.quote)
print(snapshot.quality)
```

The adapter starts at MT5 bar position 1, intentionally excluding the
currently-forming candle. It uses MT5 tick bid/ask for spread; it does not
mistake the bar's spread field or last traded price for a live quote. Broker
symbol names differ, so configure symbol_map to match Market Watch exactly.

MT5's Python package communicates with a locally installed terminal and is
distributed for Windows. The terminal must be open and reachable on the same
machine. The adapter currently has no remote-terminal or mobile-only mode.

## TradingView alert contract

TradingView sends webhook alerts as HTTP POST requests. A valid JSON message is
sent with an application/json content type. TradingView requires webhook
two-factor authentication, accepts HTTPS on ports 443 (or HTTP on 80), and
cancels a webhook request if the receiver takes longer than roughly three
seconds. Delivery can occasionally fail, so monitor the TradingView alert log.

Use a Pine alert message with these fields:

```json
{
  "alert_id": "EURUSD-M5-CHOCH-001",
  "pair": "EURUSD",
  "timeframe": "5",
  "event": "CHOCH",
  "direction": "LONG",
  "timestamp": "{{timenow}}",
  "price": "{{close}}",
  "source": "TradingView"
}
```

Supported events: BOS, CHOCH, LIQUIDITY_SWEEP, EQUAL_HIGH, EQUAL_LOW,
SUPPLY_ZONE, DEMAND_ZONE. Direction must be LONG, SHORT, or NEUTRAL. Alerts
must be M5 and use a timezone-aware timestamp. The parser is available as:

```python
from tradingagents.dataflows.tradingview import parse_tradingview_alert

alert = parse_tradingview_alert(request_body)
```

This commit deliberately provides the strict payload parser, not a publicly
reachable webhook server. Before connecting TradingView to a running instance,
deploy an HTTPS receiver with request authentication, a secret stored outside
source control, request-size limits, rate limiting, duplicate-alert handling,
durable queueing, and a response under three seconds. Do not put broker
credentials or API keys in TradingView alert messages. A local-only endpoint
cannot receive TradingView webhooks without a secure public HTTPS ingress.

TradingView alerts are supporting chart events, not authoritative market
prices. Reconcile their symbol, timestamp, and event against MT5 data before
considering a setup. TradingView alert snapshots do not automatically update
when a Pine script or its inputs change; recreate the alert after modifying
the script.

## Semi-automatic execution boundary

Current implementation is intentionally read-only:
- no order_send call;
- no account login or password handling;
- no order, position, or stop modification;
- no automatic trade on a TradingView alert.

The next execution milestone should add a durable proposal/approval queue,
risk checks, idempotency keys, and an explicit human confirmation action.
Only after separate testing and explicit authorization should a broker
execution adapter be considered. Until then, this integration is market-data
and alert ingestion only.

## Validation

The new tests use fake MT5 terminal objects and synthetic TradingView payloads;
they do not require a broker login or TradingView account. Run:

```powershell
pytest -q tests/test_forex_data.py tests/test_forex_provider.py tests/test_metatrader5_provider.py tests/test_tradingview_alerts.py
ruff check tradingagents/dataflows/forex.py tradingagents/dataflows/vendors/forex.py tradingagents/dataflows/vendors/metatrader5.py tradingagents/dataflows/tradingview.py tests/test_forex_data.py tests/test_forex_provider.py tests/test_metatrader5_provider.py tests/test_tradingview_alerts.py
```
