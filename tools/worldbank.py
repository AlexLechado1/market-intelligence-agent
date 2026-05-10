import requests

BASE = "https://api.worldbank.org/v2"

INDICATORS = {
    "gdp": "NY.GDP.MKTP.CD",
    "gdp_growth": "NY.GDP.MKTP.KD.ZG",
    "gdp_per_capita": "NY.GDP.PCAP.CD",
    "population": "SP.POP.TOTL",
    "inflation": "FP.CPI.TOTL.ZG",
    "fdi_inflows": "BX.KLT.DINV.CD.WD",
}

EU_COUNTRIES = "ES;FR;DE;IT;PL;NL;BE;SE;AT;DK"


def get_macro_context(countries: str = EU_COUNTRIES, years: str = "2020:2023") -> dict:
    """Fetch macroeconomic indicators from World Bank for given countries."""
    results = {}
    for name, code in INDICATORS.items():
        try:
            url = f"{BASE}/country/{countries}/indicator/{code}"
            params = {"date": years, "format": "json", "per_page": 100}
            r = requests.get(url, params=params, timeout=10)
            data = r.json()
            if isinstance(data, list) and len(data) > 1:
                results[name] = [
                    {
                        "country": item.get("country", {}).get("value"),
                        "year": item.get("date"),
                        "value": item.get("value"),
                    }
                    for item in data[1]
                    if item.get("value") is not None
                ]
        except Exception as e:
            results[name] = {"error": str(e)}

    return {"source": "World Bank", "countries": countries, "indicators": results}
