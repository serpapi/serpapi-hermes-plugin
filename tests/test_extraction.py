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
    assert ("json_restrictor" in params) is compact_mode
    assert "compact_mode" not in params


def test_missing_markdown_is_not_replaced_by_a_truncated_excerpt(tools_module, extract_response):
    payload, _ = extract_response
    del payload["markdown"]
    payload["text_content"] = {"excerpt": "A truncated legacy excerpt"}
    result = json.loads(tools_module.extract({"url": "https://example.com"}))
    assert result["success"] is False
    assert "no page content" in result["error"]


@pytest.mark.parametrize("args", [
    {"url": "https://user:password@example.com"},
    {"url": "file:///etc/passwd"},
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


@pytest.mark.parametrize("target", [
    "https://example.com/?token=%73%6b%2d" + "a" * 30,
    "https://blocked.example/",
])
def test_blocked_seed_never_reaches_serpapi(
    tools_module, provider_module, extract_response, monkeypatch, target
):
    _, requests = extract_response
    monkeypatch.setattr(sys.modules["tools.website_policy"], "check_website_access",
                        lambda url: {"blocked": True} if "blocked.example" in url else None)

    direct = json.loads(tools_module.extract({"url": target}))
    native = provider_module.SerpApiWebSearchProvider().extract([target])[0]

    assert direct["success"] is False
    assert native["blocked_by_policy"] is True
    assert native["content"] == ""
    assert target not in direct["error"]
    assert requests == []


@pytest.mark.parametrize("compact_mode,target", [
    (True, "https://example.com/?token=sk-" + "a" * 30),
    (False, "https://blocked.example/"),
])
def test_blocked_redirect_never_returns_content(
    tools_module, provider_module, extract_response, monkeypatch, compact_mode, target
):
    payload, _ = extract_response
    payload["page_information"]["final_url"] = target
    monkeypatch.setattr(sys.modules["tools.website_policy"], "check_website_access",
                        lambda url: {"blocked": True} if "blocked.example" in url else None)

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
    monkeypatch.setitem(sys.modules, "tools.website_policy", None)
    result = json.loads(tools_module.extract({"url": "https://example.com"}))
    assert result["success"] is False
    assert "Update Hermes" in result["error"]
    assert requests == []


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
         "page_information": {"final_url": "https://blocked.example/"}},
        {"url": "https://example.com/?sk-" + "a" * 30, "markdown": "Secret page"},
        {"url": "file:///etc/passwd", "markdown": "Malformed page"},
    ]})
    monkeypatch.setattr(sys.modules["tools.website_policy"], "check_website_access",
                        lambda url: {"blocked": True} if "blocked.example" in url else None)
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
    assert all(entry["blocked_by_policy"] for entry in full[field][2:4])
    assert all("error" in entry and "url" not in entry for entry in full[field][2:])
    for hidden in (
        "test-secret", "Blocked page", "Secret page", "Malformed page", "sk-", "blocked.example",
    ):
        assert hidden not in compact + full_text
    for request in requests:
        for key, value in {**options, "include_subdomains": True}.items():
            assert request["params"][key] == value
    assert "json_restrictor" in requests[0]["params"]
    assert "json_restrictor" not in requests[1]["params"]


def test_empty_map_is_distinguished_from_an_unrelated_response(tools_module, extract_response):
    payload, _ = extract_response
    payload.clear()
    payload["search_parameters"] = {"engine": "extract", "mode": "map"}
    args = {"url": "https://example.com", "mode": "map"}
    assert tools_module.extract(args) == "No URLs found."

    payload["search_parameters"]["engine"] = "google"
    assert json.loads(tools_module.extract(args))["success"] is False
