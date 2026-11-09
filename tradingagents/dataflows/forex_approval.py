"""Durable human approval gate for semi-automatic FX trade proposals.

Approval records intent only. This module never submits a broker order.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from tradingagents.dataflows.forex import M5_SECONDS, normalize_pair, parse_timestamp


def _positive_decimal(value: object, field: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{field} must be a valid decimal") from exc
    if not result.is_finite() or result <= 0:
        raise ValueError(f"{field} must be finite and positive")
    return result


@dataclass(frozen=True, slots=True)
class ForexTradeProposal:
    proposal_id: str
    pair: str
    side: str
    timeframe_seconds: int
    signal_at: datetime
    entry: Decimal
    stop_loss: Decimal
    take_profit: Decimal
    risk_percent: Decimal
    rationale: str

    def __post_init__(self) -> None:
        if not self.proposal_id or len(self.proposal_id) > 128:
            raise ValueError("proposal_id must contain 1 to 128 characters")
        object.__setattr__(self, "pair", normalize_pair(self.pair))
        side = self.side.strip().upper()
        if side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")
        object.__setattr__(self, "side", side)
        if self.timeframe_seconds != M5_SECONDS:
            raise ValueError("trade proposals must use M5 execution timing")
        object.__setattr__(self, "signal_at", parse_timestamp(self.signal_at, "signal_at"))
        for field in ("entry", "stop_loss", "take_profit", "risk_percent"):
            object.__setattr__(self, field, _positive_decimal(getattr(self, field), field))
        if self.side == "BUY" and not self.stop_loss < self.entry < self.take_profit:
            raise ValueError("BUY proposal requires stop_loss < entry < take_profit")
        if self.side == "SELL" and not self.take_profit < self.entry < self.stop_loss:
            raise ValueError("SELL proposal requires take_profit < entry < stop_loss")

    @property
    def reward_to_risk(self) -> Decimal:
        risk = abs(self.entry - self.stop_loss)
        reward = abs(self.take_profit - self.entry)
        return reward / risk


@dataclass(frozen=True, slots=True)
class StoredProposal:
    proposal: ForexTradeProposal
    status: str
    decision_at: datetime | None


class ForexApprovalStore:
    """SQLite-backed pending/approved/rejected proposal ledger."""

    def __init__(self, database: str | Path) -> None:
        self.database = str(database)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS forex_proposals (
                    proposal_id TEXT PRIMARY KEY,
                    pair TEXT NOT NULL,
                    side TEXT NOT NULL,
                    timeframe_seconds INTEGER NOT NULL,
                    signal_at TEXT NOT NULL,
                    entry TEXT NOT NULL,
                    stop_loss TEXT NOT NULL,
                    take_profit TEXT NOT NULL,
                    risk_percent TEXT NOT NULL,
                    rationale TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('PENDING', 'APPROVED', 'REJECTED')),
                    decision_at TEXT
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def submit(self, proposal: ForexTradeProposal) -> StoredProposal:
        """Persist a proposal once; duplicate IDs are rejected, not overwritten."""
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO forex_proposals (
                    proposal_id, pair, side, timeframe_seconds, signal_at,
                    entry, stop_loss, take_profit, risk_percent, rationale,
                    status, decision_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', NULL)
                """,
                (
                    proposal.proposal_id, proposal.pair, proposal.side,
                    proposal.timeframe_seconds, proposal.signal_at.isoformat(),
                    str(proposal.entry), str(proposal.stop_loss),
                    str(proposal.take_profit), str(proposal.risk_percent),
                    proposal.rationale,
                ),
            )
        return StoredProposal(proposal, "PENDING", None)

    def get(self, proposal_id: str) -> StoredProposal | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM forex_proposals WHERE proposal_id = ?", (proposal_id,)
            ).fetchone()
        return self._to_stored(row) if row else None

    def list_pending(self) -> list[StoredProposal]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM forex_proposals WHERE status = 'PENDING' ORDER BY signal_at"
            ).fetchall()
        return [self._to_stored(row) for row in rows]

    def approve(self, proposal_id: str, *, approved_at: datetime) -> StoredProposal:
        return self._decide(proposal_id, "APPROVED", approved_at)

    def reject(self, proposal_id: str, *, rejected_at: datetime) -> StoredProposal:
        return self._decide(proposal_id, "REJECTED", rejected_at)

    def _decide(self, proposal_id: str, status: str, at: datetime) -> StoredProposal:
        decision_at = parse_timestamp(at, "decision_at")
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE forex_proposals SET status = ?, decision_at = ?
                WHERE proposal_id = ? AND status = 'PENDING'
                """,
                (status, decision_at.isoformat(), proposal_id),
            )
            if cursor.rowcount != 1:
                raise ValueError(
                    f"proposal {proposal_id!r} does not exist or is no longer pending"
                )
        stored = self.get(proposal_id)
        if stored is None:
            raise RuntimeError("proposal disappeared after decision")
        return stored

    @staticmethod
    def _to_stored(row: sqlite3.Row) -> StoredProposal:
        proposal = ForexTradeProposal(
            proposal_id=row["proposal_id"],
            pair=row["pair"],
            side=row["side"],
            timeframe_seconds=row["timeframe_seconds"],
            signal_at=datetime.fromisoformat(row["signal_at"]),
            entry=Decimal(row["entry"]),
            stop_loss=Decimal(row["stop_loss"]),
            take_profit=Decimal(row["take_profit"]),
            risk_percent=Decimal(row["risk_percent"]),
            rationale=row["rationale"],
        )
        decision_at = (
            datetime.fromisoformat(row["decision_at"]) if row["decision_at"] else None
        )
        return StoredProposal(proposal, row["status"], decision_at)
