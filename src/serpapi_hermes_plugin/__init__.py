"""SerpApi web, Maps, News, and Shopping search for Hermes Agent."""

from __future__ import annotations

from .provider import SerpApiWebSearchProvider
from .schemas import MAPS_SEARCH_SCHEMA, NEWS_SEARCH_SCHEMA, SHOPPING_SEARCH_SCHEMA
from .tools import maps_search, news_search, shopping_search

__all__ = ["SerpApiWebSearchProvider", "register"]


def register(ctx) -> None:
    """Register SerpApi's web provider and specialized search tools."""
    provider = SerpApiWebSearchProvider()
    ctx.register_web_search_provider(provider)

    for schema, handler in (
        (MAPS_SEARCH_SCHEMA, maps_search),
        (NEWS_SEARCH_SCHEMA, news_search),
        (SHOPPING_SEARCH_SCHEMA, shopping_search),
    ):
        ctx.register_tool(
            name=schema["name"],
            toolset="serpapi",
            schema=schema,
            handler=handler,
            check_fn=provider.is_available,
            requires_env=["SERPAPI_API_KEY"],
            description=schema["description"],
        )
