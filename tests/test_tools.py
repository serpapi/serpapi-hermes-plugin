from __future__ import annotations

import json
from typing import Any

import pytest


def test_maps_search_routes_parameters_and_normalizes_json_results(
    tools_module, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    def fake_call(engine: str, params: dict[str, Any]) -> dict[str, Any]:
        captured.update({"engine": engine, "params": params})
        return {
            "local_results": [
                {
                    "position": 1,
                    "title": "Joe's Pizza",
                    "type": "Pizza restaurant",
                    "address": "New York, NY",
                    "rating": 4.5,
                    "reviews": 17266,
                    "gps_coordinates": {"latitude": 40.75, "longitude": -73.98},
                    "place_id": "place-1",
                    "thumbnail": "ignored",
                }
            ]
        }

    monkeypatch.setattr(tools_module, "call_serpapi", fake_call)

    result = json.loads(
        tools_module.maps_search(
            {
                "query": "pizza",
                "location": "New York, NY",
                "nearby": True,
                "language": "en",
                "country": "us",
                "output": "json",
            }
        )
    )

    assert captured == {
        "engine": "google_maps",
        "params": {
            "q": "pizza",
            "type": "search",
            "hl": "en",
            "gl": "us",
            "location": "New York, NY",
            "z": 14,
            "nearby": "true",
            "output": "json",
        },
    }
    assert result == {
        "success": True,
        "engine": "google_maps",
        "query": "pizza",
        "results_count": 1,
        "results": [
            {
                "position": 1,
                "title": "Joe's Pizza",
                "type": "Pizza restaurant",
                "address": "New York, NY",
                "rating": 4.5,
                "reviews": 17266,
                "place_id": "place-1",
                "coordinates": {"latitude": 40.75, "longitude": -73.98},
            }
        ],
    }


def test_maps_search_validates_origin(tools_module) -> None:
    result = json.loads(tools_module.maps_search({"query": "coffee", "latitude": 12.9}))

    assert result["success"] is False
    assert "latitude and longitude" in result["error"]


def test_news_search_routes_and_normalizes_json_results(
    tools_module, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    def fake_call(engine: str, params: dict[str, Any]) -> dict[str, Any]:
        captured.update({"engine": engine, "params": params})
        return {
            "news_results": [
                {
                    "position": 1,
                    "title": "Launch succeeds",
                    "link": "https://example.com/news",
                    "source": "Example News",
                    "date": "2 hours ago",
                    "snippet": "A reusable rocket launched successfully.",
                    "thumbnail": "ignored",
                }
            ]
        }

    monkeypatch.setattr(tools_module, "call_serpapi", fake_call)
    result = json.loads(
        tools_module.news_search(
            {
                "query": "reusable rockets",
                "location": "Florida",
                "country": "us",
                "output": "json",
            }
        )
    )

    assert captured == {
        "engine": "google_news_light",
        "params": {
            "q": "reusable rockets",
            "location": "Florida",
            "hl": None,
            "gl": "us",
            "output": "json",
        },
    }
    assert result["results"] == [
        {
            "position": 1,
            "title": "Launch succeeds",
            "link": "https://example.com/news",
            "source": "Example News",
            "date": "2 hours ago",
            "snippet": "A reusable rocket launched successfully.",
        }
    ]


def test_shopping_search_routes_filters_and_normalizes_json_results(
    tools_module, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    def fake_call(engine: str, params: dict[str, Any]) -> dict[str, Any]:
        captured.update({"engine": engine, "params": params})
        return {
            "shopping_results": [
                {
                    "position": 1,
                    "title": "Laptop",
                    "product_link": "https://example.com/product",
                    "source": "Example Store",
                    "price": "$999",
                    "extracted_price": 999,
                    "rating": 4.7,
                    "reviews": 321,
                    "delivery": "Free delivery",
                    "product_id": "product-1",
                }
            ]
        }

    monkeypatch.setattr(tools_module, "call_serpapi", fake_call)
    result = json.loads(
        tools_module.shopping_search(
            {
                "query": "laptop",
                "minimum_price": 500,
                "maximum_price": 1200,
                "sort": "price_low_to_high",
                "free_shipping": True,
                "country": "us",
                "output": "json",
            }
        )
    )

    assert captured == {
        "engine": "google_shopping_light",
        "params": {
            "q": "laptop",
            "location": "",
            "hl": None,
            "gl": "us",
            "min_price": 500,
            "max_price": 1200,
            "sort_by": "1",
            "free_shipping": "true",
            "on_sale": None,
            "output": "json",
        },
    }
    assert result["results"] == [
        {
            "position": 1,
            "title": "Laptop",
            "source": "Example Store",
            "price": "$999",
            "extracted_price": 999,
            "rating": 4.7,
            "reviews": 321,
            "delivery": "Free delivery",
            "product_id": "product-1",
            "link": "https://example.com/product",
        }
    ]


@pytest.mark.parametrize(
    ("handler_name", "args", "engine"),
    [
        ("maps_search", {"query": "coffee"}, "google_maps"),
        ("news_search", {"query": "technology"}, "google_news_light"),
        ("shopping_search", {"query": "headphones"}, "google_shopping_light"),
    ],
)
def test_existing_direct_tools_return_serpapi_markdown_by_default(
    tools_module,
    monkeypatch: pytest.MonkeyPatch,
    handler_name: str,
    args: dict[str, Any],
    engine: str,
) -> None:
    captured: dict[str, Any] = {}
    markdown = "---\nengine: test\n---\n\n## Results"

    def fake_call(actual_engine: str, params: dict[str, Any]) -> str:
        captured.update({"engine": actual_engine, "params": params})
        return markdown

    monkeypatch.setattr(tools_module, "call_serpapi", fake_call)

    result = getattr(tools_module, handler_name)(args)

    assert result == markdown
    assert captured["engine"] == engine
    assert captured["params"]["output"] == "md"


def test_hotels_search_routes_agent_friendly_parameters(
    tools_module, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}
    markdown = "---\nengine: google_hotels\n---\n\n## Properties"

    def fake_call(engine: str, params: dict[str, Any]) -> str:
        captured.update({"engine": engine, "params": params})
        return markdown

    monkeypatch.setattr(tools_module, "call_serpapi", fake_call)

    result = tools_module.hotels_search(
        {
            "query": "Bali resorts",
            "check_in_date": "2026-10-10",
            "check_out_date": "2026-10-15",
            "adults": 3,
            "currency": "usd",
            "country": "id",
            "sort": "lowest_price",
        }
    )

    assert result == markdown
    assert captured == {
        "engine": "google_hotels",
        "params": {
            "q": "Bali resorts",
            "check_in_date": "2026-10-10",
            "check_out_date": "2026-10-15",
            "adults": 3,
            "children": 0,
            "currency": "USD",
            "hl": None,
            "gl": "id",
            "min_price": None,
            "max_price": None,
            "sort_by": "3",
            "hotel_class": None,
            "vacation_rentals": None,
            "output": "md",
        },
    }


def test_flights_search_infers_one_way_and_routes_filters(
    tools_module, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}
    markdown = "---\nengine: google_flights\n---\n\n## Best flights"

    def fake_call(engine: str, params: dict[str, Any]) -> str:
        captured.update({"engine": engine, "params": params})
        return markdown

    monkeypatch.setattr(tools_module, "call_serpapi", fake_call)

    result = tools_module.flights_search(
        {
            "departure_id": "JFK",
            "arrival_id": "LAX",
            "outbound_date": "2026-10-10",
            "currency": "USD",
            "country": "us",
            "stops": "nonstop",
            "sort": "price",
            "maximum_price": 500,
        }
    )

    assert result == markdown
    assert captured == {
        "engine": "google_flights",
        "params": {
            "departure_id": "JFK",
            "arrival_id": "LAX",
            "outbound_date": "2026-10-10",
            "return_date": None,
            "type": "2",
            "travel_class": "1",
            "adults": 1,
            "children": 0,
            "currency": "USD",
            "hl": None,
            "gl": "us",
            "stops": "1",
            "sort_by": "2",
            "max_price": 500,
            "deep_search": None,
            "departure_token": "",
            "output": "md",
        },
    }


def test_travel_explore_routes_region_discovery(
    tools_module, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}
    markdown = "---\nengine: google_travel_explore\n---\n\n## Destinations"

    def fake_call(engine: str, params: dict[str, Any]) -> str:
        captured.update({"engine": engine, "params": params})
        return markdown

    monkeypatch.setattr(tools_module, "call_serpapi", fake_call)

    result = tools_module.travel_explore_search(
        {
            "departure_id": "/m/02_286",
            "arrival_area_id": "/m/02j9z",
            "month": 10,
            "travel_duration": "weekend",
            "currency": "eur",
        }
    )

    assert result == markdown
    assert captured == {
        "engine": "google_travel_explore",
        "params": {
            "departure_id": "/m/02_286",
            "arrival_id": None,
            "arrival_area_id": "/m/02j9z",
            "outbound_date": None,
            "return_date": None,
            "type": "1",
            "month": 10,
            "travel_duration": "1",
            "travel_class": "1",
            "adults": 1,
            "children": 0,
            "currency": "EUR",
            "hl": None,
            "gl": None,
            "stops": "0",
            "max_price": None,
            "output": "md",
        },
    }


@pytest.mark.parametrize(
    ("handler_name", "args", "message"),
    [
        (
            "hotels_search",
            {
                "query": "Paris",
                "check_in_date": "2026-10-10",
                "check_out_date": "2026-10-09",
            },
            "check_out_date must be after check_in_date",
        ),
        (
            "flights_search",
            {
                "departure_id": "jfk",
                "arrival_id": "LAX",
                "outbound_date": "2026-10-10",
            },
            "uppercase three-letter airport codes",
        ),
        (
            "travel_explore_search",
            {
                "departure_id": "JFK",
                "arrival_id": "LAX",
                "arrival_area_id": "/m/02j9z",
            },
            "either arrival_id or arrival_area_id",
        ),
    ],
)
def test_travel_tools_reject_invalid_requests(
    tools_module,
    handler_name: str,
    args: dict[str, Any],
    message: str,
) -> None:
    result = json.loads(getattr(tools_module, handler_name)(args))

    assert result["success"] is False
    assert message in result["error"]


def test_specialized_tool_returns_safe_client_error(
    tools_module, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(engine: str, params: dict[str, Any]) -> dict[str, Any]:
        del engine, params
        raise tools_module.SerpApiError("SerpApi quota exhausted; try again later")

    monkeypatch.setattr(tools_module, "call_serpapi", fail)

    result = json.loads(tools_module.news_search({"query": "test"}))

    assert result == {
        "success": False,
        "error": "SerpApi quota exhausted; try again later",
    }
