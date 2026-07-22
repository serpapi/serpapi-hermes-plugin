from __future__ import annotations

import importlib
import os
import sys
import types

import pytest


@pytest.fixture
def fake_hermes(monkeypatch: pytest.MonkeyPatch):
    """Install a minimal stand-in for Hermes's public web-provider module."""
    for module_name in list(sys.modules):
        if module_name == "serpapi_hermes_plugin" or module_name.startswith(
            "serpapi_hermes_plugin."
        ):
            sys.modules.pop(module_name)

    agent_module = types.ModuleType("agent")
    web_search_provider_module = types.ModuleType("agent.web_search_provider")

    class WebSearchProvider:
        pass

    def get_provider_env(name: str) -> str:
        return os.getenv(name, "").strip()

    web_search_provider_module.WebSearchProvider = WebSearchProvider
    web_search_provider_module.get_provider_env = get_provider_env
    agent_module.web_search_provider = web_search_provider_module
    monkeypatch.setitem(sys.modules, "agent", agent_module)
    monkeypatch.setitem(sys.modules, "agent.web_search_provider", web_search_provider_module)
    return WebSearchProvider


@pytest.fixture
def provider_module(fake_hermes):
    del fake_hermes
    return importlib.import_module("serpapi_hermes_plugin.provider")


@pytest.fixture
def tools_module(fake_hermes):
    del fake_hermes
    return importlib.import_module("serpapi_hermes_plugin.tools")
