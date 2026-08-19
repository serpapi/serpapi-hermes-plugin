"""Hermes web-search provider backed by SerpApi's Google Light API."""

from __future__ import annotations

import logging
from typing import Any

from agent.web_search_provider import WebSearchProvider

from .client import API_KEY_ENV, SerpApiError, call_serpapi, is_configured

logger = logging.getLogger(__name__)

_ENGINE = "google_light"
_MAX_RESULTS = 20


class SerpApiWebSearchProvider(WebSearchProvider):
    """Search-only Hermes provider using SerpApi's low-latency Google Light engine."""

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
        return False

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
            "badge": "Google Light",
            "tag": "Fast Google Light web search via SerpApi.",
            "env_vars": [
                {
                    "key": API_KEY_ENV,
                    "prompt": "SerpApi API key",
                    "url": "https://serpapi.com/manage-api-key",
                }
            ],
        }
