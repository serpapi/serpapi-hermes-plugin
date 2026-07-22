from __future__ import annotations

import json
from typing import Any

import pytest


def test_maps_search_routes_parameters_and_normalizes_results(
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


def test_news_search_routes_and_normalizes_results(
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
            {"query": "reusable rockets", "location": "Florida", "country": "us"}
        )
    )

    assert captured == {
        "engine": "google_news_light",
        "params": {
            "q": "reusable rockets",
            "location": "Florida",
            "hl": None,
            "gl": "us",
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


def test_shopping_search_routes_filters_and_normalizes_results(
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
