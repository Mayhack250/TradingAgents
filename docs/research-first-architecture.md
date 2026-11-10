# Research-first investment intelligence

## Product direction

This fork is being developed as a research and decision-support system, not an autonomous trading bot. Its first-class output is a source-backed research dossier that helps a person understand an asset, test an investment thesis, identify uncertainty, and decide what deserves further study.

The initial asset focus is listed equities. The architecture should remain extensible to ETFs, indices, FX, and other asset classes without treating their data or valuation methods as interchangeable.

## Current scope

### In scope now

- Company and security identity: legal issuer, ticker, exchange, share class, currency, reporting jurisdiction, and fiscal year-end.
- Business model, products, customers, geography, industry structure, and competitive positioning.
- Financial statements: income statement, balance sheet, cash flow, margins, returns, leverage, liquidity, dilution, and capital allocation.
- Valuation with explicit assumptions and multiple methods where appropriate; distinguish enterprise value from equity value.
- Management quality, governance, insider activity, ownership, and material risks.
- Macro, rates, regulation, industry catalysts, earnings, and relevant geopolitical exposure.
- Bull, base, and bear cases with explicit drivers, assumptions, disconfirming evidence, and scenario sensitivities.
- Source provenance, publication dates, retrieval timestamps, point-in-time eligibility, missing-data flags, and conflicting evidence.
- A final research memo that separates facts, estimates, interpretations, and open questions.

### Explicitly deferred

- Virtual/paper portfolio balances, holdings, transactions, performance attribution, and benchmark tracking.
- Broker connectivity, order routing, automated execution, and trade approvals.
- Public-facing dashboards or hosted webhook infrastructure.

The later virtual portfolio should consume reviewed research outputs, but it must be a separate layer. It must not alter research conclusions to justify an existing holding.

## Research workflow

1. Resolve the instrument. Confirm legal issuer, security class, exchange, ticker, trading currency, fiscal year-end, and reporting standards. Never rely on ticker alone.
2. Set the information cutoff. Every run has an explicit as-of date. Evidence published after that date is excluded from the contemporaneous thesis, even if useful for a clearly labelled hindsight review.
3. Collect primary evidence first. Prefer regulatory filings, audited reports, earnings releases, official company materials, exchange notices, central-bank/statistical releases, and regulator records. Use reputable secondary research for context and independent challenge.
4. Normalize and reconcile. Preserve units, currencies, fiscal periods, accounting basis, restatements, share counts, and source vintages. Do not silently combine incompatible figures.
5. Analyze the business and financials. Explain drivers behind the numbers, not just ratios. Separate recurring operations from one-offs and accounting effects.
6. Value the security. State method, inputs, date, assumptions, sensitivity, and limitations. Do not output a target price if inputs cannot support one.
7. Challenge the thesis. Require a bear case, alternative explanations, disconfirming indicators, and what would change the conclusion.
8. Write the dossier. Give a concise conclusion followed by inspectable evidence, calculations, risks, uncertainty, and questions requiring human judgment.

## Required dossier sections

- Executive summary and research date
- Instrument and issuer identity
- Business model and industry map
- Competitive advantages and vulnerabilities
- Historical financial analysis
- Balance-sheet and cash-flow quality
- Management, governance, ownership, and capital allocation
- Industry and macro environment
- Valuation and scenario analysis
- Bull/base/bear thesis
- Risks, catalysts, and thesis invalidation conditions
- Evidence register and source limitations
- Questions to investigate next

## Evidence and data rules

- A source's retrieval date is not its publication date. Record both.
- For historical research, use only information demonstrably available by the selected cutoff. A later restatement must not overwrite what investors knew earlier.
- Distinguish filing period end, filing/publication date, and data retrieval time.
- Label estimates, management guidance, consensus figures, and model-derived calculations separately.
- Preserve original currency, units, fiscal period, and accounting standard.
- Missing evidence is a visible limitation, not permission to infer a value.
- Conflicting sources remain visible until reconciled; do not silently choose the convenient number.
- Every material factual claim in the final memo should be traceable to evidence records.
- Avoid false precision: valuation ranges and sensitivity analysis are preferable to unsupported point estimates.

## Source hierarchy

1. Regulatory filings and audited financial statements.
2. Official earnings releases, investor presentations, and company disclosures.
3. Official exchange, regulator, central-bank, and national-statistics sources.
4. Industry bodies and well-documented datasets.
5. Reputable independent reporting and research.
6. Social media, forums, and unverified commentary, used only as attributed sentiment or leads for verification.

The hierarchy is a starting point, not a substitute for evaluating relevance, independence, incentives, accounting comparability, and source quality.

## Existing framework components to reuse

The upstream TradingAgents framework already has fundamentals, news, market, and sentiment analysts; bull/bear research; a research manager; risk analysis; point-in-time SEC EDGAR and FRED data paths; and report generation. Extend these deliberately rather than duplicating them.

SEC EDGAR company-facts data is useful for US issuer filings, while FRED supplies macroeconomic series. Neither source alone is a complete global equity research dataset. Non-US issuers require jurisdiction-specific filing sources and explicit coverage flags.

## Quality gates before a dossier is considered complete

- Instrument identity is unambiguous.
- Information cutoff is explicit.
- Material claims have traceable sources.
- Filing/publication dates are not confused with fiscal period dates.
- Key financial figures reconcile to filings or are labelled unavailable.
- Valuation assumptions and sensitivities are inspectable.
- Bull and bear cases both address the strongest opposing evidence.
- Conflicts, missing values, and stale data are disclosed.
- The memo distinguishes evidence from interpretation and is not represented as personalized financial advice.

## Future virtual portfolio boundary

When introduced, the virtual portfolio should be a separate simulation service with its own ledger, cash accounting, corporate-action handling, transaction costs, benchmark, and performance methodology. It should support paper transactions only and never share code paths with live broker order routing by default.
