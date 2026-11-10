from datetime import UTC, date, datetime

import pytest

from tradingagents.research.evidence import EvidenceRecord, ResearchEvidenceRegister


def make_record(
    evidence_id="sec-10k",
    *,
    published_at=date(2026, 10, 30),
    accessed_at=datetime(2026, 11, 2, 12, tzinfo=UTC),
):
    return EvidenceRecord(
        evidence_id=evidence_id,
        claim="Revenue increased year over year.",
        publisher="Example regulator",
        title="Annual filing",
        source_url="https://www.example.gov/filing/123",
        source_type="regulatory_filing",
        stance="supports",
        published_at=published_at,
        accessed_at=accessed_at,
        filing_period_end=date(2026, 9, 30),
        accession_number="0000000000-26-000001",
    )


def test_evidence_is_eligible_only_when_published_by_cutoff():
    register = ResearchEvidenceRegister("EXM", date(2026, 10, 31))
    register.add(make_record())
    register.add(make_record("future", published_at=date(2026, 11, 1)))
    register.add(make_record("unknown", published_at=None))

    assert [item.evidence_id for item in register.eligible] == ["sec-10k"]
    assert {item.evidence_id for item in register.excluded} == {"future", "unknown"}
    assert register.coverage == {
        "total": 3,
        "eligible": 1,
        "excluded": 2,
        "unknown_publication_date": 1,
    }


def test_duplicate_evidence_ids_are_rejected():
    register = ResearchEvidenceRegister("EXM", date(2026, 10, 31))
    record = make_record()
    register.add(record)

    with pytest.raises(ValueError, match="duplicate evidence_id"):
        register.add(record)


def test_naive_access_timestamp_is_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        make_record(accessed_at=datetime(2026, 11, 2, 12))


def test_future_publication_relative_to_access_is_rejected():
    with pytest.raises(ValueError, match="cannot be after accessed_at"):
        make_record(published_at=date(2026, 11, 3))


def test_filing_period_end_is_not_mistaken_for_publication_date():
    record = make_record(
        published_at=date(2026, 10, 30),
        accessed_at=datetime(2026, 11, 2, 12, tzinfo=UTC),
    )
    assert record.filing_period_end == date(2026, 9, 30)
    assert record.is_available_as_of(date(2026, 10, 29)) is False
    assert record.is_available_as_of(date(2026, 10, 30)) is True


def test_url_must_be_absolute_http_or_https_without_credentials():
    with pytest.raises(ValueError, match="absolute HTTP"):
        EvidenceRecord(
            evidence_id="bad-url",
            claim="claim",
            publisher="publisher",
            title="title",
            source_url="javascript:alert(1)",
            source_type="news",
            stance="context",
            published_at=date(2026, 10, 30),
            accessed_at=datetime(2026, 11, 2, 12, tzinfo=UTC),
        )
