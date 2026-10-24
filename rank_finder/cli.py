"""Command-line and interactive entry points."""

import argparse
import getpass
import json
import math
import os
import sqlite3
import sys
from dataclasses import replace

from .core import SearchConfig, find_rank, normalize_domain, validate_transport
from .history import save_result
from .serpapi import SerpApiClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check a domain's highest organic Google position using SerpApi. Run without arguments for guided setup.",
        allow_abbrev=False,
    )
    parser.add_argument("domain", help="Domain or URL, for example example.com")
    parser.add_argument("query", help="Search keyword or phrase")
    parser.add_argument(
        "--country", default="us", help="Two-letter search country code; default us"
    )
    parser.add_argument(
        "--location",
        help="Search origin, preferably a city, such as 'Melbourne, Victoria, Australia'",
    )
    parser.add_argument(
        "--language", default="en", help="Search interface language code; default en"
    )
    parser.add_argument(
        "--device",
        choices=("desktop", "mobile", "tablet"),
        default="desktop",
        help="Search device; default desktop",
    )
    parser.add_argument(
        "--max-results",
        "--depth",
        type=int,
        help="Highest organic position to check, 1-1000; default 100",
    )
    parser.add_argument(
        "--max-pages",
        "--max_pages",
        type=int,
        help="Page budget, 1-100; defaults to enough ten-position pages for the requested depth",
    )
    parser.add_argument(
        "--exact-host",
        action="store_true",
        help="Match only the supplied hostname, excluding its subdomains",
    )
    parser.add_argument(
        "--fresh", action="store_true", help="Bypass SerpApi's cache, which can increase usage"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30,
        help="Timeout per HTTP request in seconds; default 30, at most 300",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=1,
        help="Retries per page for connection failures and HTTP 5xx errors; default 1, maximum 3",
    )
    parser.add_argument("--json", action="store_true", help="Write the structured result as JSON")
    parser.add_argument(
        "--history", metavar="FILE", help="Append the result to a local SQLite database"
    )
    return parser


def _prompt(label: str, default: str = "", validate=None) -> str:
    while True:
        print(
            label + (f" [{default}]" if default else "") + ": ", end="", file=sys.stderr, flush=True
        )
        value = input().strip() or default
        try:
            if validate:
                validate(value)
            return value
        except ValueError as exc:
            print(str(exc), file=sys.stderr)


def _choice(*options):
    def validate(value):
        if value.lower() not in options:
            raise ValueError("Choose " + ", ".join(options) + ".")

    return validate


def interactive_config() -> tuple[SearchConfig, str, bool, str | None]:
    print(
        "Google organic rank checker\nPress Enter to accept a default. Press Ctrl+C to cancel.\n",
        file=sys.stderr,
    )
    domain = _prompt("Website domain or URL", validate=normalize_domain)

    def validate_query(value):
        if not value:
            raise ValueError("Enter a keyword or phrase.")

    query = _prompt("Keyword or phrase", validate=validate_query)
    config = SearchConfig(domain, query)
    country = _prompt(
        "Country code, for example AU or US",
        config.country,
        lambda value: replace(config, country=value),
    )
    language = _prompt(
        "Language code", config.language, lambda value: replace(config, language=value)
    )
    location = _prompt("City or region, optional; blank lets SerpApi choose the location")
    device = _prompt(
        "Device: desktop, mobile or tablet", config.device, _choice("desktop", "mobile", "tablet")
    ).lower()

    def validate_depth(value):
        try:
            replace(config, max_results=int(value))
        except ValueError:
            raise ValueError("Enter a whole number between 1 and 1000.") from None

    depth = int(_prompt("Highest organic position to check", "100", validate_depth))
    include_subdomains = _prompt(
        "Include subdomains? yes/no", "yes", _choice("yes", "no", "y", "n")
    ).lower() in ("yes", "y")
    fresh = _prompt(
        "Bypass the cached results? yes/no", "no", _choice("yes", "no", "y", "n")
    ).lower() in ("yes", "y")
    json_output = (
        _prompt("Output format: text or json", "text", _choice("text", "json")).lower() == "json"
    )
    history = _prompt("SQLite history file, optional; blank skips saving") or None
    api_key = os.getenv("SERPAPI_API_KEY", "").strip()
    if not api_key:
        print("Get a SerpApi API key at https://serpapi.com/manage-api-key", file=sys.stderr)
    while not api_key:
        api_key = getpass.getpass("SerpApi API key, hidden and used for this run only: ").strip()
        if not api_key:
            print("An API key is required.", file=sys.stderr)
    config = replace(
        config,
        country=country,
        language=language,
        location=location,
        device=device,
        max_results=depth,
        max_pages=math.ceil(depth / 10),
        include_subdomains=include_subdomains,
        fresh=fresh,
    )
    print(
        f"\nChecking up to position {depth}, with at most {config.max_pages} pages and {config.max_pages * 2} HTTP requests including retries.",
        file=sys.stderr,
    )
    return config, api_key, json_output, history


def format_result(result) -> str:
    config = result.config
    lines = ["Google organic position via SerpApi"]
    if result.status == "found":
        lines.append(f"Position: {result.rank} | Page fetched: {result.page} | URL: {result.url}")
    elif result.status == "not_found":
        lines.append(f"No matching result for {config.domain} in the positions checked.")
    elif result.status == "incomplete":
        lines.append("Search incomplete. The full requested depth was not checked.")
    else:
        lines.append("Search failed. No ranking conclusion is available.")
    if result.error:
        lines.append("Error: " + result.error)
    lines.append(f'Keyword: "{config.query}" | Domain: {config.domain}')
    lines.append(
        f"Country: {config.country.upper()} | Language: {config.language} | Device: {config.device}"
    )
    lines.append("Requested location: " + (config.location or "provider-selected"))
    locations = list(
        dict.fromkeys(
            item["location_used"] for item in result.searches if item.get("location_used")
        )
    )
    if locations:
        lines.append("Location used: " + "; ".join(locations))
    for observation in result.searches:
        displayed = observation.get("query_displayed")
        if displayed and displayed != config.query:
            lines.append(f'Google displayed the query as: "{displayed}"')
            break
    lines.append(
        f"Checked {result.results_checked} organic results across {result.pages_checked} pages; deepest position checked: {result.deepest_rank_checked}."
    )
    lines.append(f"HTTP requests: {result.requests_made} | Stop reason: {result.stop_reason}")
    lines.append(
        f"Retrieved at: {result.checked_at} | Cache: {'bypassed' if config.fresh else 'allowed'}"
    )
    return "\n".join(lines)


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    try:
        if not argv:
            if not sys.stdin.isatty():
                parser.error(
                    "Guided setup needs a terminal. Supply a domain and keyword, or run --help."
                )
            config, api_key, json_output, history = interactive_config()
            timeout, retries = 30, 1
        else:
            args = parser.parse_args(argv)
            json_output = args.json
            try:
                depth = (
                    args.max_results
                    if args.max_results is not None
                    else (args.max_pages * 10 if args.max_pages is not None else 100)
                )
                config = SearchConfig(
                    domain=args.domain,
                    query=args.query,
                    country=args.country,
                    language=args.language,
                    location=args.location,
                    device=args.device,
                    max_results=depth,
                    max_pages=args.max_pages
                    if args.max_pages is not None
                    else math.ceil(depth / 10),
                    include_subdomains=not args.exact_host,
                    fresh=args.fresh,
                )
                validate_transport(args.timeout, args.retries)
            except ValueError as exc:
                parser.error(str(exc))
            timeout, retries, history = args.timeout, args.retries, args.history
            api_key = os.getenv("SERPAPI_API_KEY", "").strip()
            if not api_key:
                message = "Set the SERPAPI_API_KEY environment variable before searching, or run without arguments for guided setup."
                if json_output:
                    print(json.dumps({"status": "error", "error": message}))
                else:
                    print("Error: " + message, file=sys.stderr)
                return 2
        with SerpApiClient(api_key, timeout=timeout, retries=retries) as client:
            result = find_rank(config, client)
        print(
            json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
            if json_output
            else format_result(result)
        )
        exit_code = {"found": 0, "not_found": 1, "error": 2, "incomplete": 3}[result.status]
        if history:
            try:
                save_result(history, result)
            except (OSError, sqlite3.Error):
                print(
                    "Error: Could not save history. Check the database path and permissions.",
                    file=sys.stderr,
                )
                return 2
        return exit_code
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 130
    except EOFError:
        print(
            "\nInput ended before setup was complete. Supply a domain and keyword to run without prompts.",
            file=sys.stderr,
        )
        return 2
