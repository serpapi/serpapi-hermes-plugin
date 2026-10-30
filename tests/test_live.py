from __future__ import annotations

import json
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
    urls = ["https://www.python.org/about/"]
    results = provider_module.SerpApiWebSearchProvider().extract(urls, format="markdown")

    assert [result["url"] for result in results] == urls
    for result in results:
        assert "error" not in result, result.get("error")
        assert result["title"].strip()
        assert result["content"].strip()
        assert result["raw_content"] == result["content"]
        assert result["metadata"]["sourceURL"] == result["url"]


@pytest.mark.parametrize("mode", ["scrape", "map", "crawl"])
def test_live_extract_modes_compact_and_full(tools_module, monkeypatch, mode) -> None:
    responses = []
    extract_page = tools_module.extract_page

    def capture_response(*args, **kwargs):
        payload = extract_page(*args, **kwargs)
        responses.append(payload)
        return payload

    monkeypatch.setattr(tools_module, "extract_page", capture_response)
    args = {
        "url": "https://books.toscrape.com/catalogue/category/books/travel_2/index.html",
        "mode": mode,
    }
    if mode == "scrape":
        args.update({
            "url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
            "include_tags": ".product_main", "exclude_tags": "form",
        })
    elif mode == "map":
        args["include_sitemap"] = False
    else:
        args.update({"max_pages": 2, "max_depth": 1})
    compact = tools_module.extract(args)
    full = json.loads(tools_module.extract({**args, "compact_mode": False}))

    assert "error" not in full, full.get("error")
    assert len(responses) == 2, compact
    # Separate live requests can return different page text or discovered URLs.
    compact_payload = responses[0]
    if mode == "scrape":
        assert compact == compact_payload["markdown"].strip()
        for content in (compact, full["markdown"]):
            assert "# A Light in the Attic" in content
            assert "£51.77" in content
            assert "Add to basket" not in content
        assert full["page_information"]["title"].strip()
    else:
        field = "urls" if mode == "map" else "pages"
        for payload in (compact_payload, full):
            entries = payload[field]
            assert entries
            for entry in entries:
                assert "error" not in entry, entry.get("error")
                _assert_http_url(entry["url"])
                if payload is compact_payload:
                    assert f"<{entry['url']}>" in compact
                if mode == "crawl":
                    assert entry["markdown"].strip()
                    if payload is compact_payload:
                        assert entry["markdown"].strip() in compact
            if mode == "crawl":
                assert len(entries) == 2
                assert {page["depth"] for page in entries} == {0, 1}


@pytest.mark.parametrize("output", ["md", "json"])
def test_live_maps_search_returns_real_places(tools_module, output) -> None:
    limit = 3
    response = tools_module.maps_search(
        {
            "query": "coffee shops",
            "location": "Austin, Texas, United States",
            "country": "us",
            "limit": limit,
            "output": output,
            "language": "en-gb",
        }
    )

    if output == "md":
        _assert_markdown(response)
        assert _markdown_result_count(response, "Local Results") == limit
        assert "coffee" in response.lower()
    else:
        data = json.loads(response)
        assert data["success"] is True, data
        assert data["results_count"] == len(data["results"]) == limit
        assert all(result["title"] and result.get("coordinates") for result in data["results"])


def test_live_news_search_returns_real_articles(tools_module) -> None:
    limit = 3
    response = tools_module.news_search(
        {
            "query": "technology",
            "country": "mx",
            "language": "es-419",
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


def test_live_hotels_search_returns_properties(tools_module) -> None:
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
    assert _markdown_result_count(response, "Properties") > 0
    assert "bali" in response.lower()


def test_live_flights_search_returns_itineraries(tools_module) -> None:
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
    assert (_markdown_result_count(response, "Best Flights")
            + _markdown_result_count(response, "Other Flights")) > 0
    assert "JFK" in response
    assert "LAX" in response


def test_live_travel_explore_returns_destinations(tools_module) -> None:
    response = tools_module.travel_explore_search(
        {
            "departure_id": "JFK",
            "currency": "USD",
            "country": "us",
        }
    )

    _assert_markdown(response)
    assert _markdown_result_count(response, "Destinations") > 0
    assert "JFK" in response


@pytest.mark.parametrize("output", ["md", "json"])
def test_live_empty_search_returns_consistent_error(tools_module, output) -> None:
    response = json.loads(tools_module.news_search({
        "query": '"hermes-serpapi-no-results-20261029-zxqv-746291"',
        "country": "us", "output": output,
    }))
    assert response["success"] is False
    assert "hasn't returned any results" in response["error"]
