import requests
import os
from datetime import datetime, timedelta
from dotenv import dotenv_values

BASE = "https://newsapi.org/v2/everything"

_env = dotenv_values(os.path.join(os.path.dirname(__file__), "..", ".env"))
os.environ.update(_env)


def get_news(query: str, days_back: int = 30, max_articles: int = 10) -> dict:
    """Fetch recent news articles for a given query using NewsAPI."""
    key = os.getenv("NEWS_API_KEY")
    from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    try:
        params = {
            "q": query,
            "from": from_date,
            "sortBy": "relevancy",
            "language": "en",
            "pageSize": max_articles,
            "apiKey": key,
        }
        r = requests.get(BASE, params=params, timeout=10)
        data = r.json()

        if data.get("status") != "ok":
            return {"source": "NewsAPI", "error": data.get("message", "Unknown error")}

        articles = data.get("articles", [])
        return {
            "source": "NewsAPI",
            "query": query,
            "total_results": data.get("totalResults", 0),
            "articles": [
                {
                    "title": a.get("title"),
                    "source": a.get("source", {}).get("name"),
                    "published": a.get("publishedAt", "")[:10],
                    "description": a.get("description", "")[:200],
                    "url": a.get("url"),
                }
                for a in articles
                if a.get("title") != "[Removed]"
            ],
        }
    except Exception as e:
        return {"source": "NewsAPI", "error": str(e)}
