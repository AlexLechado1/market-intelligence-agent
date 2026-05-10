# Market Intelligence Agent

An autonomous AI agent that generates Strategy&-grade market intelligence reports from a single natural language brief. It orchestrates 10+ real-time data sources, synthesizes findings using Claude (Anthropic), and delivers a structured analysis in both Markdown and PowerPoint format.

Built to demonstrate that many consulting project tasks (example: commercial due diligence, market entry projects, GTM strategy, etc.) can be optimized
---

## What it does

You give it a brief:
```
"Analyze the alternative protein market in Europe — market sizing, key players, 
M&A activity, and GTM strategy for a new entrant"
```

The agent autonomously:
1. Pulls **recent news** on sector trends, deals, and competitive moves (NewsAPI)
2. Fetches **macroeconomic context** across 6 European markets (World Bank API)
3. Searches **public company filings** for sector players (SEC EDGAR)
4. Retrieves **stock data and financials** for listed comparables (Alpha Vantage)
5. Pulls **Spanish market data** — industrial production, CPI, GDP (INE + MAPA)
6. Queries **agricultural production and trade flows** (FAOSTAT)
7. **Synthesizes everything** into a structured report using Claude as the reasoning layer

Output: a `report.md` with full analysis + a `report.pptx` with strategy& consulting-style slides templates.

---

## Example output

```
## Executive Summary

The European alternative protein market stands at a critical inflection point. 
After a peak-hype cycle driven by VC enthusiasm (2019–2022), the sector is now 
entering a consolidation phase — characterized by cost rationalization and the 
emergence of a second-generation competitive landscape.

TAM: €6.8B (2023) → €17.4B (2030) at ~12–14% CAGR
Key signal: Beyond Meat's 97% market cap collapse opens M&A window at 
distressed multiples for strategic buyers in 2025–2027.

Strategic imperatives:
1. Compete on science, not storytelling
2. Follow regulation (EU Farm-to-Fork), not just demand  
3. Win B2B before B2C — ingredient supply margins 40–60% vs 25–35% finished goods

## Market Sizing
[World Bank data: DE €4.56T, FR €3.06T, ES €1.62T GDP | Spain +2.5% growth, 
lowest inflation in group at 3.5% → priority underpenetrated market]

## Key Players & M&A
Beyond Meat (BYND): $429M mkt cap, $265M revenue, -$135M EBITDA
JBS → Vivera: €341M (2021) | Monde Nissin → Quorn: £550M
DSM-Firmenich merger (~€19B): targets ingredient layer where margins are 3-5x higher

## GTM Strategy
Phase 1 (0–18m): B2B ingredient beachhead — Netherlands/Germany HQ
Phase 2 (12–36m): Foodservice + Mercadona private label (Spain, 27% grocery share)
Phase 3 (30–60m): Branded consumer launch, protein-forward positioning
```

---

## Why I built this

At Strategy& (PwC) I spent three years producing exactly this kind of analysis manually — pulling data from Bloomberg, Euromonitor, and internal databases, then synthesizing into client deliverables. A senior analyst spends 60–70% of their time on data gathering and formatting, not on the actual strategic thinking.

This agent compresses that data-gathering layer from days to minutes, letting the analyst focus on judgment and recommendations. That's the value proposition of AI deployment in professional services — and this project is a working proof of concept.

The architecture maps directly to real enterprise AI deployments:
- **Tool use / function calling** → how production AI agents interact with enterprise data systems
- **Multi-source data orchestration** → the core challenge in deploying AI on top of fragmented corporate data
- **Structured output** → making AI-generated content usable in professional workflows

---

## Architecture

```
User brief (natural language)
         │
         ▼
  Claude (claude-sonnet-4-6)
  Orchestrator + Synthesizer
         │
    Tool use loop
    ┌────┴────────────────────────────────────────┐
    │                                             │
    ├── get_news()          → NewsAPI             │
    ├── get_macro_context() → World Bank API      │
    ├── get_company_data()  → SEC EDGAR           │
    ├── search_tickers()    → Alpha Vantage       │
    ├── get_stock_data()    → Alpha Vantage       │
    ├── get_spain_data()    → INE + MAPA          │
    └── get_market_size()   → FAOSTAT             │
         │                                        │
         └────────────────────────────────────────┘
         │
         ▼
  Claude synthesizes all tool results
  into structured analysis
         │
    ┌────┴────────┐
    ▼             ▼
report.md     report.pptx
(Markdown)    (PowerPoint)
```

**Key design decisions:**

**Agentic loop, not a pipeline** — Claude decides which tools to call, in what order, and how many times. If the first news query returns no results, it reformulates the query and tries again. This mirrors how a real analyst would work, not a rigid ETL pipeline.

**Tool use for data, Claude for judgment** — The tools only fetch and format raw data. All synthesis, interpretation, and strategic framing is done by Claude. This separation makes it easy to swap data sources without touching the reasoning layer.

**7 public APIs, zero proprietary data** — Every data source is either free or has a free tier. The architecture would work identically with enterprise sources (Bloomberg, Capital IQ, Euromonitor) by swapping the tool implementations — the orchestration layer doesn't change.

---

## Stack

| Layer | Technology |
|---|---|
| LLM / Orchestrator | Anthropic Claude (claude-sonnet-4-6) |
| Agent framework | Anthropic Python SDK — native tool use |
| Market data | FAOSTAT, World Bank, SEC EDGAR |
| Financial data | Alpha Vantage (free tier) |
| News | NewsAPI (free tier) |
| Spain data | INE API, MAPA open data |
| PPT generation | python-pptx |
| Config | python-dotenv |

---

## How to run it

**Prerequisites:** Python 3.10+, a free NewsAPI key, a free Alpha Vantage key

```bash
git clone https://github.com/AlexLechado1/market-intelligence-agent
cd market-intelligence-agent
pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys in .env
```

**Run with default brief:**
```bash
python main.py
```

**Run with custom brief:**
```bash
python main.py "Analyze the cybersecurity market in Southern Europe for a US company planning market entry"
```

**Output files:**
```
output/report.md    ← Full analysis in Markdown
output/report.pptx  ← 6-slide PowerPoint deck
```

**Getting free API keys:**
- NewsAPI: [newsapi.org/register](https://newsapi.org/register) — instant, free tier: 100 req/day
- Alpha Vantage: [alphavantage.co](https://www.alphavantage.co/support/#api-key) — instant, free tier: 25 req/day

All other APIs (FAOSTAT, World Bank, SEC EDGAR, INE, MAPA) require no key.

---

## How the agentic loop works

The agent runs a `while True` loop that continues until Claude stops requesting tool calls:

```python
while True:
    response = claude.messages.create(
        model="claude-sonnet-4-6",
        tools=TOOLS,
        messages=messages
    )
    
    if response.stop_reason != "tool_use":
        # Claude is done — extract final analysis
        return final_text, raw_data
    
    # Execute all tool calls Claude requested
    for tool_use in response.content:
        result = TOOL_MAP[tool_use.name](**tool_use.input)
        raw_data[tool_use.name] = result
    
    # Feed results back to Claude
    messages.append({"role": "assistant", "content": response.content})
    messages.append({"role": "user", "content": tool_results})
```

In practice, the agent runs 3–5 rounds of tool calls before synthesizing — typically: news → macro + company data → financial details → final synthesis.

---

## Roadmap (V2)

- [ ] PPT template engine — use custom corporate templates instead of generated slides
- [ ] FAOSTAT retry logic — handle timeouts with exponential backoff
- [ ] Eurostat COMEXT integration — trade flow data by HS code
- [ ] Streaming output — show analysis as it's generated
- [ ] Web UI — simple Streamlit interface for non-technical users
- [ ] Enterprise data source adapters — Capital IQ, Euromonitor, Bloomberg (drop-in replacements for free APIs)
- [ ] Competitive benchmarking — compare multiple companies side by side
- [ ] Export to Google Slides via API

---

## Relation to enterprise AI deployment

This project is a simplified version of what enterprise AI deployment looks like in practice. The patterns here — tool use, multi-source orchestration, structured output, agentic loops — are the same patterns used in production deployments at companies like Palantir (AIP), ElevenLabs (enterprise voice agents), and HappyRobot (logistics AI agents).

The main differences in a production deployment would be:
- **Authentication**: OAuth/SSO instead of API keys
- **Data sources**: Enterprise databases instead of public APIs
- **Output**: Integration into existing workflows (CRM, ERP, SharePoint) instead of local files
- **Monitoring**: Logging, cost tracking, hallucination detection
- **Security**: Data residency, PII handling, audit trails

The core architecture — LLM as orchestrator, tools as data interfaces, structured synthesis — remains identical.
