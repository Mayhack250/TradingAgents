# Equity Research-First Direction

## Purpose

This fork is being developed as a research-first platform for understanding publicly traded companies and the markets they operate in. The immediate goal is not to automate trades. It is to help a researcher investigate a business, test an investment thesis, compare alternatives, understand valuation and risk, and produce a traceable research report.

The current development focus is **public-equity research**. The existing multi-agent architecture is a useful foundation: specialist analysts gather evidence, bull and bear researchers challenge the thesis, and a research manager synthesizes the result.

## Current scope

The first research workflow should cover:

1. **Company identity and business model** — what the company sells, who pays, how it makes money, geographic and segment exposure, and key dependencies.
2. **Financial quality and trajectory** — revenue growth, margins, cash generation, balance sheet, dilution, capital allocation, and multi-year trends.
3. **Industry and competitive position** — market structure, competitors, suppliers, customers, substitutes, regulation, and defensibility.
4. **Management and governance** — leadership track record, incentives, ownership, capital allocation, related-party issues, and material governance risks where reliable evidence exists.
5. **Valuation** — relevant multiples and, where data supports it, scenario-based valuation. State assumptions and avoid false precision.
6. **Macro and catalysts** — rates, inflation, currencies, commodities, policy, earnings dates, product cycles, litigation, and other material events.
7. **Bull/base/bear thesis** — strongest supporting evidence, strongest counter-evidence, key assumptions, invalidation conditions, and what new evidence would change the conclusion.
8. **Research conclusion** — an evidence-weighted assessment such as attractive / watch / unattractive, with confidence and unresolved questions. This is research output, not an instruction to execute a trade.

The platform should support US-listed equities first while retaining the upstream project's international ticker conventions where data coverage is adequate. Crypto and forex are not the priority for this phase.

## Research quality rules

- **Source every material claim.** Prefer primary sources: SEC filings, company investor-relations materials, official earnings releases and transcripts, regulator publications, and central-bank or statistical-agency data. Use reputable secondary sources for context, not as substitutes for primary evidence.
- **Preserve point-in-time integrity.** A historical research run must not use information published after its as-of date. Record publication dates and distinguish an event date from the date the information became public.
- **Separate facts, estimates, and interpretations.** Label management guidance, consensus estimates, model assumptions, and agent-generated inference distinctly.
- **Show disagreement.** Include the best bear case and evidence that weakens the preferred thesis. Do not let a consensus summary erase material disagreement.
- **Expose missingness.** State when filings, segment data, estimates, transcripts, pricing, or other evidence are unavailable, stale, conflicting, or not comparable.
- **Avoid fabricated precision.** Do not invent financial figures, valuation inputs, source quotations, catalysts, or confidence levels. If the evidence is insufficient, say so.
- **Make analysis reproducible.** Record the ticker, exchange, currency, as-of date, data sources, retrieval timestamps where available, configuration, and assumptions used for each report.

## Standard research report

A complete company report should contain:

1. Executive thesis and as-of date
2. Company and business-model overview
3. Financial performance and balance-sheet review
4. Industry, competitors, and moat assessment
5. Management, governance, and capital allocation
6. Valuation framework with assumptions and scenarios
7. Macro, event, and catalyst map
8. Bull / base / bear cases
9. Key risks and thesis invalidation conditions
10. Evidence gaps, open questions, and source register
11. Final research stance and confidence rationale

Short reports may omit sections only when they clearly mark them as not assessed.

## Phased development

### Phase 1 — Research foundation (current)

- Audit the existing stock research agents, data tools, report assembly, and point-in-time controls.
- Define a consistent research schema and source/evidence record.
- Improve company, industry, financial-statement, management, valuation, and risk coverage.
- Produce source-linked, reproducible research reports.
- Add tests for date leakage, source attribution, missing data, and numerical consistency.

### Phase 2 — Research depth and comparison

- Add repeatable company-to-company and peer-group comparisons.
- Improve scenario analysis and valuation sensitivity.
- Add industry and thematic research that can connect macro drivers to company exposure.
- Track thesis changes between dated research runs.

### Phase 3 — Personal virtual portfolio (deferred)

A personal virtual portfolio may be developed later, after the research foundation is reliable. It is explicitly out of scope for the current phase. No personal holdings, allocation rules, paper orders, or portfolio assumptions should be invented or silently initialized.

### Phase 4 — Optional execution integrations (not current scope)

Any future broker, charting, or execution integration requires a separate design and explicit approval. This phase does not authorize live orders, automated execution, or unattended trading.

## Existing forex work

The forex data primitives and platform-integration work already committed to this feature branch are retained as experimental groundwork. They are not the active product priority and should not drive current development decisions. Do not delete or rewrite them as part of the research pivot without a separate review.

## Definition of done for the current phase

The research foundation is ready when a user can select a publicly traded company and an as-of date, receive a well-structured multi-agent research report with inspectable source evidence, see the strongest opposing case, understand the valuation assumptions and unresolved gaps, and reproduce the run without look-ahead leakage.
