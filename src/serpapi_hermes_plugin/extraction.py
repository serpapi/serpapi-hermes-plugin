"""Single-page extraction shared by the Hermes provider and direct tool."""

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
        raise SerpApiError("Blocked: URL contains what appears to be an API key or token")
    if check_website_access(url):
        raise WebsitePolicyError("Blocked by website policy")


def extract_page(
    url: str,
    *,
    compact_mode: bool = True,
    include_tags: str | None = None,
    exclude_tags: str | None = None,
) -> dict[str, Any]:
    """Request page content, optionally retaining all structured Extract fields."""
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
        normalized_url = str(httpx.URL(url))
    except httpx.InvalidURL:
        raise ValueError("url must be an absolute http or https URL") from None
    if not isinstance(compact_mode, bool):
        raise ValueError("compact_mode must be a boolean")

    params: dict[str, Any] = {
        "url": normalized_url,
        "mode": "scrape",
        "include_markdown": "true",
        "output": "json",
    }
    for name, value in (("include_tags", include_tags), ("exclude_tags", exclude_tags)):
        if value is not None:
            if not isinstance(value, str):
                raise ValueError(f"{name} must be a string of CSS selectors")
            params[name] = value.strip()
    if compact_mode:
        params["json_restrictor"] = "page_information,text_content,error"

    _check_url_policy(url)
    if normalized_url != url:
        _check_url_policy(normalized_url)

    payload = call_serpapi("extract", params)
    if not isinstance(payload, dict):
        raise SerpApiError("SerpApi returned an unexpected Extract response")
    page = payload.get("page_information")
    if isinstance(page, dict):
        for field in ("url", "final_url"):
            target = page.get(field)
            if isinstance(target, str) and target and target != normalized_url:
                _check_url_policy(target)
    if compact_mode:
        # Keep the compact contract even if an upstream response ignores the filter.
        return {key: payload[key] for key in ("page_information", "text_content") if key in payload}
    return payload


def page_content(payload: dict[str, Any], *, format: str | None = None) -> str:
    """Read complete Markdown or plain text without substituting a short excerpt."""
    text = payload.get("text_content")
    if isinstance(text, dict):
        fields = ("full", "markdown") if format == "text" else ("markdown", "full")
        for field in fields:
            content = text.get(field)
            if isinstance(content, str) and content.strip():
                return content.strip()
    raise SerpApiError("SerpApi returned no page content for this URL")
