from __future__ import annotations

import json
import os
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
    limit = 3
    payload = json.loads(
        tools_module.maps_search(
            {
                "query": "coffee shops",
                "location": "Austin, Texas, United States",
                "country": "us",
                "limit": limit,
            }
        )
    )

    results = _assert_live_results(payload, "google_maps", limit)
    for result in results:
        assert result["title"].strip()
        assert isinstance(result["position"], int)
        assert result["position"] > 0
        assert any(
            field in result
            for field in ("address", "coordinates", "rating", "place_id")
        )


def test_live_news_search_returns_real_articles(tools_module) -> None:
    limit = 3
    payload = json.loads(
        tools_module.news_search(
            {
                "query": "technology",
                "country": "us",
                "limit": limit,
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
            }
        )
    )

    results = _assert_live_results(payload, "google_shopping_light", limit)
    for result in results:
        assert result["title"].strip()
        assert str(result["source"]).strip()
        assert any(field in result for field in ("price", "extracted_price"))
        _assert_http_url(result["link"])
