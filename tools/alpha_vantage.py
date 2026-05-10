import requests
import os
from dotenv import dotenv_values

BASE = "https://www.alphavantage.co/query"

_env = dotenv_values(os.path.join(os.path.dirname(__file__), "..", ".env"))
os.environ.update(_env)


def get_stock_data(symbols: str) -> dict:
    """Fetch stock overview and financials for given ticker symbols."""
    key = os.getenv("ALPHA_VANTAGE_KEY")
    results = []

    for symbol in [s.strip() for s in symbols.split(",")][:5]:
        try:
            r = requests.get(BASE, params={"function": "OVERVIEW", "symbol": symbol, "apikey": key}, timeout=10)
            data = r.json()
            if "Symbol" in data:
                results.append({
                    "symbol": data.get("Symbol"),
                    "name": data.get("Name"),
                    "sector": data.get("Sector"),
                    "industry": data.get("Industry"),
                    "market_cap": data.get("MarketCapitalization"),
                    "pe_ratio": data.get("PERatio"),
                    "revenue_ttm": data.get("RevenueTTM"),
                    "ebitda": data.get("EBITDA"),
                    "profit_margin": data.get("ProfitMargin"),
                    "52w_high": data.get("52WeekHigh"),
                    "52w_low": data.get("52WeekLow"),
                    "description": data.get("Description", "")[:300],
                })
            else:
                results.append({"symbol": symbol, "error": data.get("Note") or data.get("Information") or "No data"})
        except Exception as e:
            results.append({"symbol": symbol, "error": str(e)})

    return {"source": "Alpha Vantage", "stocks": results}


def search_tickers(keywords: str) -> dict:
    """Search for ticker symbols matching keywords."""
    key = os.getenv("ALPHA_VANTAGE_KEY")
    try:
        r = requests.get(BASE, params={"function": "SYMBOL_SEARCH", "keywords": keywords, "apikey": key}, timeout=10)
        data = r.json()
        matches = data.get("bestMatches", [])[:8]
        return {
            "source": "Alpha Vantage Search",
            "query": keywords,
            "tickers": [
                {
                    "symbol": m.get("1. symbol"),
                    "name": m.get("2. name"),
                    "type": m.get("3. type"),
                    "region": m.get("4. region"),
                }
                for m in matches
            ],
        }
    except Exception as e:
        return {"source": "Alpha Vantage Search", "error": str(e)}
