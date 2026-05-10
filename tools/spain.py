import requests

INE_BASE = "https://servicios.ine.es/wstempus/js/ES"
MAPA_BASE = "https://www.mapa.gob.es/es/estadistica/temas"


def get_spain_data(sector_keywords: str) -> dict:
    """Fetch Spanish market data from INE and related public sources."""
    results = {}

    # INE - Industrial Production Index by sector
    try:
        r = requests.get(
            f"{INE_BASE}/DATOS_SERIE/IPI251",
            params={"nult": 12},
            timeout=10,
        )
        data = r.json()
        results["ine_industrial_production"] = {
            "source": "INE",
            "series": "Industrial Production Index",
            "data": data.get("Data", [])[:12] if isinstance(data, dict) else [],
        }
    except Exception as e:
        results["ine_industrial_production"] = {"error": str(e)}

    # INE - CPI food and beverages
    try:
        r = requests.get(
            f"{INE_BASE}/DATOS_SERIE/IPC251852",
            params={"nult": 12},
            timeout=10,
        )
        data = r.json()
        results["ine_food_cpi"] = {
            "source": "INE",
            "series": "CPI Food & Beverages Spain",
            "data": data.get("Data", [])[:12] if isinstance(data, dict) else [],
        }
    except Exception as e:
        results["ine_food_cpi"] = {"error": str(e)}

    # INE - GDP Spain quarterly
    try:
        r = requests.get(
            f"{INE_BASE}/DATOS_SERIE/CNTR2010",
            params={"nult": 8},
            timeout=10,
        )
        data = r.json()
        results["ine_gdp"] = {
            "source": "INE",
            "series": "Spain GDP Quarterly",
            "data": data.get("Data", [])[:8] if isinstance(data, dict) else [],
        }
    except Exception as e:
        results["ine_gdp"] = {"error": str(e)}

    # MAPA - Agricultural statistics (public open data)
    try:
        keywords = sector_keywords.lower()
        r = requests.get(
            "https://www.mapa.gob.es/es/estadistica/temas/estadisticas-agrarias/agricultura/encuestas-superficies-producciones-cultivos/",
            timeout=10,
        )
        results["mapa"] = {
            "source": "MAPA",
            "note": f"MAPA agriculture stats for: {sector_keywords}",
            "url": "https://www.mapa.gob.es/es/estadistica/temas/estadisticas-agrarias/",
            "status": "accessible",
        }
    except Exception as e:
        results["mapa"] = {"error": str(e)}

    return {"source": "Spain Public Data (INE + MAPA)", "sector": sector_keywords, "results": results}
