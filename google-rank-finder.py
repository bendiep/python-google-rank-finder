import os
import argparse
import requests

GOOGLE_CUSTOM_SEARCH_BASE_URL = "https://www.googleapis.com/customsearch/v1"
GOOGLE_CUSTOM_SEARCH_API_KEY = os.getenv("GOOGLE_CUSTOM_SEARCH_API_KEY")
GOOGLE_CUSTOM_SEARCH_ENGINE_ID = os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID")

DEFAULT_COUNTRY = ""
DEFAULT_MAX_PAGES = 10
DEFAULT_RESULTS_PER_PAGE = 10
DEFAULT_TIMEOUT = 20

def find_google_search_rank(query, domain, country, max_pages):
    for page in range(max_pages):
        start = page * DEFAULT_RESULTS_PER_PAGE + 1
        params = {
            "key": GOOGLE_CUSTOM_SEARCH_API_KEY,
            "cx": GOOGLE_CUSTOM_SEARCH_ENGINE_ID,
            "q": query,
            "gl": country.lower(),
            "cr": "country:" + country.upper(),
            "num": DEFAULT_RESULTS_PER_PAGE,
            "start": start,
            "safe": "off",
        }

        response = requests.get(GOOGLE_CUSTOM_SEARCH_BASE_URL, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        items = data.get("items", [])

        if not items:
            return None

        for i, item in enumerate(items, start=1):
            link = item.get("link", "")
            if domain.lower() in link.lower():
                overall_rank = (page * DEFAULT_RESULTS_PER_PAGE) + i
                page_number = page + 1
                return {"page": page_number, "rank": overall_rank, "url": link}

    return None

if __name__ == "__main__":
    if not GOOGLE_CUSTOM_SEARCH_API_KEY:
        raise ValueError("ERROR: GOOGLE_CUSTOM_SEARCH_API_KEY environment variable not set.")
    if not GOOGLE_CUSTOM_SEARCH_ENGINE_ID:
        raise ValueError("ERROR: GOOGLE_CUSTOM_SEARCH_ENGINE_ID environment variable not set.")

    parser = argparse.ArgumentParser()
    parser.add_argument("domain")
    parser.add_argument("query")
    parser.add_argument("--country", default=DEFAULT_COUNTRY)
    parser.add_argument("--max_pages", type=int, default=DEFAULT_MAX_PAGES)
    args = parser.parse_args()

    res = find_google_search_rank(args.query, args.domain, args.country, args.max_pages)

    if res:
        print("Google Search Rank:")
        print(f"page: {res['page']}, rank: {res['rank']}, url: {res['url']}")
    else:
        print(f"No result for {args.domain} found within first {args.max_pages} pages.")
