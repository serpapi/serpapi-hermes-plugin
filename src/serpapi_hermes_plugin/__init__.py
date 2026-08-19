"""SerpApi web, Maps, News, Shopping, Hotels, Flights, and Travel Explore for Hermes Agent."""

from __future__ import annotations

from .provider import SerpApiWebSearchProvider
from .schemas import (
    FLIGHTS_SEARCH_SCHEMA,
    HOTELS_SEARCH_SCHEMA,
    MAPS_SEARCH_SCHEMA,
    NEWS_SEARCH_SCHEMA,
    SHOPPING_SEARCH_SCHEMA,
    TRAVEL_EXPLORE_SEARCH_SCHEMA,
)
from .tools import (
    flights_search,
    hotels_search,
    maps_search,
    news_search,
    shopping_search,
    travel_explore_search,
)

__all__ = ["SerpApiWebSearchProvider", "register"]


def register(ctx) -> None:
    """Register SerpApi's web provider and specialized search tools."""
    provider = SerpApiWebSearchProvider()
    ctx.register_web_search_provider(provider)

    for schema, handler in (
        (MAPS_SEARCH_SCHEMA, maps_search),
        (NEWS_SEARCH_SCHEMA, news_search),
        (SHOPPING_SEARCH_SCHEMA, shopping_search),
        (HOTELS_SEARCH_SCHEMA, hotels_search),
        (FLIGHTS_SEARCH_SCHEMA, flights_search),
        (TRAVEL_EXPLORE_SEARCH_SCHEMA, travel_explore_search),
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
