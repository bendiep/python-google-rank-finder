# python-google-search-rank

A simple Python script that checks the Google search ranking of a given domain for a specific keyword or phrase.
<br><br>
It uses [Custom Search API](https://developers.google.com/custom-search/v1) from Google to perform the search and fetch the results.

## 📋 Prerequisites

1. A Google Custom Search `API Key` and `Engine ID` (both can be created [here](https://developers.google.com/custom-search/v1/introduction))

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

3. Set up your environment variables:

   ```bash
   export GOOGLE_CUSTOM_SEARCH_API_KEY="your_api_key"
   export GOOGLE_CUSTOM_SEARCH_ENGINE_ID="your_engine_id"
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

## 📂 Example Output

```text
python google-rank-finder.py "instagram.com" "ig"
Google Search Rank:
page: 1, rank: 1, url: https://www.instagram.com/
```

## 📝 License

Released under the MIT License. Feel free to use, modify, and share!
