"""Specialized SerpApi tool handlers exposed directly to Hermes."""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from .client import SerpApiError, call_serpapi
from .markdown import limit_result_table

_MAX_RESULTS = 20


def _json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False)


def _error(message: str) -> str:
    return _json({"success": False, "error": message})


def _query(args: dict[str, Any]) -> str:
    return str(args.get("query") or "").strip()


def _output(args: dict[str, Any]) -> str:
    output = str(args.get("output") or "md").strip().lower()
    if output not in {"md", "json"}:
        raise ValueError("output must be 'md' or 'json'")
    return output


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


def _currency(args: dict[str, Any]) -> str | None:
    value = str(args.get("currency") or "").strip().upper()
    if not value:
        return None
    if len(value) != 3 or not value.isalpha():
        raise ValueError("currency must be a three-letter code")
    return value


def _date(args: dict[str, Any], name: str, *, required: bool = False) -> str | None:
    value = str(args.get(name) or "").strip()
    if not value:
        if required:
            raise ValueError(f"{name} is required")
        return None
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{name} must use YYYY-MM-DD") from None
    if parsed.isoformat() != value:
        raise ValueError(f"{name} must use YYYY-MM-DD")
    return value


def _travel_id(args: dict[str, Any], name: str, *, required: bool = False) -> str | None:
    value = str(args.get(name) or "").strip()
    if not value:
        if required:
            raise ValueError(f"{name} is required")
        return None
    identifiers = [identifier.strip() for identifier in value.split(",")]
    if any(
        not identifier
        or not (
            (len(identifier) == 3 and identifier.isalpha() and identifier.isupper())
            or identifier.startswith(("/m/", "/g/"))
        )
        for identifier in identifiers
    ):
        raise ValueError(
            f"{name} must contain uppercase three-letter airport codes or /m/ or /g/ KGMIDs"
        )
    return ",".join(identifiers)


def _passengers(args: dict[str, Any], *, adults_default: int = 1) -> dict[str, int]:
    values: dict[str, int] = {}
    for name, default in (("adults", adults_default), ("children", 0)):
        raw_value = args.get(name)
        if raw_value is None:
            values[name] = default
            continue
        value = int(raw_value)
        minimum = 1 if name == "adults" else 0
        if value < minimum or value > 9:
            raise ValueError(f"{name} must be between {minimum} and 9")
        values[name] = value
    return values


def _optional_fields(item: dict[str, Any], names: tuple[str, ...]) -> dict[str, Any]:
    return {name: item[name] for name in names if item.get(name) not in (None, "", [])}


def maps_search(args: dict[str, Any], **kwargs: Any) -> str:
    """Search Google Maps for places and local businesses."""
    del kwargs
    query = _query(args)
    if not query:
        return _error("Search query must not be empty")

    try:
        output = _output(args)
    except ValueError as exc:
        return _error(str(exc))

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
            "output": output,
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

    if isinstance(payload, str):
        return limit_result_table(payload, heading="Local Results", limit=_limit(args))

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
        output = _output(args)
        payload = call_serpapi(
            "google_news_light",
            {
                "q": query,
                "location": str(args.get("location") or "").strip(),
                "hl": _code(args, "language"),
                "gl": _code(args, "country"),
                "output": output,
            },
        )
    except (TypeError, ValueError) as exc:
        return _error(str(exc))
    except SerpApiError as exc:
        return _error(str(exc))

    if isinstance(payload, str):
        return limit_result_table(payload, heading="News Results", limit=_limit(args))

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

    try:
        output = _output(args)
    except ValueError as exc:
        return _error(str(exc))

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
                "output": output,
            },
        )
    except (TypeError, ValueError) as exc:
        return _error(str(exc))
    except SerpApiError as exc:
        return _error(str(exc))

    if isinstance(payload, str):
        return limit_result_table(payload, heading="Shopping Results", limit=_limit(args))

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


def hotels_search(args: dict[str, Any], **kwargs: Any) -> str:
    """Search Google Hotels for stays and nightly prices."""
    del kwargs
    query = _query(args)
    if not query:
        return _error("Search query must not be empty")

    try:
        output = _output(args)
        check_in_date = _date(args, "check_in_date", required=True)
        check_out_date = _date(args, "check_out_date", required=True)
        if date.fromisoformat(check_out_date) <= date.fromisoformat(check_in_date):
            return _error("check_out_date must be after check_in_date")

        minimum_price = args.get("minimum_price")
        maximum_price = args.get("maximum_price")
        if minimum_price is not None and float(minimum_price) < 0:
            return _error("minimum_price must be at least 0")
        if maximum_price is not None and float(maximum_price) < 0:
            return _error("maximum_price must be at least 0")
        if (
            minimum_price is not None
            and maximum_price is not None
            and float(minimum_price) > float(maximum_price)
        ):
            return _error("minimum_price must not exceed maximum_price")

        sort_by = {
            "lowest_price": "3",
            "highest_rating": "8",
            "most_reviewed": "13",
        }.get(str(args.get("sort") or "relevance"))
        payload = call_serpapi(
            "google_hotels",
            {
                "q": query,
                "check_in_date": check_in_date,
                "check_out_date": check_out_date,
                **_passengers(args, adults_default=2),
                "currency": _currency(args),
                "hl": _code(args, "language"),
                "gl": _code(args, "country"),
                "min_price": minimum_price,
                "max_price": maximum_price,
                "sort_by": sort_by,
                "hotel_class": args.get("hotel_class"),
                "vacation_rentals": "true" if args.get("vacation_rentals") else None,
                "output": output,
            },
        )
    except (TypeError, ValueError) as exc:
        return _error(str(exc))
    except SerpApiError as exc:
        return _error(str(exc))

    return payload if isinstance(payload, str) else _json(payload)


def flights_search(args: dict[str, Any], **kwargs: Any) -> str:
    """Search Google Flights for one-way or round-trip itineraries."""
    del kwargs
    try:
        output = _output(args)
        departure_id = _travel_id(args, "departure_id", required=True)
        arrival_id = _travel_id(args, "arrival_id", required=True)
        outbound_date = _date(args, "outbound_date", required=True)
        return_date = _date(args, "return_date")

        trip_type = str(args.get("trip_type") or "").strip()
        if not trip_type:
            trip_type = "round_trip" if return_date else "one_way"
        if trip_type not in {"round_trip", "one_way"}:
            return _error("trip_type must be 'round_trip' or 'one_way'")
        if trip_type == "round_trip" and not return_date:
            return _error("return_date is required for a round trip")
        if trip_type == "one_way" and return_date:
            return _error("return_date cannot be used for a one-way trip")
        if return_date and date.fromisoformat(return_date) < date.fromisoformat(outbound_date):
            return _error("return_date must not be before outbound_date")

        maximum_price = args.get("maximum_price")
        if maximum_price is not None and float(maximum_price) < 0:
            return _error("maximum_price must be at least 0")

        travel_class = {
            "economy": "1",
            "premium_economy": "2",
            "business": "3",
            "first": "4",
        }.get(str(args.get("travel_class") or "economy"))
        sort_by = {
            "top_flights": "1",
            "price": "2",
            "departure_time": "3",
            "arrival_time": "4",
            "duration": "5",
            "emissions": "6",
        }.get(str(args.get("sort") or "top_flights"))
        stops = {
            "any": "0",
            "nonstop": "1",
            "one_or_fewer": "2",
            "two_or_fewer": "3",
        }.get(str(args.get("stops") or "any"))
        payload = call_serpapi(
            "google_flights",
            {
                "departure_id": departure_id,
                "arrival_id": arrival_id,
                "outbound_date": outbound_date,
                "return_date": return_date,
                "type": "1" if trip_type == "round_trip" else "2",
                "travel_class": travel_class,
                **_passengers(args),
                "currency": _currency(args),
                "hl": _code(args, "language"),
                "gl": _code(args, "country"),
                "stops": stops,
                "sort_by": sort_by,
                "max_price": maximum_price,
                "deep_search": "true" if args.get("deep_search") else None,
                "departure_token": str(args.get("departure_token") or "").strip(),
                "output": output,
            },
        )
    except (TypeError, ValueError) as exc:
        return _error(str(exc))
    except SerpApiError as exc:
        return _error(str(exc))

    return payload if isinstance(payload, str) else _json(payload)


def travel_explore_search(args: dict[str, Any], **kwargs: Any) -> str:
    """Explore destinations and flexible trip prices with Google Travel Explore."""
    del kwargs
    try:
        output = _output(args)
        departure_id = _travel_id(args, "departure_id", required=True)
        arrival_id = _travel_id(args, "arrival_id")
        arrival_area_id = str(args.get("arrival_area_id") or "").strip() or None
        if arrival_id and arrival_area_id:
            return _error("Use either arrival_id or arrival_area_id, not both")
        if arrival_area_id and not arrival_area_id.startswith(("/m/", "/g/")):
            return _error("arrival_area_id must be a /m/ or /g/ region or country KGMID")

        outbound_date = _date(args, "outbound_date")
        return_date = _date(args, "return_date")
        if return_date and not outbound_date:
            return _error("outbound_date is required when return_date is provided")
        if return_date and date.fromisoformat(return_date) < date.fromisoformat(outbound_date):
            return _error("return_date must not be before outbound_date")

        trip_type = str(args.get("trip_type") or "").strip()
        if not trip_type:
            trip_type = "round_trip" if return_date or not outbound_date else "one_way"
        if trip_type not in {"round_trip", "one_way"}:
            return _error("trip_type must be 'round_trip' or 'one_way'")
        if trip_type == "round_trip" and outbound_date and not return_date:
            return _error("return_date is required for a fixed-date round trip")
        if trip_type == "one_way" and return_date:
            return _error("return_date cannot be used for a one-way trip")

        month = args.get("month")
        if month is not None and not 0 <= int(month) <= 12:
            return _error("month must be between 0 and 12")
        if outbound_date and month not in (None, 0, "0"):
            return _error("Use fixed dates or month, not both")

        maximum_price = args.get("maximum_price")
        if maximum_price is not None and float(maximum_price) < 0:
            return _error("maximum_price must be at least 0")

        travel_duration = {
            "weekend": "1",
            "one_week": "2",
            "two_weeks": "3",
        }.get(str(args.get("travel_duration") or "one_week"))
        travel_class = {
            "economy": "1",
            "premium_economy": "2",
            "business": "3",
            "first": "4",
        }.get(str(args.get("travel_class") or "economy"))
        stops = {
            "any": "0",
            "nonstop": "1",
            "one_or_fewer": "2",
            "two_or_fewer": "3",
        }.get(str(args.get("stops") or "any"))
        payload = call_serpapi(
            "google_travel_explore",
            {
                "departure_id": departure_id,
                "arrival_id": arrival_id,
                "arrival_area_id": arrival_area_id,
                "outbound_date": outbound_date,
                "return_date": return_date,
                "type": "1" if trip_type == "round_trip" else "2",
                "month": int(month) if month is not None else None,
                "travel_duration": travel_duration if not outbound_date else None,
                "travel_class": travel_class,
                **_passengers(args),
                "currency": _currency(args),
                "hl": _code(args, "language"),
                "gl": _code(args, "country"),
                "stops": stops,
                "max_price": maximum_price,
                "output": output,
            },
        )
    except (TypeError, ValueError) as exc:
        return _error(str(exc))
    except SerpApiError as exc:
        return _error(str(exc))

    return payload if isinstance(payload, str) else _json(payload)
