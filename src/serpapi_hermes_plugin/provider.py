"""Hermes web search and extraction backed by SerpApi."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from typing import Any

from agent.web_search_provider import WebSearchProvider

from .client import API_KEY_ENV, SerpApiError, call_serpapi, is_configured
from .extraction import WebsitePolicyError, extract_page, page_content

logger = logging.getLogger(__name__)

_ENGINE = "google_light"
_MAX_RESULTS = 20


class SerpApiWebSearchProvider(WebSearchProvider):
    """Hermes provider using Google Light for search and Extract for page content."""

    @property
    def name(self) -> str:
        return "serpapi"

    @property
    def display_name(self) -> str:
        return "SerpApi"

    def is_available(self) -> bool:
        """Check local configuration without making a network request."""
        return is_configured()

    def supports_search(self) -> bool:
        return True

    def supports_extract(self) -> bool:
        return True

    def extract(self, urls: list[str], **kwargs: Any) -> list[dict[str, Any]]:
        """Return ordered Hermes documents, preserving individual URL failures."""
        if not urls:
            return []

        def extract_one(url: str) -> dict[str, Any]:
            document: dict[str, Any] = {
                "url": url,
                "title": "",
                "content": "",
                "raw_content": "",
            }
            try:
                payload = extract_page(url)
                content = page_content(payload, format=kwargs.get("format"))
                page = payload.get("page_information")
                if not isinstance(page, dict):
                    page = {}
                document.update(
                    title=page.get("title") or "",
                    content=content,
                    raw_content=content,
                    metadata={**page, "sourceURL": url},
                )
            except (ValueError, SerpApiError) as exc:
                document["error"] = str(exc)
                if isinstance(exc, WebsitePolicyError):
                    document["blocked_by_policy"] = True
            return document

        # Hermes allows five URLs per call and caps the whole dispatch at 120 seconds.
        with ThreadPoolExecutor(max_workers=min(len(urls), 5)) as executor:
            # Carry Hermes's profile-scoped credentials into each worker.
            futures = [executor.submit(copy_context().run, extract_one, url) for url in urls]
            return [future.result() for future in futures]

    def search(self, query: str, limit: int = 5) -> dict[str, Any]:
        """Search Google Light and return Hermes's standard web result envelope."""
        query = str(query or "").strip()
        if not query:
            return {"success": False, "error": "Search query must not be empty"}

        try:
            result_limit = max(1, min(int(limit), _MAX_RESULTS))
        except (TypeError, ValueError):
            result_limit = 5

        try:
            payload = call_serpapi(
                _ENGINE,
                {
                    "q": query,
                    "num": result_limit,
                    "output": "json",
                },
            )
        except SerpApiError as exc:
            return {"success": False, "error": str(exc)}

        organic_results = payload.get("organic_results", [])
        if not isinstance(organic_results, list):
            return {"success": False, "error": "SerpApi returned an unexpected response"}

        web_results = []
        for result in organic_results[:result_limit]:
            if not isinstance(result, dict):
                continue
            web_results.append(
                {
                    "title": str(result.get("title", "")),
                    "url": str(result.get("link", "")),
                    "description": str(result.get("snippet", "")),
                    "position": len(web_results) + 1,
                }
            )

        logger.info("SerpApi search returned %d result(s)", len(web_results))
        return {"success": True, "data": {"web": web_results}}

    def get_setup_schema(self) -> dict[str, Any]:
        """Describe SerpApi to Hermes's interactive provider picker."""
        return {
            "name": "SerpApi",
            "badge": "Google Light + Extract",
            "tag": "Google Light web search and page extraction via SerpApi.",
            "env_vars": [
                {
                    "key": API_KEY_ENV,
                    "prompt": "SerpApi API key",
                    "url": "https://serpapi.com/manage-api-key",
                }
            ],
        }
