"""Terminal presentation. Redirected output remains plain text."""

import os
import shutil
import sys
import textwrap
from datetime import datetime

from .core import RankResult


def style(text: str, code: str, *, stream=None) -> str:
    stream = sys.stdout if stream is None else stream
    if not stream.isatty() or "NO_COLOR" in os.environ or os.getenv("TERM") == "dumb":
        return text
    return f"\033[{code}m{text}\033[0m"


def banner(subtitle: str, *, stream=None) -> str:
    width = min(shutil.get_terminal_size((80, 24)).columns - 4, 64)
    return "\n".join(
        [
            "",
            style("  Google rank finder", "1;36", stream=stream),
            style("  " + subtitle, "2", stream=stream),
            style("  " + "-" * max(20, width), "2", stream=stream),
        ]
    )


def section(title: str, *, stream=None) -> str:
    return "\n" + style("  " + title, "1;36", stream=stream)


def _row(label: str, value: str) -> list[str]:
    prefix = f"    {label:<16}  "
    width = max(20, min(shutil.get_terminal_size((80, 24)).columns, 100) - len(prefix))
    values = textwrap.wrap(value, width=width, break_long_words=False, break_on_hyphens=False) or [
        ""
    ]
    return [style(prefix, "2") + values[0], *(" " * len(prefix) + part for part in values[1:])]


def format_result(result: RankResult) -> str:
    config = result.config
    lines = [banner("Organic Google results / SerpApi"), ""]
    if result.status == "found":
        lines.append(style(f"  #{result.rank}  Match found", "1;32"))
        lines.append("  " + style(result.url or "", "4;36"))
    elif result.status == "not_found":
        lines.append(style("  No match found", "1;33"))
        lines.append("  Your website did not appear in the positions checked.")
    elif result.status == "incomplete":
        lines.append(style("  Search incomplete", "1;33"))
        lines.append("  The full requested depth was not checked.")
    else:
        lines.append(style("  Search failed", "1;31"))
        lines.append("  No ranking conclusion is available.")
    if result.error:
        lines.extend(_row("Error", result.error))

    lines.append(section("Search"))
    for label, value in [
        ("Website", config.domain),
        ("Keyword", config.query),
        ("Country", config.country.upper()),
        ("Language", config.language),
        ("Device", config.device.capitalize()),
        ("Location", config.location or "Provider-selected"),
    ]:
        lines.extend(_row(label, value))
    locations = list(
        dict.fromkeys(
            ", ".join(part.strip() for part in item["location_used"].split(","))
            for item in result.searches
            if item.get("location_used")
        )
    )
    if locations:
        lines.extend(_row("Location used", "; ".join(locations)))
    lines.extend(
        _row("Matching", "Domain and subdomains" if config.include_subdomains else "Exact hostname")
    )
    for observation in result.searches:
        displayed = observation.get("query_displayed")
        if displayed and displayed != config.query:
            lines.extend(_row("Query shown", displayed))
            break

    lines.append(section("Coverage"))
    lines.extend(_row("Results checked", str(result.results_checked)))
    lines.extend(
        _row(
            "Deepest position",
            f"#{result.deepest_rank_checked} of top {config.max_results}"
            if result.deepest_rank_checked
            else "No organic positions checked",
        )
    )
    pages = f"{result.pages_checked}"
    if result.page:
        pages += f"; match on page {result.page}"
    lines.extend(_row("Pages fetched", pages))
    lines.extend(_row("HTTP requests", str(result.requests_made)))
    stop_reasons = {
        "match": "Match found",
        "end_of_results": "End of available results",
        "depth_limit": "Requested depth reached",
        "page_limit": "Page budget reached",
        "provider_error": "Provider error",
    }
    lines.extend(_row("Stopped because", stop_reasons.get(result.stop_reason, result.stop_reason)))
    try:
        checked_at = datetime.fromisoformat(result.checked_at).strftime("%d %b %Y, %H:%M:%S %Z")
    except ValueError:
        checked_at = result.checked_at
    lines.append(section("Timing"))
    lines.extend(_row("Retrieved", checked_at))
    lines.extend(_row("Cache", "Bypassed" if config.fresh else "Allowed"))
    return "\n".join(lines) + "\n"
