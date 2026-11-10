"""Research Manager: synthesizes the bull/bear debate into an evidence-weighted equity research assessment."""

from __future__ import annotations

from tradingagents.agents.context import get_instrument_context_from_state, get_language_instruction
from tradingagents.agents.schemas import ResearchPlan, render_research_plan
from tradingagents.agents.structured import (
    NO_EXTERNAL_TOOLS,
    bind_structured,
    invoke_structured_or_freetext,
)


def create_research_manager(llm):
    structured_llm = bind_structured(llm, ResearchPlan, "Research Manager")

    def research_manager_node(state) -> dict:
        instrument_context = get_instrument_context_from_state(state)
        history = state["investment_debate_state"].get("history", "")

        investment_debate_state = state["investment_debate_state"]

        prompt = f"""As the Research Manager, synthesize the debate into a balanced, decision-useful equity research assessment. This is a research conclusion, not a trading instruction. Evaluate the business and the evidence, not a hypothetical portfolio or a trade setup.

{instrument_context}

---

**Rating Scale** (use exactly one):
- **Buy**: The evidence supports a strongly attractive long-term business and investment thesis; this is an analytical rating, not an order
- **Overweight**: The thesis is constructive, with identifiable but manageable uncertainties
- **Hold**: Evidence is mixed, valuation-sensitive, or insufficient for a stronger conclusion
- **Underweight**: Material concerns weaken the thesis or make the risk/reward unattractive
- **Sell**: The evidence indicates a structurally weak or materially impaired thesis

Do not confuse confidence with certainty. Weigh the strongest bull and bear evidence independently of speaking order. Separate business quality from valuation: an excellent company can be an unattractive investment at an excessive price. Identify the key assumptions behind the conclusion, the evidence gaps, the most important thesis breakers, and the facts that would change the rating. If the evidence is too thin, say so rather than manufacturing conviction. Do not invent valuation data or financial metrics.

---

**Debate History:**
{history}

## Output

Write these sections, in this order, starting with the recommendation on its own line:

- **Recommendation**: exactly one of Buy / Overweight / Hold / Underweight / Sell
- **Rationale**: which arguments decided it
- **Strategic Actions**: prioritized next research steps, diligence questions, monitoring items, and evidence needed to confirm or invalidate the thesis. Do not provide trade execution, entry, stop, or position-sizing instructions.

{NO_EXTERNAL_TOOLS}""" + get_language_instruction()

        investment_plan = invoke_structured_or_freetext(
            structured_llm,
            llm,
            prompt,
            render_research_plan,
            "Research Manager",
        )

        new_investment_debate_state = {
            "history": investment_debate_state.get("history", ""),
            "bear_history": investment_debate_state.get("bear_history", ""),
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": investment_plan,
            "count": investment_debate_state["count"],
        }

        return {
            "investment_debate_state": new_investment_debate_state,
            "investment_plan": investment_plan,
        }

    return research_manager_node
