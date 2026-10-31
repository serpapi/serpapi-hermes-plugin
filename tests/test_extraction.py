from __future__ import annotations

import json
import sys
from contextvars import ContextVar
from threading import Barrier

import httpx
import pytest


@pytest.fixture
def extract_response(monkeypatch):
    monkeypatch.setenv("SERPAPI_API_KEY", "test-secret")
    requests = []
    payload = {
        "page_information": {"title": "Product", "final_url": "https://example.com/product"},
        "markdown": "# Product\n\nCosts **$20**.",
        "json_ld": [{"@type": "Product", "offers": {"price": "20"}}],
        "debug": "test-secret",
    }

    def fake_get(url, **kwargs):
        requests.append({"url": url, **kwargs})
        return httpx.Response(200, json=payload, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)
    return payload, requests


@pytest.mark.parametrize("compact_mode", [True, False])
def test_scrape_formats_and_css_filters(tools_module, extract_response, compact_mode):
    payload, requests = extract_response
    result = tools_module.extract({
        "url": "https://example.com/product", "compact_mode": compact_mode,
        "include_tags": "main,article", "exclude_tags": "nav,footer",
    })

    assert "test-secret" not in result
    assert (result if compact_mode else json.loads(result)["markdown"]) == payload["markdown"]
    if not compact_mode:
        assert json.loads(result) == {**payload, "debug": "[redacted]"}
    params = requests[0]["params"]
    assert (params["engine"], params["mode"], params["output"]) == ("extract", "scrape", "json")
    assert (params["include_tags"], params["exclude_tags"]) == ("main,article", "nav,footer")
    assert "json_restrictor" not in params
    assert "compact_mode" not in params


def test_missing_markdown_is_not_replaced_by_a_truncated_excerpt(tools_module, extract_response):
    payload, _ = extract_response
    del payload["markdown"]
    payload["text_content"] = {"excerpt": "A truncated legacy excerpt"}
    result = json.loads(tools_module.extract({"url": "https://example.com"}))
    assert result["success"] is False
    assert "no page content" in result["error"]


def test_routed_engines_preserve_results_in_compact_full_and_provider(
    tools_module, extract_response,
):
    from serpapi_hermes_plugin.provider import SerpApiWebSearchProvider

    payload, requests = extract_response
    payload.clear()
    payload.update({
        "search_parameters": {"engine": "google", "q": "coffee"},
        "search_metadata": {"google_url": "https://www.google.com/search?q=coffee"},
        "organic_results": [{"title": "Coffee", "link": "https://example.com/coffee"}],
        "shopping_results": [{"title": "Coffee beans", "price": "$12"}],
    })
    url = "https://www.google.com/search?q=coffee"
    for mode in ("scrape", "map", "crawl"):
        compact = tools_module.extract({"url": url, "mode": mode})
        data = json.loads(compact.split("```json\n", 1)[1].rsplit("\n```", 1)[0])
        assert data["organic_results"] == payload["organic_results"]
        assert data["shopping_results"] == payload["shopping_results"]
        assert "search_metadata" not in data
    full = json.loads(tools_module.extract({"url": url, "compact_mode": False}))
    assert full == payload
    document = SerpApiWebSearchProvider().extract([url])[0]
    assert "error" not in document
    assert document["content"] == document["raw_content"] == compact
    assert document["title"] == "google results"
    assert document["metadata"]["sourceURL"] == url
    assert all("json_restrictor" not in request["params"] for request in requests)

    routed_page = {**payload, "url": url, "depth": 1}
    payload.clear()
    payload.update({
        "search_parameters": {"engine": "extract", "mode": "crawl"},
        "pages": [routed_page],
    })
    crawl = tools_module.extract({"url": "https://example.com", "mode": "crawl"})
    assert f"<{url}>" in crawl
    assert '"organic_results"' in crawl and '"shopping_results"' in crawl


@pytest.mark.parametrize("args", [
    {"url": "https://user:password@example.com"},
    {"url": "file:///etc/passwd"},
    {"url": "https://"},
    {"url": "https://example.com:invalid/"},
    {"url": "https://example.com", "mode": "crawl", "max_pages": 101},
    {"url": "https://example.com", "mode": "scrape", "max_depth": 1},
])
def test_invalid_requests_fail_before_network_access(tools_module, extract_response, args):
    _, requests = extract_response
    assert json.loads(tools_module.extract(args))["success"] is False
    assert requests == []


def test_native_batch_preserves_order_profile_and_partial_failures(provider_module, monkeypatch):
    from agent import web_search_provider

    profile_key = ContextVar("profile_key", default="wrong-profile")
    monkeypatch.setattr(web_search_provider, "get_provider_env", lambda name: profile_key.get())
    barrier = Barrier(3)
    requests = []

    def fake_get(url, **kwargs):
        params = kwargs["params"]
        requests.append(params)
        barrier.wait(timeout=5)
        request = httpx.Request("GET", url)
        if params["url"].endswith("/error"):
            return httpx.Response(
                400, json={"error": "Cannot fetch profile-secret"}, request=request,
            )
        if params["url"].endswith("/timeout"):
            raise httpx.ReadTimeout("profile-secret", request=request)
        return httpx.Response(200, json={
            "markdown": "A page", "page_information": {"title": "Page"},
        }, request=request)

    monkeypatch.setattr(httpx, "get", fake_get)
    urls = ["https://example.com/error", "https://example.com/good", "https://example.com/timeout"]
    token = profile_key.set("profile-secret")
    try:
        results = provider_module.SerpApiWebSearchProvider().extract(
            urls, format="markdown", mode="crawl", max_pages=10,
        )
    finally:
        profile_key.reset(token)

    assert [result["url"] for result in results] == urls
    assert results[0]["error"] == "Cannot fetch [redacted]"
    assert results[1] == {
        "url": urls[1], "title": "Page", "content": "A page", "raw_content": "A page",
        "metadata": {"title": "Page", "sourceURL": urls[1]},
    }
    assert results[2]["error"] == "Could not reach SerpApi; try again shortly"
    assert "profile-secret" not in json.dumps(results)
    assert all(p["api_key"] == "profile-secret" and p["mode"] == "scrape" for p in requests)
    assert all("max_pages" not in p for p in requests)


def test_private_seed_never_reaches_serpapi(
    tools_module, provider_module, extract_response, monkeypatch
):
    _, requests = extract_response
    target = "http://127.0.0.1/"
    monkeypatch.setattr(sys.modules["tools.url_safety"], "is_safe_url",
                        lambda url: "127.0.0.1" not in url)

    direct = json.loads(tools_module.extract({"url": target}))
    native = provider_module.SerpApiWebSearchProvider().extract([target])[0]

    assert direct["success"] is False
    assert native["blocked_by_policy"] is True
    assert native["content"] == ""
    assert target not in direct["error"]
    assert requests == []


@pytest.mark.parametrize("compact_mode", [True, False])
def test_private_redirect_never_returns_content(
    tools_module, provider_module, extract_response, monkeypatch, compact_mode
):
    payload, _ = extract_response
    target = "http://[::1]/"
    payload["page_information"]["final_url"] = target
    monkeypatch.setattr(sys.modules["tools.url_safety"], "is_safe_url",
                        lambda url: "[::1]" not in url)

    direct = json.loads(tools_module.extract({
        "url": "https://example.com/product", "compact_mode": compact_mode,
    }))
    native = provider_module.SerpApiWebSearchProvider().extract(["https://example.com/product"])[0]

    assert direct["success"] is False
    assert native["blocked_by_policy"] is True
    assert native["content"] == ""
    assert target not in json.dumps([direct, native])


def test_missing_safety_helpers_fail_closed(tools_module, extract_response, monkeypatch):
    _, requests = extract_response
    monkeypatch.setitem(sys.modules, "tools.url_safety", None)
    result = json.loads(tools_module.extract({"url": "https://example.com"}))
    assert result["success"] is False
    assert "Update Hermes" in result["error"]
    assert requests == []


def test_query_parameters_pass_through_without_custom_policy_checks(
    tools_module, extract_response, monkeypatch,
):
    from serpapi_hermes_plugin.provider import SerpApiWebSearchProvider

    payload, requests = extract_response
    monkeypatch.setitem(sys.modules, "agent.redact", None)
    monkeypatch.setitem(sys.modules, "tools.website_policy", None)
    monkeypatch.setitem(sys.modules, "hermes_cli.config", None)
    url = (
        "https://example.com/product?token=chapter1&signature=example-signature"
        "&api_key=test-secret&q=ghp_" + "a" * 30
    )
    # Exercise both the requested URL and a returned URL with signed parameters.
    payload["page_information"]["final_url"] = url
    assert tools_module.extract({"url": url}) == payload["markdown"]
    native = SerpApiWebSearchProvider().extract([url])[0]
    assert "error" not in native
    assert native["content"] == payload["markdown"]
    assert len(requests) == 2
    assert all(request["params"]["url"] == url for request in requests)


@pytest.mark.parametrize("mode,field", [("map", "urls"), ("crawl", "pages")])
def test_site_modes_preserve_good_results_and_isolate_failures(
    tools_module, extract_response, monkeypatch, mode, field
):
    payload, requests = extract_response
    good = {"url": "https://example.com/good", "markdown": "Keep this page", "title": "Good"}
    payload.clear()
    payload.update({"search_parameters": {"engine": "extract", "mode": mode}, field: [
        good,
        {"url": "https://example.com/error", "error": "Fetch failed test-secret"},
        {"url": "https://example.com/redirect", "markdown": "Blocked page",
         "page_information": {"final_url": "http://10.0.0.1/"}},
        {"url": "file:///etc/passwd", "markdown": "Malformed page"},
        {"url": "http://10.0.0.1/", "markdown": "Private page"},
    ]})
    monkeypatch.setattr(sys.modules["tools.url_safety"], "is_safe_url",
                        lambda url: "10.0.0.1" not in url)
    options = ({"include_sitemap": False} if mode == "map" else {"max_pages": 2, "max_depth": 1})
    args = {"url": "https://example.com", "mode": mode, "include_subdomains": True, **options}

    compact = tools_module.extract(args)
    full_text = tools_module.extract({**args, "compact_mode": False})
    full = json.loads(full_text)

    assert "<https://example.com/good>" in compact
    assert "Fetch failed [redacted]" in compact
    assert "Blocked" in compact
    if mode == "crawl":
        assert "Keep this page" in compact
    assert full[field][0] == good
    assert full[field][1]["error"] == "Fetch failed [redacted]"
    assert all(entry["blocked_by_policy"] for entry in full[field][2:])
    assert all("error" in entry and "url" not in entry for entry in full[field][2:])
    for hidden in (
        "test-secret", "Blocked page", "Malformed page",
        "Private page", "10.0.0.1",
    ):
        assert hidden not in compact + full_text
    for request in requests:
        for key, value in {**options, "include_subdomains": True}.items():
            assert request["params"][key] == value
    assert "json_restrictor" not in requests[0]["params"]
    assert "json_restrictor" not in requests[1]["params"]


def test_empty_map_is_distinguished_from_an_unrelated_response(tools_module, extract_response):
    payload, _ = extract_response
    payload.clear()
    payload["search_parameters"] = {"engine": "extract", "mode": "map"}
    args = {"url": "https://example.com", "mode": "map"}
    assert tools_module.extract(args) == "No URLs found."

    payload["search_parameters"]["engine"] = "google"
    assert json.loads(tools_module.extract(args))["success"] is False
