import os
import argparse
import requests

SERPAPI_URL = "https://serpapi.com/search.json"
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

DEFAULT_COUNTRY = ""
DEFAULT_MAX_PAGES = 10
RESULTS_PER_PAGE = 10
DEFAULT_TIMEOUT = 20

def find_google_search_rank(query, domain, country, max_pages):
    """
    Returns {"page": int, "rank": int, "url": str} if found; otherwise None.
    """
    # SerpAPI uses 0-based 'start' offsets: 0, 10, 20...
    for page_idx in range(max_pages):
        start = page_idx * RESULTS_PER_PAGE

        params = {
            "engine": "google",
            "q": query,
            "api_key": SERPAPI_API_KEY,
            "num": RESULTS_PER_PAGE,
            "start": start,
            # Localization: 'gl' for country; 'hl' for UI language (optional).
            # You can also specify google_domain (e.g., google.com.au) if you want.
            "gl": country.lower() if country else None,
            # "google_domain": "google.com.au" if country.lower() == "au" else "google.com",
            # "hl": "en",
            # SafeSearch isn't a direct flag in SerpAPI like CSE; omit or use 'safe=active' via tbs if needed.
        }

        # Remove None values so the request is clean
        params = {k: v for k, v in params.items() if v is not None}

        resp = requests.get(SERPAPI_URL, params=params, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        organic = data.get("organic_results", []) or []

        # If no organic results are returned for this page, stop early
        if not organic:
            return None

        # SerpAPI's items have 'link' and often 'position' (absolute overall rank)
        for i, item in enumerate(organic, start=1):
            link = item.get("link", "") or ""
            if domain.lower() in link.lower():
                # overall rank = (results before this page) + in-page index
                overall_rank = start + i
                page_number = page_idx + 1
                return {"page": page_number, "rank": overall_rank, "url": link}

    return None

if __name__ == "__main__":
    if not SERPAPI_API_KEY:
        raise ValueError("ERROR: SERPAPI_API_KEY environment variable not set.")

    parser = argparse.ArgumentParser()
    parser.add_argument("domain", help="Domain substring to match (e.g., example.com)")
    parser.add_argument("query", help="Google query")
    parser.add_argument("--country", default=DEFAULT_COUNTRY, help="ISO country code like 'au', 'us'")
    parser.add_argument("--max_pages", type=int, default=DEFAULT_MAX_PAGES)
    args = parser.parse_args()

    res = find_google_search_rank(args.query, args.domain, args.country, args.max_pages)

    if res:
        print("Google Search Rank (SerpAPI):")
        print(f"page: {res['page']}, rank: {res['rank']}, url: {res['url']}")
    else:
        print(f"No result for {args.domain} found within first {args.max_pages} pages.")