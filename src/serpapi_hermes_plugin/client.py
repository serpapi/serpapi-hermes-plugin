"""Shared SerpApi HTTP client for the provider and specialized tools."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import httpx

logger = logging.getLogger(__name__)

API_KEY_ENV = "SERPAPI_API_KEY"
ENDPOINT = "https://serpapi.com/search"
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


def _redact_response(value: Any, api_key: str) -> Any:
    """Remove the credential from any response text before returning it to Hermes."""
    if isinstance(value, str):
        return value.replace(api_key, "[redacted]")
    if isinstance(value, list):
        return [_redact_response(item, api_key) for item in value]
    if isinstance(value, dict):
        return {key: _redact_response(item, api_key) for key, item in value.items()}
    return value


def call_serpapi(engine: str, params: Mapping[str, Any]) -> dict[str, Any] | str:
    """Call one SerpApi engine and return Markdown by default or decoded JSON."""
    api_key = get_api_key()
    if not api_key:
        raise SerpApiError(f"{API_KEY_ENV} is not set. Run `hermes tools` to configure SerpApi.")

    request_params = {
        key: value
        for key, value in params.items()
        if key not in {"api_key", "engine"} and value is not None and value != ""
    }
    output = str(request_params.get("output") or "md").strip().lower()
    if output not in {"json", "md"}:
        raise SerpApiError("output must be 'md' or 'json'")
    request_params.update({"engine": engine, "api_key": api_key, "output": output})

    try:
        response = httpx.get(
            ENDPOINT,
            params=request_params,
            headers={
                "Accept": "text/markdown" if output == "md" else "application/json",
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

    if output == "md" and "application/json" not in response.headers.get("content-type", ""):
        markdown = response.text.replace(api_key, "[redacted]").strip()
        if not markdown:
            raise SerpApiError("SerpApi returned an empty Markdown response")
        return markdown

    try:
        payload = _redact_response(response.json(), api_key)
    except ValueError:
        response_name = "Markdown" if output == "md" else "JSON"
        logger.warning("SerpApi returned malformed %s", response_name)
        raise SerpApiError(f"SerpApi returned malformed {response_name}") from None

    if not isinstance(payload, dict):
        raise SerpApiError("SerpApi returned an unexpected response")

    if payload.get("error"):
        raise SerpApiError(_safe_api_error(payload["error"], api_key))

    if output == "md":
        raise SerpApiError("SerpApi returned an unexpected Markdown response")

    return payload
