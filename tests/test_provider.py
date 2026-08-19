from __future__ import annotations

import importlib
import importlib.metadata
from typing import Any

import httpx
import pytest


def _response(status_code: int, payload: Any) -> httpx.Response:
    request = httpx.Request("GET", "https://serpapi.com/search")
    return httpx.Response(status_code, json=payload, request=request)


def test_provider_metadata_and_capabilities(provider_module) -> None:
    provider = provider_module.SerpApiWebSearchProvider()

    assert provider.name == "serpapi"
    assert provider.display_name == "SerpApi"
    assert provider.supports_search() is True
    assert provider.supports_extract() is False
    assert provider.get_setup_schema()["env_vars"][0]["key"] == "SERPAPI_API_KEY"


def test_availability_uses_api_key(provider_module, monkeypatch: pytest.MonkeyPatch) -> None:
    provider = provider_module.SerpApiWebSearchProvider()

    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    assert provider.is_available() is False
    monkeypatch.setenv("SERPAPI_API_KEY", "test-key")
    assert provider.is_available() is True


def test_missing_api_key_returns_hermes_error_envelope(
    provider_module, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)

    result = provider_module.SerpApiWebSearchProvider().search("Hermes Agent")

    assert result["success"] is False
    assert "SERPAPI_API_KEY" in result["error"]


def test_search_maps_google_light_results(provider_module, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "test-key")
    captured: dict[str, Any] = {}

    def fake_get(url: str, **kwargs: Any) -> httpx.Response:
        captured["url"] = url
        captured.update(kwargs)
        return _response(
            200,
            {
                "organic_results": [
                    {"title": "One", "link": "https://example.com/1", "snippet": "First"},
                    {"title": "Two", "link": "https://example.com/2", "snippet": "Second"},
                    {"title": "Three", "link": "https://example.com/3", "snippet": "Third"},
                ]
            },
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    result = provider_module.SerpApiWebSearchProvider().search("Hermes Agent", limit=2)

    assert result == {
        "success": True,
        "data": {
            "web": [
                {
                    "title": "One",
                    "url": "https://example.com/1",
                    "description": "First",
                    "position": 1,
                },
                {
                    "title": "Two",
                    "url": "https://example.com/2",
                    "description": "Second",
                    "position": 2,
                },
            ]
        },
    }
    assert captured["url"] == "https://serpapi.com/search"
    assert captured["params"] == {
        "engine": "google_light",
        "q": "Hermes Agent",
        "num": 2,
        "api_key": "test-key",
        "output": "json",
    }


@pytest.mark.parametrize(
    ("status", "message"),
    [
        (401, "rejected the API key"),
        (429, "quota exhausted"),
        (503, "upstream error"),
    ],
)
def test_search_returns_safe_http_errors(
    provider_module,
    monkeypatch: pytest.MonkeyPatch,
    status: int,
    message: str,
) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "secret-key")
    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: _response(status, {}))

    result = provider_module.SerpApiWebSearchProvider().search("test")

    assert result["success"] is False
    assert message in result["error"]
    assert "secret-key" not in result["error"]


def test_api_error_redacts_key(provider_module, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "secret-key")
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: _response(200, {"error": "Invalid secret-key"}),
    )

    result = provider_module.SerpApiWebSearchProvider().search("test")

    assert result == {"success": False, "error": "Invalid [redacted]"}


def test_request_error_does_not_expose_key(
    provider_module, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "secret-key")

    def fail_request(*args: Any, **kwargs: Any) -> httpx.Response:
        request = httpx.Request("GET", "https://serpapi.com/search.json?api_key=secret-key")
        raise httpx.ConnectError("connection failed", request=request)

    monkeypatch.setattr(httpx, "get", fail_request)

    result = provider_module.SerpApiWebSearchProvider().search("test")

    assert result["success"] is False
    assert "secret-key" not in result["error"]


def test_register_adds_provider_and_specialized_tools(provider_module) -> None:
    plugin_module = importlib.import_module("serpapi_hermes_plugin")

    class Context:
        def __init__(self) -> None:
            self.providers = []
            self.tools = []

        def register_web_search_provider(self, provider) -> None:
            self.providers.append(provider)

        def register_tool(self, **kwargs: Any) -> None:
            self.tools.append(kwargs)

    context = Context()

    plugin_module.register(context)

    assert len(context.providers) == 1
    assert isinstance(context.providers[0], provider_module.SerpApiWebSearchProvider)
    assert [tool["name"] for tool in context.tools] == [
        "serpapi_maps_search",
        "serpapi_news_search",
        "serpapi_shopping_search",
        "serpapi_hotels_search",
        "serpapi_flights_search",
        "serpapi_travel_explore_search",
    ]
    assert all(tool["toolset"] == "serpapi" for tool in context.tools)
    assert all(tool["requires_env"] == ["SERPAPI_API_KEY"] for tool in context.tools)

    tools_by_name = {tool["name"]: tool for tool in context.tools}
    hotel_properties = tools_by_name["serpapi_hotels_search"]["schema"]["parameters"]["properties"]
    assert hotel_properties["children_ages"]["items"] == {
        "type": "integer",
        "minimum": 1,
        "maximum": 17,
    }

    for tool_name in ("serpapi_flights_search", "serpapi_travel_explore_search"):
        properties = tools_by_name[tool_name]["schema"]["parameters"]["properties"]
        assert {"infants_in_seat", "infants_on_lap"} <= properties.keys()


def test_package_declares_hermes_entry_point(provider_module) -> None:
    entry_points = importlib.metadata.entry_points().select(group="hermes_agent.plugins")
    entry_point = next(ep for ep in entry_points if ep.name == "serpapi")

    assert entry_point.value == "serpapi_hermes_plugin"
    assert callable(entry_point.load().register)
