"""Specialized SerpApi tool handlers exposed directly to Hermes."""

from __future__ import annotations

import json
from typing import Any

from .client import SerpApiError, call_serpapi

_MAX_RESULTS = 20


def _json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False)


def _error(message: str) -> str:
    return _json({"success": False, "error": message})


def _query(args: dict[str, Any]) -> str:
    return str(args.get("query") or "").strip()


def _limit(args: dict[str, Any]) -> int:
    try:
        return max(1, min(int(args.get("limit", 5)), _MAX_RESULTS))
    except (TypeError, ValueError):
        return 5


def _code(args: dict[str, Any], name: str) -> str | None:
    value = str(args.get(name) or "").strip().lower()
    if not value:
        return None
    if len(value) != 2 or not value.isalpha():
        raise ValueError(f"{name} must be a two-letter code")
    return value


def _optional_fields(item: dict[str, Any], names: tuple[str, ...]) -> dict[str, Any]:
    return {name: item[name] for name in names if item.get(name) not in (None, "", [])}


def maps_search(args: dict[str, Any], **kwargs: Any) -> str:
    """Search Google Maps for places and local businesses."""
    del kwargs
    query = _query(args)
    if not query:
        return _error("Search query must not be empty")

    location = str(args.get("location") or "").strip()
    latitude = args.get("latitude")
    longitude = args.get("longitude")
    has_coordinates = latitude is not None or longitude is not None
    if has_coordinates and (latitude is None or longitude is None):
        return _error("latitude and longitude must be provided together")
    if location and has_coordinates:
        return _error("Use either location or latitude/longitude, not both")

    try:
        params: dict[str, Any] = {
            "q": query,
            "type": "search",
            "hl": _code(args, "language"),
            "gl": _code(args, "country"),
        }
        if location:
            params.update({"location": location, "z": int(args.get("zoom", 14))})
        elif has_coordinates:
            params.update(
                {
                    "lat": float(latitude),
                    "lon": float(longitude),
                    "z": int(args.get("zoom", 14)),
                }
            )
        if args.get("nearby"):
            if not location and not has_coordinates:
                return _error("nearby requires a location or latitude/longitude")
            params["nearby"] = "true"
        payload = call_serpapi("google_maps", params)
    except (TypeError, ValueError) as exc:
        return _error(str(exc))
    except SerpApiError as exc:
        return _error(str(exc))

    results = []
    raw_results = payload.get("local_results", [])
    if not isinstance(raw_results, list):
        return _error("SerpApi returned an unexpected Google Maps response")
    for index, item in enumerate(raw_results[: _limit(args)], start=1):
        if not isinstance(item, dict):
            continue
        result = {
            "position": item.get("position", index),
            **_optional_fields(
                item,
                (
                    "title",
                    "type",
                    "address",
                    "rating",
                    "reviews",
                    "price",
                    "open_state",
                    "phone",
                    "website",
                    "place_id",
                ),
            ),
        }
        coordinates = item.get("gps_coordinates")
        if isinstance(coordinates, dict):
            result["coordinates"] = coordinates
        results.append(result)

    return _json(
        {
            "success": True,
            "engine": "google_maps",
            "query": query,
            "results_count": len(results),
            "results": results,
        }
    )


def news_search(args: dict[str, Any], **kwargs: Any) -> str:
    """Search Google News Light for recent reporting."""
    del kwargs
    query = _query(args)
    if not query:
        return _error("Search query must not be empty")

    try:
        payload = call_serpapi(
            "google_news_light",
            {
                "q": query,
                "location": str(args.get("location") or "").strip(),
                "hl": _code(args, "language"),
                "gl": _code(args, "country"),
            },
        )
    except (TypeError, ValueError) as exc:
        return _error(str(exc))
    except SerpApiError as exc:
        return _error(str(exc))

    results = []
    raw_results = payload.get("news_results", [])
    if not isinstance(raw_results, list):
        return _error("SerpApi returned an unexpected Google News response")
    for index, item in enumerate(raw_results[: _limit(args)], start=1):
        if not isinstance(item, dict):
            continue
        results.append(
            {
                "position": item.get("position", index),
                **_optional_fields(item, ("title", "link", "source", "date", "snippet")),
            }
        )

    return _json(
        {
            "success": True,
            "engine": "google_news_light",
            "query": query,
            "results_count": len(results),
            "results": results,
        }
    )


def shopping_search(args: dict[str, Any], **kwargs: Any) -> str:
    """Search Google Shopping Light for products and prices."""
    del kwargs
    query = _query(args)
    if not query:
        return _error("Search query must not be empty")

    minimum_price = args.get("minimum_price")
    maximum_price = args.get("maximum_price")
    if minimum_price is not None and maximum_price is not None:
        try:
            if float(minimum_price) > float(maximum_price):
                return _error("minimum_price must not exceed maximum_price")
        except (TypeError, ValueError):
            return _error("minimum_price and maximum_price must be numbers")

    sort_by = {
        "price_low_to_high": "1",
        "price_high_to_low": "2",
    }.get(str(args.get("sort") or "relevance"))

    try:
        payload = call_serpapi(
            "google_shopping_light",
            {
                "q": query,
                "location": str(args.get("location") or "").strip(),
                "hl": _code(args, "language"),
                "gl": _code(args, "country"),
                "min_price": minimum_price,
                "max_price": maximum_price,
                "sort_by": sort_by,
                "free_shipping": "true" if args.get("free_shipping") else None,
                "on_sale": "true" if args.get("on_sale") else None,
            },
        )
    except (TypeError, ValueError) as exc:
        return _error(str(exc))
    except SerpApiError as exc:
        return _error(str(exc))

    results = []
    raw_results = payload.get("shopping_results", [])
    if not isinstance(raw_results, list):
        return _error("SerpApi returned an unexpected Google Shopping response")
    for index, item in enumerate(raw_results[: _limit(args)], start=1):
        if not isinstance(item, dict):
            continue
        result = {
            "position": item.get("position", index),
            **_optional_fields(
                item,
                (
                    "title",
                    "source",
                    "price",
                    "extracted_price",
                    "old_price",
                    "rating",
                    "reviews",
                    "delivery",
                    "snippet",
                    "product_id",
                ),
            ),
        }
        link = item.get("link") or item.get("product_link")
        if link:
            result["link"] = link
        results.append(result)

    return _json(
        {
            "success": True,
            "engine": "google_shopping_light",
            "query": query,
            "results_count": len(results),
            "results": results,
        }
    )
