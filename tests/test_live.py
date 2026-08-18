from __future__ import annotations

import json
import os
from datetime import date, timedelta
from typing import Any
from urllib.parse import urlparse

import pytest

pytestmark = pytest.mark.live


@pytest.fixture(scope="module", autouse=True)
def require_serpapi_api_key() -> None:
    if not os.getenv("SERPAPI_API_KEY", "").strip():
        pytest.skip("SERPAPI_API_KEY is required for live tests")


def _assert_http_url(value: Any) -> None:
    parsed = urlparse(str(value))
    assert parsed.scheme in {"http", "https"}
    assert parsed.netloc


def _assert_live_results(payload: dict[str, Any], engine: str, limit: int) -> list[dict[str, Any]]:
    assert payload["success"] is True, payload
    assert payload["engine"] == engine

    results = payload["results"]
    assert isinstance(results, list)
    assert 1 <= len(results) <= limit
    assert payload["results_count"] == len(results)
    assert all(isinstance(result, dict) for result in results)
    return results


def _assert_markdown(value: str) -> None:
    assert isinstance(value, str)
    assert value.startswith("---\n")
    assert "\n---\n" in value
    assert any(marker in value for marker in ("\n## ", "\n|"))


def test_live_web_search_returns_real_hermes_results(provider_module) -> None:
    limit = 3
    response = provider_module.SerpApiWebSearchProvider().search(
        "SerpApi search API",
        limit=limit,
    )

    assert response["success"] is True, response
    results = response["data"]["web"]
    assert 1 <= len(results) <= limit
    assert [result["position"] for result in results] == list(range(1, len(results) + 1))

    for result in results:
        assert result["title"].strip()
        _assert_http_url(result["url"])
        assert isinstance(result["description"], str)


def test_live_maps_search_returns_real_places(tools_module) -> None:
    response = tools_module.maps_search(
        {
            "query": "coffee shops",
            "location": "Austin, Texas, United States",
            "country": "us",
        }
    )

    _assert_markdown(response)
    assert "coffee" in response.lower()


def test_live_news_search_returns_real_articles(tools_module) -> None:
    limit = 3
    payload = json.loads(
        tools_module.news_search(
            {
                "query": "technology",
                "country": "us",
                "limit": limit,
                "output": "json",
            }
        )
    )

    results = _assert_live_results(payload, "google_news_light", limit)
    for result in results:
        assert result["title"].strip()
        assert str(result["source"]).strip()
        _assert_http_url(result["link"])


def test_live_shopping_search_returns_real_products(tools_module) -> None:
    limit = 3
    payload = json.loads(
        tools_module.shopping_search(
            {
                "query": "wireless headphones",
                "country": "us",
                "limit": limit,
                "output": "json",
            }
        )
    )

    results = _assert_live_results(payload, "google_shopping_light", limit)
    for result in results:
        assert result["title"].strip()
        assert str(result["source"]).strip()
        assert any(field in result for field in ("price", "extracted_price"))
        _assert_http_url(result["link"])


def test_live_hotels_search_returns_markdown_properties(tools_module) -> None:
    check_in = date.today() + timedelta(days=60)
    response = tools_module.hotels_search(
        {
            "query": "Bali resorts",
            "check_in_date": check_in.isoformat(),
            "check_out_date": (check_in + timedelta(days=2)).isoformat(),
            "country": "id",
            "currency": "USD",
        }
    )

    _assert_markdown(response)
    assert "bali" in response.lower()


def test_live_flights_search_returns_markdown_itineraries(tools_module) -> None:
    outbound = date.today() + timedelta(days=60)
    response = tools_module.flights_search(
        {
            "departure_id": "JFK",
            "arrival_id": "LAX",
            "outbound_date": outbound.isoformat(),
            "return_date": (outbound + timedelta(days=7)).isoformat(),
            "country": "us",
            "currency": "USD",
        }
    )

    _assert_markdown(response)
    assert "JFK" in response
    assert "LAX" in response


def test_live_travel_explore_returns_markdown_destinations(tools_module) -> None:
    response = tools_module.travel_explore_search(
        {
            "departure_id": "JFK",
            "currency": "USD",
            "country": "us",
        }
    )

    _assert_markdown(response)
    assert "JFK" in response
