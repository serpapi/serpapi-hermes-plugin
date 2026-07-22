"""Hermes tool schemas for SerpApi's specialized search engines."""

from __future__ import annotations

MAPS_SEARCH_SCHEMA = {
    "name": "serpapi_maps_search",
    "description": (
        "Search Google Maps through SerpApi for places, local businesses, restaurants, "
        "shops, attractions, and services. Use this instead of web_search when the user "
        "wants physical places, ratings, addresses, opening status, or coordinates."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Place or business search, such as 'coffee shops' or 'museums'.",
            },
            "location": {
                "type": "string",
                "description": "Optional search origin, such as 'New York, NY' or '560001'.",
            },
            "latitude": {
                "type": "number",
                "minimum": -90,
                "maximum": 90,
                "description": "Optional precise search-origin latitude; requires longitude.",
            },
            "longitude": {
                "type": "number",
                "minimum": -180,
                "maximum": 180,
                "description": "Optional precise search-origin longitude; requires latitude.",
            },
            "zoom": {
                "type": "integer",
                "minimum": 3,
                "maximum": 30,
                "default": 14,
                "description": "Map zoom when a location or coordinates are supplied.",
            },
            "nearby": {
                "type": "boolean",
                "default": False,
                "description": "Prioritize results close to the supplied search origin.",
            },
            "language": {
                "type": "string",
                "description": "Optional two-letter language code, such as 'en' or 'es'.",
            },
            "country": {
                "type": "string",
                "description": "Optional two-letter country code, such as 'us' or 'in'.",
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 20,
                "default": 5,
                "description": "Maximum number of places to return.",
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    },
}

NEWS_SEARCH_SCHEMA = {
    "name": "serpapi_news_search",
    "description": (
        "Search recent Google News results through SerpApi. Use this for current events, "
        "breaking news, recent reporting, and coverage from news publications."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "News search query.",
            },
            "location": {
                "type": "string",
                "description": "Optional city-level origin for geographically relevant news.",
            },
            "language": {
                "type": "string",
                "description": "Optional two-letter language code, such as 'en' or 'fr'.",
            },
            "country": {
                "type": "string",
                "description": "Optional two-letter country code, such as 'us' or 'in'.",
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 20,
                "default": 5,
                "description": "Maximum number of news results to return.",
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    },
}

SHOPPING_SEARCH_SCHEMA = {
    "name": "serpapi_shopping_search",
    "description": (
        "Search Google Shopping through SerpApi for products, merchants, prices, ratings, "
        "and delivery information. Use this for shopping and product-comparison requests."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Product search query.",
            },
            "location": {
                "type": "string",
                "description": "Optional city-level origin for local prices and availability.",
            },
            "language": {
                "type": "string",
                "description": "Optional two-letter language code, such as 'en' or 'de'.",
            },
            "country": {
                "type": "string",
                "description": "Optional two-letter country code, such as 'us' or 'in'.",
            },
            "minimum_price": {
                "type": "number",
                "minimum": 0,
                "description": "Optional minimum product price in the selected market currency.",
            },
            "maximum_price": {
                "type": "number",
                "minimum": 0,
                "description": "Optional maximum product price in the selected market currency.",
            },
            "sort": {
                "type": "string",
                "enum": ["relevance", "price_low_to_high", "price_high_to_low"],
                "default": "relevance",
                "description": "How to order products.",
            },
            "free_shipping": {
                "type": "boolean",
                "default": False,
                "description": "Return only products offering free shipping.",
            },
            "on_sale": {
                "type": "boolean",
                "default": False,
                "description": "Return only products currently on sale.",
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 20,
                "default": 5,
                "description": "Maximum number of products to return.",
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    },
}
