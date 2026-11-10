from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.analysts.turn import take_turn
from tradingagents.agents.context import get_instrument_context_from_state, get_language_instruction
from tradingagents.agents.tools import (
    get_balance_sheet,
    get_cashflow,
    get_fundamentals,
    get_income_statement,
    get_insider_transactions,
)

# The tools this analyst is offered; its tool node is built from the same tuple.
TOOLS = (
    get_fundamentals,
    get_balance_sheet,
    get_cashflow,
    get_income_statement,
    get_insider_transactions,
)


def create_fundamentals_analyst(llm):
    def fundamentals_analyst_node(state):
        current_date = state["trade_date"]
        instrument_context = get_instrument_context_from_state(state)

        system_message = (
            "You are a senior public-equity fundamental research analyst. Produce a deep, evidence-led assessment of the company as of the run date, not a short trading brief. Reconstruct the business model, revenue segments, customer and geographic exposure, unit economics where available, competitive position, management and governance, capital allocation, and material dependencies. Analyze several years of income statements, balance sheets, and cash-flow statements where available; explain growth quality, margins, returns, liquidity, leverage, dilution, working-capital trends, and cash conversion. Distinguish reported facts from management guidance, third-party estimates, and your own interpretation. Identify accounting-quality questions, inconsistencies, one-off items, and missing evidence. Use the available tools to retrieve company fundamentals, balance sheet, cash flow, income statement, and insider transactions. Do not invent numbers, peer comparisons, valuation inputs, or source details. State the period, units, currency, and as-of limitations for every important metric. This is investment research, not an instruction to place a trade."
            + " Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read."
            + " Use the available tools: `get_fundamentals` for comprehensive company analysis, `get_balance_sheet`, `get_cashflow`, and `get_income_statement` for specific financial statements, and `get_insider_transactions` for recent insider buying and selling."
            + get_language_instruction()
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " Report only what the retrieved evidence supports. Do not turn research findings into trade instructions."
                    " You have access to the following tools: {tool_names}."
                    " Today's date is {current_date}; treat it as 'now' for all analysis and tool-call date ranges. {instrument_context}\n"
                    "{system_message}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in TOOLS]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(instrument_context=instrument_context)

        result, report = take_turn(prompt, llm, TOOLS, state["messages"])

        return {
            "messages": [result],
            "fundamentals_report": report,
        }

    return fundamentals_analyst_node
