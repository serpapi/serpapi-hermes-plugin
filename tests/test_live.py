from __future__ import annotations

import os
from datetime import date, timedelta
from typing import Any
from urllib.parse import urlparse

import pytest
from markdown_it import MarkdownIt

pytestmark = pytest.mark.live

_MARKDOWN_PARSER = MarkdownIt("commonmark").enable("table")


@pytest.fixture(scope="module", autouse=True)
def require_serpapi_api_key() -> None:
    if not os.getenv("SERPAPI_API_KEY", "").strip():
        pytest.skip("SERPAPI_API_KEY is required for live tests")


def _assert_http_url(value: Any) -> None:
    parsed = urlparse(str(value))
    assert parsed.scheme in {"http", "https"}
    assert parsed.netloc


def _assert_markdown(value: str) -> None:
    assert isinstance(value, str)
    assert value.startswith("---\n")
    assert "\n---\n" in value
    assert any(marker in value for marker in ("\n## ", "\n|"))


def _markdown_result_count(value: str, heading: str) -> int:
    tokens = _MARKDOWN_PARSER.parse(value)
    section_level: int | None = None
    in_table_body = False
    result_count = 0

    for index, token in enumerate(tokens):
        if token.type == "heading_open":
            level = int(token.tag.removeprefix("h"))
            if section_level is not None and level <= section_level:
                break

            next_token = tokens[index + 1] if index + 1 < len(tokens) else None
            if (
                section_level is None
                and next_token is not None
                and next_token.type == "inline"
                and next_token.content == heading
            ):
                section_level = level
            continue

        if section_level is None:
            continue
        if token.type == "tbody_open":
            in_table_body = True
        elif token.type == "tbody_close":
            in_table_body = False
        elif token.type == "tr_open" and in_table_body:
            result_count += 1

    return result_count


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


def test_live_extract_returns_hermes_documents(provider_module) -> None:
    urls = ["https://www.python.org/about/", "https://example.com/"]
    results = provider_module.SerpApiWebSearchProvider().extract(urls, format="markdown")

    assert [result["url"] for result in results] == urls
    for result in results:
        assert "error" not in result, result.get("error")
        assert result["title"].strip()
        assert result["content"].strip()
        assert result["raw_content"] == result["content"]
        assert result["metadata"]["sourceURL"] == result["url"]


def test_live_extract_compact_and_full(tools_module) -> None:
    import json

    args = {"url": "https://www.python.org/about/"}
    compact = tools_module.extract(args)
    full = json.loads(tools_module.extract({**args, "compact_mode": False}))

    assert "error" not in full, full.get("error")
    assert "Python" in compact
    assert compact == full["text_content"]["markdown"].strip()
    assert full["page_information"]["title"].strip()
    assert full["meta_tags"]
    assert full["sections"]
    assert len(compact) < len(json.dumps(full))


def test_live_maps_search_returns_real_places(tools_module) -> None:
    limit = 3
    response = tools_module.maps_search(
        {
            "query": "coffee shops",
            "location": "Austin, Texas, United States",
            "country": "us",
            "limit": limit,
        }
    )

    _assert_markdown(response)
    assert _markdown_result_count(response, "Local Results") == limit
    assert "coffee" in response.lower()


def test_live_news_search_returns_real_articles(tools_module) -> None:
    limit = 3
    response = tools_module.news_search(
        {
            "query": "technology",
            "country": "us",
            "limit": limit,
        }
    )

    _assert_markdown(response)
    assert _markdown_result_count(response, "News Results") == limit
    assert "technology" in response.lower()


def test_live_shopping_search_returns_real_products(tools_module) -> None:
    limit = 3
    response = tools_module.shopping_search(
        {
            "query": "wireless headphones",
            "country": "us",
            "limit": limit,
        }
    )

    _assert_markdown(response)
    assert _markdown_result_count(response, "Shopping Results") == limit
    assert "headphones" in response.lower()


def test_live_hotels_search_returns_markdown_properties(tools_module) -> None:
    check_in = date.today() + timedelta(days=60)
    response = tools_module.hotels_search(
        {
            "query": "Bali resorts",
            "check_in_date": check_in.isoformat(),
            "check_out_date": (check_in + timedelta(days=2)).isoformat(),
            "children": 1,
            "children_ages": [5],
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
            "infants_on_lap": 1,
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
