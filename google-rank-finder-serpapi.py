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
    for page in range(max_pages):
        start = page * RESULTS_PER_PAGE
        params = {
            "api_key": SERPAPI_API_KEY,
            "engine": "google",
            "q": query,
            "gl": country.lower(),
            "num": RESULTS_PER_PAGE,
            "start": start,
            "safe": "off",
        }

        response = requests.get(SERPAPI_URL, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        items = data.get("organic_results", []) or []

        if not items:
            return None

        for i, item in enumerate(items, start=1):
            link = item.get("link", "")
            if domain.lower() in link.lower():
                overall_rank = start + i
                page_number = page + 1
                return {"page": page_number, "rank": overall_rank, "url": link}

    return None

if __name__ == "__main__":
    if not SERPAPI_API_KEY:
        raise ValueError("ERROR: SERPAPI_API_KEY environment variable not set.")

    parser = argparse.ArgumentParser()
    parser.add_argument("domain")
    parser.add_argument("query")
    parser.add_argument("--country", default=DEFAULT_COUNTRY)
    parser.add_argument("--max_pages", type=int, default=DEFAULT_MAX_PAGES)
    args = parser.parse_args()

    result = find_google_search_rank(args.query, args.domain, args.country, args.max_pages)

    if result:
        print("Google Search Rank (via. SerpAPI):")
        print(f"page: {result['page']}, rank: {result['rank']}, url: {result['url']}")
    else:
        print(f"No result for {args.domain} found within first {args.max_pages} pages.")