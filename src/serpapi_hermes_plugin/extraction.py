"""SerpApi extraction shared by the Hermes provider and direct tool."""

from __future__ import annotations

from typing import Any
from urllib.parse import unquote, urlsplit

import httpx

from .client import SerpApiError, call_serpapi


class WebsitePolicyError(SerpApiError):
    """An intentional website-policy refusal that Hermes must not retry elsewhere."""


def _check_url_policy(url: str) -> None:
    """Apply Hermes's secret-URL and website policy checks before any API request."""
    try:
        from agent.redact import _PREFIX_RE
        from tools.website_policy import check_website_access
    except ImportError:
        raise SerpApiError(
            "Update Hermes to a version with URL safety and website policy support"
        ) from None

    if _PREFIX_RE.search(url) or _PREFIX_RE.search(unquote(url)):
        raise WebsitePolicyError("Blocked: URL contains what appears to be an API key or token")
    if check_website_access(url):
        raise WebsitePolicyError("Blocked by website policy")


def _normalize_url(url: str) -> str:
    """Validate input and discovered URLs before passing them to URL consumers."""
    if not isinstance(url, str) or not url.strip():
        raise ValueError("url must be an absolute http or https URL")
    url = url.strip()
    try:
        parsed = urlsplit(url)
        valid = parsed.scheme in {"http", "https"} and bool(parsed.hostname)
        has_credentials = parsed.username is not None or parsed.password is not None
        _ = parsed.port  # Validate a supplied port before sending the request.
    except ValueError:
        raise ValueError("url must be an absolute http or https URL") from None
    if not valid or any(character.isspace() for character in url):
        raise ValueError("url must be an absolute http or https URL")
    if has_credentials:
        raise ValueError("url must not contain credentials")
    try:
        return str(httpx.URL(url))
    except httpx.InvalidURL:
        raise ValueError("url must be an absolute http or https URL") from None


def extract_page(
    url: str,
    *,
    mode: str = "scrape",
    compact_mode: bool = True,
    include_tags: str | None = None,
    exclude_tags: str | None = None,
    max_pages: int | None = None,
    max_depth: int | None = None,
    include_subdomains: bool | None = None,
    include_sitemap: bool | None = None,
) -> dict[str, Any]:
    """Scrape a page, map a site, or crawl it with optional response filtering."""
    normalized_url = _normalize_url(url)
    url = url.strip()
    if not isinstance(compact_mode, bool):
        raise ValueError("compact_mode must be a boolean")
    if not isinstance(mode, str) or mode not in {"scrape", "map", "crawl"}:
        raise ValueError("mode must be 'scrape', 'map', or 'crawl'")

    params: dict[str, Any] = {
        "url": normalized_url,
        "mode": mode,
        "output": "json",
    }
    for name, value, minimum, maximum in (
        ("max_pages", max_pages, 1, 100),
        ("max_depth", max_depth, 0, 3),
    ):
        if value is not None:
            if mode != "crawl":
                raise ValueError(f"{name} is only available with mode='crawl'")
            if type(value) is not int or not minimum <= value <= maximum:
                raise ValueError(f"{name} must be an integer from {minimum} to {maximum}")
            params[name] = value
    for name, value, modes in (
        ("include_subdomains", include_subdomains, {"map", "crawl"}),
        ("include_sitemap", include_sitemap, {"map"}),
    ):
        if value is not None:
            if mode not in modes:
                raise ValueError(f"{name} is only available with mode {' or '.join(sorted(modes))}")
            if not isinstance(value, bool):
                raise ValueError(f"{name} must be a boolean")
            params[name] = value
    for name, value in (("include_tags", include_tags), ("exclude_tags", exclude_tags)):
        if value is not None:
            if not isinstance(value, str):
                raise ValueError(f"{name} must be a string of CSS selectors")
            params[name] = value.strip()
    if compact_mode:
        params["json_restrictor"] = {
            "scrape": "page_information,markdown,error",
            "map": "search_parameters,page_information,urls[].{url,title,source},error",
            "crawl": (
                "search_parameters,page_information,"
                "pages[].{url,depth,page_information,markdown,error},error"
            ),
        }[mode]

    _check_url_policy(url)
    if normalized_url != url:
        _check_url_policy(normalized_url)

    payload = call_serpapi("extract", params)
    if not isinstance(payload, dict):
        raise SerpApiError("SerpApi returned an unexpected Extract response")
    _check_page_urls(payload)
    if mode != "scrape":
        field = "urls" if mode == "map" else "pages"
        # The API omits empty arrays. Keep the echoed mode in compact responses
        # so an empty map can be distinguished from an unrelated engine response.
        search_parameters = payload.get("search_parameters")
        matches_mode = (
            isinstance(search_parameters, dict)
            and search_parameters.get("engine") == "extract"
            and search_parameters.get("mode") == mode
        )
        entries = payload.get(field, [] if matches_mode else None)
        if not isinstance(entries, list):
            raise SerpApiError(f"SerpApi returned an unexpected {mode} response")
        checked_entries = []
        for entry in entries:
            try:
                _check_entry_urls(entry, mode)
            except SerpApiError as exc:
                # Keep other results without exposing the refused URL or page content.
                failure: dict[str, Any] = {"error": str(exc)}
                if isinstance(exc, WebsitePolicyError):
                    failure["blocked_by_policy"] = True
                checked_entries.append(failure)
            else:
                checked_entries.append(entry)
        if compact_mode:
            fields = (
                ("url", "title", "source", "error", "blocked_by_policy") if mode == "map"
                else ("url", "depth", "page_information", "markdown", "error", "blocked_by_policy")
            )
            return {
                field: [{k: entry[k] for k in fields if k in entry} for entry in checked_entries]
            }
        return {**payload, field: checked_entries}
    if compact_mode:
        # Keep the compact contract even if an upstream response ignores the filter.
        return {key: payload[key] for key in ("page_information", "markdown") if key in payload}
    return payload


def _check_entry_urls(entry: Any, mode: str) -> None:
    """Validate one discovered result without affecting other entries."""
    if not isinstance(entry, dict) or not isinstance(entry.get("url"), str):
        raise SerpApiError(f"SerpApi returned an unexpected {mode} entry")
    target = entry["url"]
    try:
        normalized_target = _normalize_url(target)
    except ValueError:
        raise SerpApiError(f"SerpApi returned an unexpected {mode} URL") from None
    _check_url_policy(target)
    if normalized_target != target:
        _check_url_policy(normalized_target)
    _check_page_urls(entry)


def _check_page_urls(payload: dict[str, Any]) -> None:
    """Check redirects for the seed page and for every returned crawl page."""
    page = payload.get("page_information")
    if isinstance(page, dict):
        for field in ("url", "final_url"):
            target = page.get(field)
            if isinstance(target, str) and target:
                _check_url_policy(target)


def compact_content(payload: dict[str, Any], mode: str) -> str:
    """Render compact Extract results without losing per-page crawl failures."""
    if mode == "scrape":
        return page_content(payload)
    if mode == "map":
        return "\n".join(
            f"- URL {index}: Error: {entry['error']}" if entry.get("error")
            else f"- {_url_link(entry['url'])}"
            for index, entry in enumerate(payload["urls"], start=1)
        ) or "No URLs found."
    sections = []
    for index, page in enumerate(payload["pages"], start=1):
        if page.get("error"):
            content = f"Error: {page['error']}"
        else:
            try:
                content = page_content(page)
            except SerpApiError as exc:
                content = f"Error: {exc}"
        heading = _url_link(page["url"]) if "url" in page else f"Page {index}"
        sections.append(f"## {heading}\n\n{content}")
    return "\n\n".join(sections) or "No pages extracted."


def _url_link(url: str) -> str:
    """Keep URL characters from breaking Markdown autolinks or headings."""
    for character in ("<", ">", "\n", "\r"):
        url = url.replace(character, f"%{ord(character):02X}")
    return f"<{url}>"


def page_content(payload: dict[str, Any]) -> str:
    """Read the page's main Markdown from the Extract response."""
    content = payload.get("markdown")
    if isinstance(content, str) and content.strip():
        return content.strip()
    raise SerpApiError("SerpApi returned no page content for this URL")
