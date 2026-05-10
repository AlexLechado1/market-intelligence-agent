import requests

BASE = "https://fenixservices.fao.org/faostat/api/v1/en"

def get_market_size(sector_keywords: str, countries: str = "Europe") -> dict:
    """Fetch production and trade data from FAOSTAT for a given sector."""
    try:
        # Get available datasets
        r = requests.get(f"{BASE}/datasets", timeout=10)
        datasets = r.json().get("data", [])

        # Try to get production data (dataset QCL - Crops and livestock products)
        params = {
            "area": "5706",  # Europe aggregate
            "element": "5510",  # Production
            "year": "2020,2021,2022,2023",
            "show_flags": "false",
            "null_values": "false",
        }
        r = requests.get(f"{BASE}/data/QCL", params=params, timeout=15)
        data = r.json().get("data", [])

        # Filter by keyword relevance
        keywords = [k.lower().strip() for k in sector_keywords.split(",")]
        filtered = [
            row for row in data
            if any(kw in row.get("Item", "").lower() for kw in keywords)
        ][:20]

        if not filtered:
            return {"source": "FAOSTAT", "note": f"No data found for keywords: {sector_keywords}", "data": []}

        return {
            "source": "FAOSTAT",
            "sector": sector_keywords,
            "region": countries,
            "data": [
                {
                    "item": row.get("Item"),
                    "area": row.get("Area"),
                    "year": row.get("Year"),
                    "value": row.get("Value"),
                    "unit": row.get("Unit"),
                }
                for row in filtered
            ],
        }
    except Exception as e:
        return {"source": "FAOSTAT", "error": str(e)}


def get_trade_flows(sector_keywords: str) -> dict:
    """Fetch import/export trade data from FAOSTAT."""
    try:
        keywords = [k.lower().strip() for k in sector_keywords.split(",")]
        params = {
            "area": "5706",
            "element": "5610,5910",  # Import/Export quantity
            "year": "2021,2022,2023",
            "null_values": "false",
        }
        r = requests.get(f"{BASE}/data/TCL", params=params, timeout=15)
        data = r.json().get("data", [])

        filtered = [
            row for row in data
            if any(kw in row.get("Item", "").lower() for kw in keywords)
        ][:20]

        return {
            "source": "FAOSTAT Trade",
            "sector": sector_keywords,
            "data": [
                {
                    "item": row.get("Item"),
                    "area": row.get("Area"),
                    "element": row.get("Element"),
                    "year": row.get("Year"),
                    "value": row.get("Value"),
                    "unit": row.get("Unit"),
                }
                for row in filtered
            ],
        }
    except Exception as e:
        return {"source": "FAOSTAT Trade", "error": str(e)}
