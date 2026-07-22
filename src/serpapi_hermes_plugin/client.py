"""Shared SerpApi HTTP client for the provider and specialized tools."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import httpx

logger = logging.getLogger(__name__)

API_KEY_ENV = "SERPAPI_API_KEY"
ENDPOINT = "https://serpapi.com/search.json"
TIMEOUT_SECONDS = 15.0


class SerpApiError(RuntimeError):
    """A safe, user-facing SerpApi request error."""


def get_api_key() -> str:
    """Read the key through Hermes so values in ``~/.hermes/.env`` work."""
    from agent.web_search_provider import get_provider_env

    return get_provider_env(API_KEY_ENV)


def is_configured() -> bool:
    """Return whether Hermes can resolve a SerpApi API key locally."""
    return bool(get_api_key())


def _safe_api_error(value: Any, api_key: str) -> str:
    """Return a bounded API error without ever echoing the credential."""
    message = str(value or "Unknown SerpApi error").replace(api_key, "[redacted]")
    return message[:500]


def call_serpapi(engine: str, params: Mapping[str, Any]) -> dict[str, Any]:
    """Call one SerpApi engine and return its decoded JSON response."""
    api_key = get_api_key()
    if not api_key:
        raise SerpApiError(f"{API_KEY_ENV} is not set. Run `hermes tools` to configure SerpApi.")

    request_params = {
        key: value
        for key, value in params.items()
        if key not in {"api_key", "engine"} and value is not None and value != ""
    }
    request_params.update(
        {
            "engine": engine,
            "api_key": api_key,
            "output": "json",
        }
    )

    try:
        response = httpx.get(
            ENDPOINT,
            params=request_params,
            headers={
                "Accept": "application/json",
                "X-Client-Source": "hermes",
            },
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        logger.warning("SerpApi returned HTTP %d", status)
        if status == 401:
            message = "SerpApi rejected the API key"
        elif status == 429:
            message = "SerpApi quota exhausted; try again later"
        elif status >= 500:
            message = f"SerpApi upstream error (HTTP {status}); try again shortly"
        else:
            message = f"SerpApi request failed (HTTP {status})"
        raise SerpApiError(message) from None
    except httpx.RequestError as exc:
        logger.warning("SerpApi request failed (%s)", type(exc).__name__)
        raise SerpApiError("Could not reach SerpApi; try again shortly") from None

    try:
        payload = response.json()
    except ValueError:
        logger.warning("SerpApi returned malformed JSON")
        raise SerpApiError("SerpApi returned malformed JSON") from None

    if not isinstance(payload, dict):
        raise SerpApiError("SerpApi returned an unexpected response")

    if payload.get("error"):
        raise SerpApiError(_safe_api_error(payload["error"], api_key))

    return payload
