"""Evidence provenance and point-in-time eligibility for investment research.

The register stores source metadata separately from analyst interpretation.
It does not fetch sources or decide whether a claim is true. Its job is to
make provenance inspectable and prevent post-cutoff publications from silently
entering a historical research dossier.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Literal
from urllib.parse import urlsplit

EvidenceStance = Literal["supports", "contradicts", "context"]
EvidenceType = Literal[
    "regulatory_filing", "audited_report", "company_release",
    "official_statistics", "official_statement", "independent_research",
    "news", "market_data", "other",
]


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    """One traceable source supporting, challenging, or contextualizing a claim.

    published_at is when information became public, not the financial period
    it describes. For filings, use the filing acceptance/publication date.
    Unknown publication dates cannot qualify for historical point-in-time use.
    """

    evidence_id: str
    claim: str
    publisher: str
    title: str
    source_url: str
    source_type: EvidenceType
    stance: EvidenceStance
    published_at: date | None
    accessed_at: datetime
    excerpt_or_note: str = ""
    filing_period_end: date | None = None
    accession_number: str | None = None
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("evidence_id", "claim", "publisher", "title", "source_url"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")

        parsed = urlsplit(self.source_url)
        if parsed.scheme not in {"https", "http"} or not parsed.netloc:
            raise ValueError("source_url must be an absolute HTTP(S) URL")
        if parsed.username or parsed.password:
            raise ValueError("source_url must not contain embedded credentials")

        accessed_at = _aware_utc(self.accessed_at, "accessed_at")
        if self.published_at and self.published_at > accessed_at.date():
            raise ValueError("published_at cannot be after accessed_at")
        if self.filing_period_end and self.published_at:
            if self.filing_period_end > self.published_at:
                raise ValueError("filing_period_end cannot be after published_at")
        if self.stance not in {"supports", "contradicts", "context"}:
            raise ValueError("stance must be supports, contradicts, or context")

        allowed_types = {
            "regulatory_filing", "audited_report", "company_release",
            "official_statistics", "official_statement", "independent_research",
            "news", "market_data", "other",
        }
        if self.source_type not in allowed_types:
            raise ValueError(f"unsupported source_type: {self.source_type}")

        object.__setattr__(self, "accessed_at", accessed_at)
        object.__setattr__(self, "tags", tuple(tag.strip() for tag in self.tags if tag.strip()))

    def is_available_as_of(self, cutoff: date) -> bool:
        """Whether the evidence was publicly available by the research cutoff."""
        return self.published_at is not None and self.published_at <= cutoff


@dataclass(slots=True)
class ResearchEvidenceRegister:
    """Deduplicated, inspectable evidence set for one dated research run."""

    instrument: str
    as_of_date: date
    records: list[EvidenceRecord] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.instrument.strip():
            raise ValueError("instrument must be non-empty")
        initial_records = list(self.records)
        self.records.clear()
        self.add_many(initial_records)

    def add(self, record: EvidenceRecord) -> None:
        if any(existing.evidence_id == record.evidence_id for existing in self.records):
            raise ValueError(f"duplicate evidence_id: {record.evidence_id}")
        self.records.append(record)

    def add_many(self, records: list[EvidenceRecord]) -> None:
        for record in records:
            self.add(record)

    @property
    def eligible(self) -> tuple[EvidenceRecord, ...]:
        """Evidence safe to use in the as-of thesis."""
        return tuple(record for record in self.records if record.is_available_as_of(self.as_of_date))

    @property
    def excluded(self) -> tuple[EvidenceRecord, ...]:
        """Evidence with unknown or post-cutoff publication dates."""
        return tuple(record for record in self.records if not record.is_available_as_of(self.as_of_date))

    @property
    def coverage(self) -> dict[str, int]:
        """Counts only; this is not a quality score."""
        return {
            "total": len(self.records),
            "eligible": len(self.eligible),
            "excluded": len(self.excluded),
            "unknown_publication_date": sum(record.published_at is None for record in self.records),
        }
