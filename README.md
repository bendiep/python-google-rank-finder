# python-google-search-rank

A simple Python script that checks the `Google Search Ranking` of a given domain for a specific keyword or phrase.

It supports the following Search APIs:

- [SerpApi](https://serpapi.com) (Default)
- [Google Custom Search API](https://developers.google.com/custom-search/v1)

## 📋 Prerequisites

Depending on which Search API you choose, you’ll need one of the following:

### Option 1: SerpApi

- A SerpApi `API Key` is required (can be created [here](https://serpapi.com))

### Option 2: Google Custom Search API

- A Google Custom Search `API Key` and `Engine ID` is required (both can be created [here](https://developers.google.com/custom-search/v1/introduction))

## 📦 Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/bendiep/python-google-rank-finder.git
   cd python-google-rank-finder
   ```

2. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up your environment variables based on the Search API you plan to use:

   ```bash
   # For SerpApi
   export SERPAPI_API_KEY="your-serpapi-api-key"

   # For Google Custom Search API
   export GOOGLE_CUSTOM_SEARCH_API_KEY="your-google-custom-search-api-key"
   export GOOGLE_CUSTOM_SEARCH_ENGINE_ID="your-google-custom-search-engine-id"
   ```

## ▶️ Usage

Run the script with the following command:

```bash
python google-rank-finder.py <website_domain> <search_term>

e.g.
python google-rank-finder.py "instagram.com" "ig"
```

Optional arguments:

`--country`: Specify the country code

```bash
python google-rank-finder.py <website_domain> <search_term> --country AU
```

`--max_pages`: Set the maximum number of pages to search (default: 10).

```bash
python google-rank-finder.py <website_domain> <search_term> --max_pages 3
```

`--api`: Choose the Search API to use (`SERPAPI` or `GOOGLE_CUSTOM_SEARCH`). Default is `SERPAPI`.

```bash
python google-rank-finder.py <website_domain> <search_term> --api GOOGLE_CUSTOM_SEARCH
```

## 📂 Example Output

```text
python google-rank-finder.py "instagram.com" "ig"
Google Search Rank (via. SERPAPI):
page: 1, rank: 1, url: https://www.instagram.com/
```

## 📝 License

Released under the MIT License. Feel free to use, modify, and share!
