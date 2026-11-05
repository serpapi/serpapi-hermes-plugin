from __future__ import annotations

from typing import Any

import httpx
import pytest


def test_call_serpapi_defaults_to_markdown(
    client_module, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "test-key")
    captured: dict[str, Any] = {}

    def fake_get(url: str, **kwargs: Any) -> httpx.Response:
        captured["url"] = url
        captured.update(kwargs)
        request = httpx.Request("GET", url)
        return httpx.Response(
            200,
            text="---\nsearch: coffee\nkey: test-key\n---\n\n## Results\n",
            headers={"content-type": "text/markdown; charset=utf-8"},
            request=request,
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    result = client_module.call_serpapi("google_light", {"q": "coffee"})

    assert result == "---\nsearch: coffee\nkey: [redacted]\n---\n\n## Results"
    assert captured["url"] == "https://serpapi.com/search"
    assert captured["params"] == {
        "q": "coffee",
        "engine": "google_light",
        "api_key": "test-key",
        "output": "md",
    }
    assert captured["headers"]["Accept"] == "text/markdown"


def test_call_serpapi_allows_json_override(
    client_module, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "test-key")
    captured: dict[str, Any] = {}

    def fake_get(url: str, **kwargs: Any) -> httpx.Response:
        captured.update(kwargs)
        request = httpx.Request("GET", url)
        return httpx.Response(
            200,
            json={"organic_results": [], "debug_url": "https://example.com/?key=test-key"},
            request=request,
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    result = client_module.call_serpapi(
        "google_light",
        {"q": "coffee", "output": "json"},
    )

    assert result == {
        "organic_results": [],
        "debug_url": "https://example.com/?key=[redacted]",
    }
    assert captured["params"]["output"] == "json"
    assert captured["headers"]["Accept"] == "application/json"


def test_markdown_api_error_is_safe(client_module, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "secret-key")

    def fake_get(url: str, **kwargs: Any) -> httpx.Response:
        del kwargs
        request = httpx.Request("GET", url)
        return httpx.Response(
            200,
            json={"error": "Invalid secret-key"},
            request=request,
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(client_module.SerpApiError, match=r"Invalid \[redacted\]"):
        client_module.call_serpapi("google_light", {"q": "coffee"})


def test_http_400_returns_safe_api_error(client_module, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "secret-key")

    def fake_get(url: str, **kwargs: Any) -> httpx.Response:
        del kwargs
        request = httpx.Request("GET", url)
        return httpx.Response(
            400,
            json={"error": "Invalid children_ages for secret-key"},
            request=request,
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(
        client_module.SerpApiError,
        match=r"Invalid children_ages for \[redacted\]",
    ):
        client_module.call_serpapi("google_hotels", {"q": "Bali", "output": "md"})


def test_http_400_without_json_uses_generic_error(
    client_module, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "secret-key")

    def fake_get(url: str, **kwargs: Any) -> httpx.Response:
        del kwargs
        request = httpx.Request("GET", url)
        return httpx.Response(400, text="Bad request", request=request)

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(client_module.SerpApiError, match=r"request failed \(HTTP 400\)"):
        client_module.call_serpapi("google_hotels", {"q": "Bali", "output": "md"})


def test_http_200_markdown_error_is_bounded_and_redacted(client_module, monkeypatch):
    monkeypatch.setenv("SERPAPI_API_KEY", "secret-key")
    message = "No results for secret-key " + "x" * 600
    body = "---\nsearch_metadata:\n  status: Success\n---\n\n## Error\n\n" + message
    body += "\n\n## Pagination\n\nUnrelated next section"
    body = "\ufeff" + body.replace("\n", "\r\n")
    monkeypatch.setattr(httpx, "get", lambda url, **kw: httpx.Response(
        200, text=body, headers={"content-type": "text/markdown"},
        request=httpx.Request("GET", url),
    ))

    with pytest.raises(client_module.SerpApiError) as error:
        client_module.call_serpapi("google_news_light", {"q": "no results"})

    assert str(error.value) == message.replace("secret-key", "[redacted]")[:500]


@pytest.mark.parametrize("engine, body", [
    ("extract", "---\ntitle: Error handling\n---\n\n## Error\n\nAn article about errors."),
    ("google_news_light", "---\nengine: google_news_light\n---\n\n"
     "## News Results\n\n| Title |\n| --- |\n| Error |\n\n```\n## Error\n```"),
])
def test_markdown_content_is_not_mistaken_for_an_api_error(
    client_module, monkeypatch, engine, body
):
    monkeypatch.setenv("SERPAPI_API_KEY", "secret-key")
    monkeypatch.setattr(httpx, "get", lambda url, **kw: httpx.Response(
        200, text=body, headers={"content-type": "text/markdown"},
        request=httpx.Request("GET", url),
    ))

    assert client_module.call_serpapi(engine, {"output": "md"}) == body
