# Google rank finder

Find a domain's highest organic Google position for a keyword or phrase using
[SerpApi](https://serpapi.com/search-api). Run it with arguments for scripts and
automation, or without arguments for a guided setup.

Each result records the search conditions, timestamp, matched URL and actual
number of results examined. A failed or incomplete search has its own status.

## Installation

You need **Python 3.10 or newer** and a [SerpApi API key](https://serpapi.com/manage-api-key).

```sh
git clone https://github.com/bendiep/python-google-rank-finder.git
cd python-google-rank-finder
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows, create the environment with `py -3 -m venv .venv` and activate it in
PowerShell with `.venv\Scripts\Activate.ps1`.

For command-line use, set your key in the environment:

```sh
export SERPAPI_API_KEY="your-serpapi-api-key"
```

In PowerShell, use `$env:SERPAPI_API_KEY = "your-serpapi-api-key"`.
Guided setup can prompt privately for a key instead. It uses that key for the
current run and does not save it.

## Guided setup

Run this in a terminal with no arguments:

```sh
python google-rank-finder.py
```

The script asks for the website, keyword, country, language, city or region,
device and search depth. It also offers exact-host matching, fresh results,
JSON output and an optional SQLite history file. Press Enter to accept a
default, or Ctrl+C to cancel. Invalid entries can be corrected at the prompt.

Defaults are US, English, desktop, subdomains included, and a maximum depth of
100. The location is provider-selected unless you supply one. For comparable
checks over time, choose the same city or region, country, language and device.
Use a precise location such as `Melbourne, Victoria, Australia`.

## Command-line usage

```sh
python google-rank-finder.py example.com "example keyword" \
  --country AU \
  --location "Melbourne, Victoria, Australia" \
  --language en \
  --device mobile \
  --max-results 100
```

Domains and full HTTP URLs are accepted. The hostname determines the match;
a path in the supplied URL does not restrict the check to that page. Checking
`example.com` includes `www.example.com` and other subdomains by default. With
`--exact-host`, only `example.com` matches. To check only `www.example.com`, supply
that hostname and `--exact-host`.

You can also run the package with `python -m rank_finder`.

| Option | Meaning | Default |
| --- | --- | --- |
| `--country` | Two-letter search country code, such as `AU` or `US` | `us` |
| `--location` | Search origin, preferably a city and region | Provider-selected |
| `--language` | Interface language, such as `en` or `en-gb` | `en` |
| `--device` | `desktop`, `mobile` or `tablet` | `desktop` |
| `--max-results`, `--depth` | Highest organic position to examine, from 1 to 1000 | `100` |
| `--max-pages`, `--max_pages` | Maximum pages to fetch, from 1 to 100 | Depth divided by 10, rounded up |
| `--exact-host` | Exclude subdomains of the supplied hostname | Subdomains included |
| `--fresh` | Bypass SerpApi's cache | Cache allowed |
| `--timeout` | Timeout per HTTP request in seconds, greater than 0 and at most 300 | `30` |
| `--retries` | Retries per page for connection failures and HTTP 500, 502, 503 or 504 | `1`, maximum `3` |
| `--json` | Output a structured JSON result | Text |
| `--history FILE` | Append the observation to a local SQLite file | Disabled |

When only `--max-pages` is supplied, the depth is ten times that page budget.
For example, the existing `--max_pages 3` usage searches up to position 30.
If both limits are supplied, the first one reached stops the search.
Run `python google-rank-finder.py --help` for help.

## What the position means

The script examines the top-level `organic_results` returned by SerpApi and
returns the first matching hostname in position order. Rank is the provider's
page-local organic position plus that page's result offset. It follows the
provider's next-page metadata rather than assuming every page contains ten
results. Results without a usable link count toward the checked positions but
cannot match a domain.

This measures an organic search snapshot under the requested conditions. It
does not measure ads, Maps listings, AI Overview citations, nested sitelinks or
pixel visibility. It is also different from Search Console's average position
across impressions. There is no universal position seen by every Google user.

The output reports the actual organic results checked and the deepest position
examined. A depth of 100 is a ceiling; Google may return fewer results or stop
pagination earlier. Reaching the page budget while more eligible pages remain
produces an `incomplete` result.

The text output identifies the location SerpApi used when available, and notes
if Google displayed a different query. The client requests no spelling correction,
but Google can still substitute a query when it has no results for the original.
Review those observations when interpreting a rank.

## JSON and exit codes

```sh
python google-rank-finder.py example.com "example keyword" --country AU --json > result.json
```

Search output on stdout is one JSON object. Interactive prompts and setup errors
use stderr. The object includes `status`, `rank`, `url`, `config`, `checked_at`,
`results_checked`, `deepest_rank_checked`, `pages_checked`, `requests_made`,
`stop_reason`, `error` and per-page `searches` metadata. API keys and pagination
URLs are excluded. `checked_at` is the UTC retrieval time; `searches[].created_at`
is the provider's search time, which can be earlier when cached results are used.

| Exit code | Meaning |
| --- | --- |
| `0` | A matching organic result was found |
| `1` | No match in the successfully checked positions |
| `2` | Invalid setup, provider failure, or failure to save requested history |
| `3` | Incomplete search due to a page limit or failure after partial progress |
| `130` | Cancelled with Ctrl+C |

Argument errors use argparse's normal stderr output, including with `--json`.
A missing API key with `--json` returns a short JSON error object. If saving
history fails, the measured result is still printed and the process exits with
code 2. Consumers should check both the exit code and result status.

## History

```sh
python google-rank-finder.py example.com "example keyword" \
  --country AU --location "Melbourne, Victoria, Australia" \
  --history ranks.sqlite3
```

The SQLite file contains an append-only `rank_checks` table with `checked_at`,
`domain`, `query`, `status`, `rank` and the complete `result_json`. Its parent
directory must already exist. Failed and incomplete searches retain their
statuses, so they need not be treated as ranking drops. API keys are not saved.

Run the same command from your own scheduler for recurring checks. Keep the
search settings consistent and inspect failures before comparing ranks.

## Request usage

The script stops after a match, the depth limit, the page limit or the end of
pagination. Each page can make at most `1 + retries` HTTP requests. With the
defaults, a lookup makes at most 20 requests across ten pages. Authentication
and quota errors are not retried. Retries use a bounded exponential delay.

For planning, 100 keywords checked daily at ten pages each is up to 30,000
requests in a 30-day month before retries, devices or additional locations.
HTTP request counts are not the same as billed searches.
[SerpApi documents an hour-long cache for identical requests](https://serpapi.com/search-api);
cached searches do not count toward the monthly search allowance. `--fresh`
bypasses that cache. Retries can also increase usage.

## Development

```sh
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m ruff format --check .
python -m unittest discover -v
```

Tests use local fixtures and mocked HTTP responses. They need no API key and
make no live searches. Fixtures follow the published SerpApi response format,
including its successful empty-result response. GitHub Actions runs the checks
on Python 3.10, 3.12 and 3.14 on Linux, plus Python 3.12 on Windows.

The implementation separates settings and matching in `rank_finder/core.py`,
HTTP and response parsing in `rank_finder/serpapi.py`, the terminal interface in
`rank_finder/cli.py`, and optional persistence in `rank_finder/history.py`.

## License

[MIT](LICENSE).
