from __future__ import annotations

import json
from typing import Any

import httpx
import pytest


@pytest.fixture
def extract_response(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SERPAPI_API_KEY", "test-secret")
    requests = []
    payload = {
        "page_information": {
            "title": "A product",
            "url": "https://example.com/product",
            "final_url": "https://example.com/product/",
        },
        "text_content": {"markdown": "# Product\n\nCosts **$20**.", "full": "Product Costs $20."},
        "price_offers": [{"price": "$20"}],
        "meta_tags": {"description": "A product"},
        "sections": [{"text": "Product details"}],
    }

    def fake_get(url: str, **kwargs: Any) -> httpx.Response:
        requests.append({"url": url, **kwargs})
        return httpx.Response(200, json=payload, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)
    return payload, requests


def test_compact_tool_returns_main_markdown_and_filters_upstream(tools_module, extract_response):
    payload, requests = extract_response

    result = tools_module.extract({"url": "https://example.com/product"})

    assert result == payload["text_content"]["markdown"]
    request = requests[0]
    assert request["url"] == "https://serpapi.com/search"
    assert request["params"] == {
        "url": "https://example.com/product",
        "engine": "extract",
        "mode": "scrape",
        "include_markdown": "true",
        "json_restrictor": "page_information,text_content,error",
        "output": "json",
        "api_key": "test-secret",
    }
    assert request["timeout"] == 60
    assert request["headers"]["Accept"] == "application/json"


def test_full_tool_preserves_structured_fields_and_passes_css_filters(
    tools_module, extract_response
):
    payload, requests = extract_response
    payload["debug"] = "test-secret"

    result = json.loads(tools_module.extract({
        "url": "https://example.com/product",
        "compact_mode": False,
        "include_tags": "main,article",
        "exclude_tags": "nav,footer",
    }))

    assert result == {**payload, "debug": "[redacted]"}
    params = requests[0]["params"]
    assert "json_restrictor" not in params
    assert params["include_tags"] == "main,article"
    assert params["exclude_tags"] == "nav,footer"
    assert "compact_mode" not in params


@pytest.mark.parametrize("markdown", [None, "", "  ", ["invalid"]])
def test_missing_markdown_falls_back_to_complete_text(tools_module, extract_response, markdown):
    payload, _ = extract_response
    payload["text_content"]["markdown"] = markdown
    payload["text_content"]["excerpt"] = "Truncated"

    assert tools_module.extract({"url": "https://example.com"}) == "Product Costs $20."


@pytest.mark.parametrize("text_content", [None, [], {}, {"excerpt": "Only a short excerpt"}])
def test_missing_page_content_is_an_error(tools_module, extract_response, text_content):
    payload, _ = extract_response
    payload["text_content"] = text_content

    result = json.loads(tools_module.extract({"url": "https://example.com"}))

    assert result["success"] is False
    assert "no page content" in result["error"]


@pytest.mark.parametrize("args", [
    {},
    {"url": "file:///etc/passwd"},
    {"url": "example.com"},
    {"url": "https://"},
    {"url": "https://[bad"},
    {"url": "https://example.com:invalid"},
    {"url": "https://☃.example"},
    {"url": "https://example.com/\u0000"},
    {"url": "https://user:password@example.com"},
    {"url": ["https://example.com"]},
    {"url": "https://example.com", "compact_mode": "false"},
    {"url": "https://example.com", "include_tags": ["main"]},
])
def test_invalid_inputs_fail_without_request(tools_module, extract_response, args):
    _, requests = extract_response

    assert json.loads(tools_module.extract(args))["success"] is False
    assert requests == []


def test_provider_returns_hermes_documents_and_ignores_unknown_kwargs(
    provider_module, extract_response
):
    payload, _ = extract_response

    results = provider_module.SerpApiWebSearchProvider().extract(
        ["https://example.com/product"], format="text", unknown_option=True
    )

    assert results == [{
        "url": "https://example.com/product",
        "title": "A product",
        "content": "Product Costs $20.",
        "raw_content": "Product Costs $20.",
        "metadata": {**payload["page_information"], "sourceURL": "https://example.com/product"},
    }]


def test_batch_runs_concurrently_and_preserves_order_and_errors(
    provider_module, monkeypatch: pytest.MonkeyPatch
):
    from threading import Barrier

    barrier = Barrier(3)
    monkeypatch.setenv("SERPAPI_API_KEY", "test-secret")

    def fake_get(url: str, **kwargs: Any) -> httpx.Response:
        target = kwargs["params"]["url"]
        barrier.wait(timeout=5)
        request = httpx.Request("GET", url)
        if target.endswith("/error"):
            return httpx.Response(400, json={"error": "Cannot fetch test-secret"}, request=request)
        if target.endswith("/timeout"):
            raise httpx.ReadTimeout("test-secret", request=request)
        return httpx.Response(200, json={"text_content": {"markdown": "A page"}}, request=request)

    monkeypatch.setattr(httpx, "get", fake_get)
    urls = ["https://example.com/error", "https://example.com/good", "https://example.com/timeout"]

    results = provider_module.SerpApiWebSearchProvider().extract(urls, format="markdown")

    assert [result["url"] for result in results] == urls
    assert results[0]["error"] == "Cannot fetch [redacted]"
    assert results[1]["content"] == "A page"
    assert "error" not in results[1]
    assert results[2]["error"] == "Could not reach SerpApi; try again shortly"
    assert "test-secret" not in json.dumps(results)


def test_empty_batch_does_not_request(provider_module, extract_response):
    _, requests = extract_response
    assert provider_module.SerpApiWebSearchProvider().extract([]) == []
    assert requests == []


def test_batch_preserves_profile_scoped_credentials(
    provider_module, extract_response, monkeypatch: pytest.MonkeyPatch
):
    from contextvars import ContextVar

    from agent import web_search_provider

    profile_key = ContextVar("profile_key", default="")
    monkeypatch.setattr(web_search_provider, "get_provider_env", lambda name: profile_key.get())
    token = profile_key.set("profile-secret")
    _, requests = extract_response
    try:
        results = provider_module.SerpApiWebSearchProvider().extract(
            ["https://example.com/one", "https://example.com/two"]
        )
    finally:
        profile_key.reset(token)

    assert all("error" not in result for result in results)
    assert len(requests) == 2
    assert all(request["params"]["api_key"] == "profile-secret" for request in requests)


def test_missing_key_returns_per_url_errors(provider_module, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    results = provider_module.SerpApiWebSearchProvider().extract(["https://example.com"])
    assert len(results) == 1
    assert "SERPAPI_API_KEY" in results[0]["error"]


@pytest.mark.parametrize("token", ["sk-" + "a" * 30, "%73%6b%2d" + "a" * 30])
def test_secret_url_is_blocked_before_request(tools_module, extract_response, token):
    _, requests = extract_response

    result = json.loads(tools_module.extract({"url": f"https://example.com/?token={token}"}))

    assert result["success"] is False
    assert "API key or token" in result["error"]
    assert token not in result["error"]
    assert requests == []


def test_website_policy_blocks_both_extraction_paths(
    tools_module, provider_module, extract_response, monkeypatch: pytest.MonkeyPatch
):
    import sys

    _, requests = extract_response
    monkeypatch.setattr(
        sys.modules["tools.website_policy"], "check_website_access", lambda url: {"blocked": True}
    )

    direct = json.loads(tools_module.extract({"url": "https://example.com"}))
    native = provider_module.SerpApiWebSearchProvider().extract(["https://example.com"])

    assert direct["error"] == native[0]["error"] == "Blocked by website policy"
    assert native[0]["blocked_by_policy"] is True
    assert requests == []


def test_missing_safety_helpers_fail_closed(tools_module, extract_response, monkeypatch):
    import sys

    _, requests = extract_response
    monkeypatch.setitem(sys.modules, "tools.website_policy", None)

    result = json.loads(tools_module.extract({"url": "https://example.com"}))

    assert result["success"] is False
    assert "Update Hermes" in result["error"]
    assert requests == []


@pytest.mark.parametrize("field", ["url", "final_url"])
@pytest.mark.parametrize("compact_mode", [True, False])
def test_redirect_to_blocked_domain_never_returns_content(
    tools_module, provider_module, extract_response, monkeypatch, field, compact_mode
):
    import sys

    payload, _ = extract_response
    payload["page_information"][field] = "https://blocked.example/page"
    monkeypatch.setattr(
        sys.modules["tools.website_policy"],
        "check_website_access",
        lambda url: {"blocked": True} if "blocked.example" in url else None,
    )

    direct = json.loads(tools_module.extract({
        "url": "https://example.com/product", "compact_mode": compact_mode,
    }))
    native = provider_module.SerpApiWebSearchProvider().extract(["https://example.com/product"])

    assert direct["error"] == native[0]["error"] == "Blocked by website policy"
    assert native[0]["blocked_by_policy"] is True
    assert "content" not in direct
    assert native[0]["content"] == ""
