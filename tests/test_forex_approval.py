"""Tests for the durable semi-automatic FX approval gate."""
from datetime import datetime, timezone
from decimal import Decimal
import sqlite3

import pytest

from tradingagents.dataflows.forex_approval import ForexApprovalStore, ForexTradeProposal

UTC = timezone.utc
NOW = datetime(2026, 11, 9, 10, 5, tzinfo=UTC)


def make_proposal(**overrides):
    values = {
        "proposal_id": "setup-001",
        "pair": "EURUSD",
        "side": "BUY",
        "timeframe_seconds": 300,
        "signal_at": NOW,
        "entry": Decimal("1.1000"),
        "stop_loss": Decimal("1.0990"),
        "take_profit": Decimal("1.1030"),
        "risk_percent": Decimal("0.5"),
        "rationale": "M5 bullish CHOCH after liquidity sweep",
    }
    values.update(overrides)
    return ForexTradeProposal(**values)


def test_proposal_validates_m5_and_reward_to_risk():
    proposal = make_proposal()
    assert proposal.reward_to_risk == Decimal("3")
    with pytest.raises(ValueError, match="M5"):
        make_proposal(timeframe_seconds=900)
    with pytest.raises(ValueError, match="stop_loss < entry"):
        make_proposal(stop_loss=Decimal("1.1010"))


def test_pending_proposal_is_durable_and_requires_explicit_approval(tmp_path):
    database = tmp_path / "approvals.sqlite3"
    store = ForexApprovalStore(database)
    submitted = store.submit(make_proposal())
    assert submitted.status == "PENDING"
    assert len(store.list_pending()) == 1

    restarted_store = ForexApprovalStore(database)
    approved = restarted_store.approve("setup-001", approved_at=NOW)
    assert approved.status == "APPROVED"
    assert approved.decision_at == NOW
    assert restarted_store.list_pending() == []


def test_rejected_proposal_cannot_be_approved_again(tmp_path):
    store = ForexApprovalStore(tmp_path / "approvals.sqlite3")
    store.submit(make_proposal())
    rejected = store.reject("setup-001", rejected_at=NOW)
    assert rejected.status == "REJECTED"
    with pytest.raises(ValueError, match="no longer pending"):
        store.approve("setup-001", approved_at=NOW)


def test_duplicate_ids_and_unknown_ids_are_rejected(tmp_path):
    store = ForexApprovalStore(tmp_path / "approvals.sqlite3")
    store.submit(make_proposal())
    with pytest.raises(sqlite3.IntegrityError):
        store.submit(make_proposal())
    with pytest.raises(ValueError, match="does not exist"):
        store.approve("missing", approved_at=NOW)
