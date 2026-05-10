import os
import json
from dotenv import dotenv_values
import anthropic

from tools.faostat import get_market_size, get_trade_flows
from tools.worldbank import get_macro_context
from tools.edgar import get_company_data
from tools.alpha_vantage import get_stock_data, search_tickers
from tools.spain import get_spain_data
from tools.news import get_news
from output.generator_md import generate_markdown
from output.generator_ppt import generate_pptx

_env = dotenv_values(os.path.join(os.path.dirname(__file__), ".env"))
os.environ.update(_env)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ─── TOOL DEFINITIONS ─────────────────────────────────────────────────────────
TOOLS = [
    {
        "name": "get_market_size",
        "description": "Fetch agricultural/food production and market size data from FAOSTAT for a given sector and region. Use for TAM estimation and production trends.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sector_keywords": {"type": "string", "description": "Comma-separated keywords e.g. 'soy, protein, legumes'"},
                "countries": {"type": "string", "description": "Region or countries e.g. 'Europe', 'Spain'", "default": "Europe"},
            },
            "required": ["sector_keywords"],
        },
    },
    {
        "name": "get_trade_flows",
        "description": "Fetch import/export trade flow data from FAOSTAT for a given sector.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sector_keywords": {"type": "string", "description": "Comma-separated keywords e.g. 'plant protein, soy'"},
            },
            "required": ["sector_keywords"],
        },
    },
    {
        "name": "get_macro_context",
        "description": "Fetch macroeconomic indicators (GDP, population, inflation, FDI) from World Bank for European countries.",
        "input_schema": {
            "type": "object",
            "properties": {
                "countries": {"type": "string", "description": "Semicolon-separated ISO2 codes e.g. 'ES;FR;DE;IT'", "default": "ES;FR;DE;IT;NL"},
                "years": {"type": "string", "description": "Year range e.g. '2020:2023'", "default": "2020:2023"},
            },
        },
    },
    {
        "name": "get_company_data",
        "description": "Search SEC EDGAR for public companies in a given sector. Returns company names, recent filings, and financial period data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sector_keywords": {"type": "string", "description": "Keywords to search e.g. 'alternative protein food tech'"},
                "max_results": {"type": "integer", "description": "Max companies to return", "default": 8},
            },
            "required": ["sector_keywords"],
        },
    },
    {
        "name": "search_tickers",
        "description": "Search for stock ticker symbols for companies in the sector.",
        "input_schema": {
            "type": "object",
            "properties": {
                "keywords": {"type": "string", "description": "Company or sector keywords e.g. 'Beyond Meat plant protein'"},
            },
            "required": ["keywords"],
        },
    },
    {
        "name": "get_stock_data",
        "description": "Fetch financial data for specific stock tickers: market cap, P/E ratio, revenue, EBITDA, profit margin.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbols": {"type": "string", "description": "Comma-separated ticker symbols e.g. 'BYND,TSN,OTLY'"},
            },
            "required": ["symbols"],
        },
    },
    {
        "name": "get_spain_data",
        "description": "Fetch Spanish market data from INE (industrial production, CPI, GDP) and MAPA (agriculture statistics).",
        "input_schema": {
            "type": "object",
            "properties": {
                "sector_keywords": {"type": "string", "description": "Sector keywords for context e.g. 'food, agri, protein'"},
            },
            "required": ["sector_keywords"],
        },
    },
    {
        "name": "get_news",
        "description": "Fetch recent news articles about the sector from NewsAPI. Use for M&A activity, trends, and competitive intelligence.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query e.g. 'alternative protein Europe M&A 2024'"},
                "days_back": {"type": "integer", "description": "How many days back to search", "default": 30},
                "max_articles": {"type": "integer", "description": "Max articles to return", "default": 10},
            },
            "required": ["query"],
        },
    },
]

TOOL_MAP = {
    "get_market_size": get_market_size,
    "get_trade_flows": get_trade_flows,
    "get_macro_context": get_macro_context,
    "get_company_data": get_company_data,
    "search_tickers": search_tickers,
    "get_stock_data": get_stock_data,
    "get_spain_data": get_spain_data,
    "get_news": get_news,
}

SYSTEM_PROMPT = """You are a senior strategy consultant and market intelligence analyst.
Your job is to produce a comprehensive market analysis report based on a client brief.

You have access to real-time data tools. Use them strategically:
1. Start with news to understand current landscape and M&A activity
2. Use FAOSTAT/trade data for production and market size
3. Use World Bank for macro context
4. Search for tickers, then get stock data for key players
5. Use Spain data if the brief mentions Spain or Iberian market
6. Use news again if you need more context on specific companies or deals

Structure your final analysis in these sections:
## Executive Summary
## Market Sizing (TAM, growth rate, key geographies)
## Key Players & M&A Landscape
## Go-To-Market Strategy
## Strategic Recommendation

Be specific with numbers. Cite your data sources. Write like a McKinsey consultant.
Output in English."""


def run_agent(brief: str) -> tuple[str, dict]:
    """Run the market intelligence agent with agentic tool use loop."""
    print(f"\n{'='*60}")
    print(f"BRIEF: {brief}")
    print(f"{'='*60}\n")

    messages = [{"role": "user", "content": brief}]
    raw_data = {}

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        print(f"[Agent] Stop reason: {response.stop_reason}")

        # Collect tool calls
        tool_uses = [b for b in response.content if b.type == "tool_use"]

        if not tool_uses:
            # No more tools — extract final text
            final_text = " ".join(
                b.text for b in response.content if hasattr(b, "text")
            )
            return final_text, raw_data

        # Execute all tool calls
        tool_results = []
        for tool_use in tool_uses:
            name = tool_use.name
            inputs = tool_use.input
            print(f"[Tool] {name}({json.dumps(inputs, ensure_ascii=False)[:80]}...)")

            fn = TOOL_MAP.get(name)
            if fn:
                result = fn(**inputs)
                raw_data[name] = result
                print(f"       → {str(result)[:100]}...")
            else:
                result = {"error": f"Unknown tool: {name}"}

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

        # Add assistant response + tool results to messages
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})


def analyze(brief: str):
    """Main entry point: run agent, generate Markdown and PPT."""
    analysis, raw_data = run_agent(brief)

    md_path  = generate_markdown(brief, analysis, raw_data)
    ppt_path = generate_pptx(brief, analysis)

    print(f"\n{'='*60}")
    print(f"DONE")
    print(f"  Markdown : {md_path}")
    print(f"  PowerPoint: {ppt_path}")
    print(f"{'='*60}")
    return md_path, ppt_path


if __name__ == "__main__":
    import sys
    brief = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else (
        "Analyze the alternative protein market in Europe — "
        "market sizing, key players, M&A activity, and GTM strategy for a new entrant"
    )
    analyze(brief)
