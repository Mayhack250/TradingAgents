# Daily Intelligence Report — ADHD-Friendly Presentation Specification

## Purpose

The daily intelligence report is delivered directly in ChatGPT. It is a compact, engaging decision-support briefing that helps the reader understand what matters, why it matters, what is uncertain, and what to investigate next. It is not a dashboard, a stream of headlines, a trade signal service, or personalized financial advice.

The near-term emphasis follows the project pivot: public equities and the market context affecting them. Forex is retained as secondary context only when it materially affects equity risk or is explicitly requested. A personal virtual portfolio remains deferred.

## Presentation principles

- Lead with the three most important takeaways, not a long market recap.
- Use short sections, clear labels, whitespace, compact tables, and one idea per block.
- Use progressive disclosure: a short briefing first, then expandable/deeper detail in a predictable order.
- Use plain language first; define necessary financial terms in a short inline glossary.
- Prefer visual comparisons, small charts, timelines, scorecards, and scenario ranges over dense prose.
- Avoid decorative charts. Every visual must answer a question and show units, timeframe, source, and timestamp.
- Use a consistent visual vocabulary and restrained colors. Color must never be the only carrier of meaning.
- End each major section with a concrete "why it matters" and, where useful, "what to watch next".
- Provide a clear stopping point: the reader should be able to finish the essential briefing quickly and return later for deeper research.
- Do not use gamification that pressures the reader to trade, invest, or keep reading.

## Standard daily report flow

### 1. Opening snapshot

Show:
- Report date, timezone (Africa/Kigali), data cutoff, and last refresh.
- Coverage status: complete, partial, or unavailable, with missing feeds called out.
- A short market regime label only when supported by defined evidence (for example, risk-on, risk-off, mixed, or unclear).
- Three key takeaways, each limited to a few sentences.
- A "time to read" estimate that is based on actual report length, not fabricated precision.

### 2. Focus panel — what deserves attention today

Limit to three ranked items. Each item contains:
- What happened or changed.
- Why it matters to equities or the broader market.
- Which sectors, companies, or assets may be exposed.
- Evidence quality and the source link.
- What would confirm or weaken the interpretation.

Do not force three items when fewer than three are material.

### 3. Market pulse

Use compact visual summaries for:
- Major US equity indices and relevant global benchmarks.
- Treasury yields, dollar, major commodities, and volatility where relevant.
- Sector and factor leadership/laggards where reliable data is available.
- Earnings and macro events on the near-term calendar.

For each quote or statistic, state currency/unit, period change, timestamp, and source. Distinguish delayed, end-of-day, and live data. Never label delayed or stale data as live.

### 4. Equity opportunities and company watch

This is a research queue, not a buy list. Include only companies with a defensible evidence-based reason to investigate. Each company card should show:
- Issuer name, ticker, exchange, share class and reporting currency.
- One-sentence business description.
- Why it is on today's research radar.
- Latest relevant catalyst and date.
- Initial research stance: investigate, watch, avoid for now, or insufficient evidence.
- Valuation context only when inputs are available and dated.
- Principal risk and the key unanswered question.
- Links to primary evidence.

Do not invent a user watchlist, personal holdings, or portfolio allocation. Clearly label discovery candidates as system-selected research leads.

### 5. Ratings and scorecards

Percentages are allowed only when a documented rubric and adequate evidence support them. Every score must show its definition, evidence coverage, as-of date, and limitations.

Recommended independent dimensions:
- **Business quality (0–100):** durability of demand, competitive position, margins/returns, balance-sheet resilience, and execution evidence.
- **Financial health (0–100):** cash conversion, leverage, liquidity, profitability, dilution and financial-statement quality.
- **Valuation attractiveness (0–100):** valuation relative to defensible scenarios, growth assumptions, peer context and downside; higher means more attractive, not more certain.
- **Risk level (0–100):** higher means more risk, not a better score. Show key drivers and distinguish business, financial, valuation, governance and event risks.
- **Evidence confidence (0–100):** completeness, recency, primary-source share, consistency and point-in-time integrity of the evidence used.
- **Thesis strength (0–100):** balance of supporting and contradicting evidence, scenario robustness and clarity of invalidation conditions.

Rules:
- These are structured assessments, not measured probabilities of profit, future returns, or success.
- Never present a score as an objective fact or a guarantee.
- Do not average dimensions into one opaque overall score. If a composite is ever introduced, publish its formula, weights, missing-data treatment and sensitivity.
- If the evidence is inadequate, show "Not rated — insufficient evidence" rather than manufacture a percentage.
- Explain the two or three largest drivers behind each score.
- Keep risk direction explicit: a high risk score is a warning.
- Separate confidence in the evidence from confidence in the investment outcome.
- Recalibrate scores only when the rubric changes or new evidence justifies a change; explain score changes.

### 6. One company deep dive

Feature at most one main company deep dive per daily edition unless the user requests more. Use a consistent sequence:
1. What the company does and how it earns money.
2. Revenue and profit drivers.
3. Financial trend visual (with fiscal periods and units).
4. Balance-sheet and cash-flow health.
5. Competitive position and management/capital allocation.
6. Valuation range and assumptions, if supportable.
7. Bull/base/bear scenarios and sensitivities.
8. Strongest opposing evidence.
9. Risks, catalysts, and thesis invalidation conditions.
10. What to research next.

### 7. Learning and engagement layer

Include one small learning element per report:
- "Concept in 60 seconds": explain one useful investing or accounting concept using the company/market example in the report.
- "Read this chart": explain one visual and what it does and does not show.
- "Challenge the thesis": one question that encourages independent judgment.
- "Recall check": one optional short question; reveal or provide the answer immediately below so it never blocks the report.

Use adult, respectful language. Do not assume the reader has no knowledge. Avoid childish gamification, streaks, excessive emojis, or artificial urgency.

### 8. What changed and what to watch

Show:
- Changes since the previous report, only when a prior comparable report exists.
- Upcoming earnings, economic releases, regulatory events and other dated catalysts.
- The observable condition that would make a thesis stronger or weaker.
- A short "no action required" note when the day contains no material change.

### 9. Close — three useful next steps

Give no more than three concrete research actions, ranked by usefulness. Examples: inspect a primary filing, compare two peers, or test a valuation assumption. Do not turn these into trade instructions.

## Evidence and freshness labels

Use consistent labels:
- **Primary source** — filing, audited report, regulator, official company release, exchange or official statistics.
- **Independent source** — reputable reporting or independent research.
- **Estimate** — management guidance, analyst consensus or model estimate, with provider and date.
- **Model interpretation** — analyst/agent inference, explicitly not a source fact.
- **Unverified / missing** — information could not be confirmed.

Each material number should have source, publication date or period, retrieval timestamp when available, currency/unit, and data status. Preserve source conflicts and explain unresolved differences.

## Visual standards

- Use charts only when enough comparable observations exist.
- Label axes, units, period, and source; do not crop axes to exaggerate changes.
- Prefer simple line charts for trends, horizontal bars for peer comparisons, stacked bars for composition, and timelines for catalysts.
- Use scenario bands or ranges rather than false-precision target lines.
- Include a short written interpretation beside every chart.
- Use a consistent palette and icons sparingly; never rely on color alone.
- Keep mobile readability as a first-class constraint.

## Report completion and quality gates

Before publishing:
- Confirm report date, timezone, data cutoff and refresh timestamps.
- Distinguish live, delayed, end-of-day and stale data.
- Verify material claims against underlying sources, prioritizing primary evidence.
- Flag missing, conflicting or non-comparable information.
- Check every score against its rubric and evidence sufficiency.
- Ensure scores are not described as probabilities of return or profit.
- Ensure the report has a concise opening, no more than three focus items, at most one main deep dive, one learning element, and a clear close.
- If the data feed or source retrieval fails, publish a clearly marked partial report or state that the report cannot be completed; never fill gaps with invented figures.

## Deferred virtual portfolio interface

The future paper portfolio may add holdings, cash, position sizing, transactions, corporate actions, benchmark-relative performance, drawdown and exposure. Until that phase is explicitly started, do not show portfolio balances, pretend holdings exist, or imply that research candidates are already owned.
