import requests

BASE = "https://efts.sec.gov/LATEST/search-index"
HEADERS = {"User-Agent": "market-intelligence-agent alex.lechado10@gmail.com"}


def get_company_data(sector_keywords: str, max_results: int = 10) -> dict:
    """Search SEC EDGAR for companies in a given sector."""
    try:
        params = {
            "q": sector_keywords,
            "dateRange": "custom",
            "startdt": "2023-01-01",
            "enddt": "2024-12-31",
            "forms": "10-K",
        }
        r = requests.get(
            "https://efts.sec.gov/LATEST/search-index?q=%22alternative+protein%22&forms=10-K",
            headers=HEADERS,
            timeout=10,
        )

        # Use full text search
        search_url = "https://efts.sec.gov/LATEST/search-index"
        params = {"q": f'"{sector_keywords}"', "forms": "10-K", "dateRange": "custom",
                  "startdt": "2022-01-01", "enddt": "2024-12-31"}
        r = requests.get(
            "https://efts.sec.gov/LATEST/search-index",
            params={"q": sector_keywords, "forms": "10-K"},
            headers=HEADERS,
            timeout=10,
        )
        data = r.json()
        hits = data.get("hits", {}).get("hits", [])[:max_results]

        return {
            "source": "SEC EDGAR",
            "sector": sector_keywords,
            "companies": [
                {
                    "company": h.get("_source", {}).get("entity_name"),
                    "form": h.get("_source", {}).get("form_type"),
                    "date": h.get("_source", {}).get("file_date"),
                    "description": h.get("_source", {}).get("period_of_report"),
                }
                for h in hits
            ],
        }
    except Exception as e:
        return {"source": "SEC EDGAR", "error": str(e)}
