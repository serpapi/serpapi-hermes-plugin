from __future__ import annotations

import importlib.util
import shutil
import sys
import types
from pathlib import Path
from typing import Any

import httpx
import pytest


def test_git_entry_point_uses_checkout_without_pypi_package(
    fake_hermes, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    del fake_hermes
    root = Path(__file__).resolve().parents[1]
    plugin_dir = tmp_path / "plugins" / "serpapi"
    plugin_dir.mkdir(parents=True)
    shutil.copy2(root / "__init__.py", plugin_dir / "__init__.py")
    shutil.copytree(
        root / "src" / "serpapi_hermes_plugin",
        plugin_dir / "src" / "serpapi_hermes_plugin",
        ignore=shutil.ignore_patterns("__pycache__"),
    )

    # A Git install must work even when the PyPI module is unavailable.
    monkeypatch.setitem(sys.modules, "serpapi_hermes_plugin", None)
    namespace = types.ModuleType("hermes_plugins")
    namespace.__path__ = []
    monkeypatch.setitem(sys.modules, "hermes_plugins", namespace)
    module_name = "hermes_plugins.serpapi"
    spec = importlib.util.spec_from_file_location(
        module_name, plugin_dir / "__init__.py", submodule_search_locations=[str(plugin_dir)]
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, module_name, module)
    original_path = sys.path.copy()

    class Context:
        def __init__(self) -> None:
            self.providers = []
            self.tools = {}

        def register_web_search_provider(self, provider) -> None:
            self.providers.append(provider)

        def register_tool(self, **kwargs: Any) -> None:
            assert kwargs["name"] not in self.tools
            self.tools[kwargs["name"]] = kwargs

    context = Context()
    monkeypatch.setenv("SERPAPI_API_KEY", "test-key")
    requests = []

    def fake_get(url: str, **kwargs: Any) -> httpx.Response:
        requests.append(kwargs["params"])
        return httpx.Response(
            200,
            json={"organic_results": [{"title": "Result", "link": "https://example.com"}]},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", fake_get)
    try:
        spec.loader.exec_module(module)
        module.register(context)

        assert len(context.providers) == 1
        provider = context.providers[0]
        assert provider.name == "serpapi"
        assert provider.search("test")["data"]["web"][0]["url"] == "https://example.com"
        assert requests[0]["engine"] == "google_light"
        assert len(context.tools) == 6
        assert all(tool["check_fn"]() for tool in context.tools.values())
        assert all(
            tool["handler"].__module__.startswith(f"{module_name}.src.serpapi_hermes_plugin.")
            for tool in context.tools.values()
        )
        assert sys.path == original_path
    finally:
        for name in list(sys.modules):
            if name.startswith(f"{module_name}."):
                sys.modules.pop(name)
