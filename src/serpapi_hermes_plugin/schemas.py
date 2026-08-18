"""Hermes tool schemas for SerpApi's specialized search engines."""

from __future__ import annotations

_OUTPUT_PROPERTY = {
    "type": "string",
    "enum": ["md", "json"],
    "default": "md",
    "description": (
        "Response format. Markdown is the default and is optimized for Hermes. "
        "Use JSON only when structured data is required."
    ),
}

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
                "description": "Maximum number of places to return when output is JSON.",
            },
            "output": _OUTPUT_PROPERTY,
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
                "description": "Maximum number of news results to return when output is JSON.",
            },
            "output": _OUTPUT_PROPERTY,
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
                "description": "Maximum number of products to return when output is JSON.",
            },
            "output": _OUTPUT_PROPERTY,
        },
        "required": ["query"],
        "additionalProperties": False,
    },
}

HOTELS_SEARCH_SCHEMA = {
    "name": "serpapi_hotels_search",
    "description": (
        "Search Google Hotels through SerpApi for hotels, vacation rentals, nightly rates, "
        "ratings, amenities, and booking options. Use this for stays with known check-in and "
        "check-out dates."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Destination, neighborhood, landmark, or property name.",
            },
            "check_in_date": {
                "type": "string",
                "format": "date",
                "description": "Check-in date in YYYY-MM-DD format.",
            },
            "check_out_date": {
                "type": "string",
                "format": "date",
                "description": "Check-out date in YYYY-MM-DD format, after check_in_date.",
            },
            "adults": {
                "type": "integer",
                "minimum": 1,
                "maximum": 9,
                "default": 2,
                "description": "Number of adult guests.",
            },
            "children": {
                "type": "integer",
                "minimum": 0,
                "maximum": 9,
                "default": 0,
                "description": "Number of child guests.",
            },
            "currency": {
                "type": "string",
                "description": "Optional three-letter currency code, such as USD or EUR.",
            },
            "language": {
                "type": "string",
                "description": "Optional two-letter language code, such as 'en' or 'fr'.",
            },
            "country": {
                "type": "string",
                "description": "Optional two-letter market country code, such as 'us' or 'in'.",
            },
            "minimum_price": {
                "type": "number",
                "minimum": 0,
                "description": "Optional minimum nightly price in the selected currency.",
            },
            "maximum_price": {
                "type": "number",
                "minimum": 0,
                "description": "Optional maximum nightly price in the selected currency.",
            },
            "hotel_class": {
                "type": "integer",
                "enum": [2, 3, 4, 5],
                "description": "Optional hotel star class.",
            },
            "sort": {
                "type": "string",
                "enum": ["relevance", "lowest_price", "highest_rating", "most_reviewed"],
                "default": "relevance",
                "description": "How to order properties.",
            },
            "vacation_rentals": {
                "type": "boolean",
                "default": False,
                "description": "Search vacation rentals instead of hotels.",
            },
            "output": _OUTPUT_PROPERTY,
        },
        "required": ["query", "check_in_date", "check_out_date"],
        "additionalProperties": False,
    },
}

FLIGHTS_SEARCH_SCHEMA = {
    "name": "serpapi_flights_search",
    "description": (
        "Search Google Flights through SerpApi for one-way and round-trip fares. Airport IDs "
        "must be individual three-letter airport codes or location KGMIDs. For a round trip, "
        "use a returned departure_token in a follow-up call to retrieve return-flight choices."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "departure_id": {
                "type": "string",
                "description": (
                    "Uppercase airport code such as LHR or a /m/ or /g/ location KGMID. "
                    "Comma-separated IDs are supported; city codes such as LON are unsupported."
                ),
            },
            "arrival_id": {
                "type": "string",
                "description": (
                    "Uppercase airport code such as CDG or a /m/ or /g/ location KGMID. "
                    "Comma-separated IDs are supported; city codes such as PAR are unsupported."
                ),
            },
            "outbound_date": {
                "type": "string",
                "format": "date",
                "description": "Outbound date in YYYY-MM-DD format.",
            },
            "return_date": {
                "type": "string",
                "format": "date",
                "description": "Return date for a round trip in YYYY-MM-DD format.",
            },
            "trip_type": {
                "type": "string",
                "enum": ["one_way", "round_trip"],
                "description": "Optional; inferred from whether return_date is present.",
            },
            "travel_class": {
                "type": "string",
                "enum": ["economy", "premium_economy", "business", "first"],
                "default": "economy",
                "description": "Cabin class.",
            },
            "adults": {
                "type": "integer",
                "minimum": 1,
                "maximum": 9,
                "default": 1,
                "description": "Number of adult passengers.",
            },
            "children": {
                "type": "integer",
                "minimum": 0,
                "maximum": 9,
                "default": 0,
                "description": "Number of child passengers.",
            },
            "currency": {
                "type": "string",
                "description": "Optional three-letter currency code, such as USD or EUR.",
            },
            "language": {
                "type": "string",
                "description": "Optional two-letter language code, such as 'en' or 'fr'.",
            },
            "country": {
                "type": "string",
                "description": "Optional two-letter market country code, such as 'us' or 'in'.",
            },
            "stops": {
                "type": "string",
                "enum": ["any", "nonstop", "one_or_fewer", "two_or_fewer"],
                "default": "any",
                "description": "Maximum number of stops.",
            },
            "sort": {
                "type": "string",
                "enum": [
                    "top_flights",
                    "price",
                    "departure_time",
                    "arrival_time",
                    "duration",
                    "emissions",
                ],
                "default": "top_flights",
                "description": "How to order itineraries.",
            },
            "maximum_price": {
                "type": "number",
                "minimum": 0,
                "description": "Optional maximum ticket price in the selected currency.",
            },
            "deep_search": {
                "type": "boolean",
                "default": False,
                "description": "Match Google Flights more closely at the cost of extra latency.",
            },
            "departure_token": {
                "type": "string",
                "description": "Token from a selected outbound itinerary for return choices.",
            },
            "output": _OUTPUT_PROPERTY,
        },
        "required": ["departure_id", "arrival_id", "outbound_date"],
        "additionalProperties": False,
    },
}

TRAVEL_EXPLORE_SEARCH_SCHEMA = {
    "name": "serpapi_travel_explore_search",
    "description": (
        "Explore destinations and flexible trip prices through SerpApi's Google Travel Explore. "
        "Use this when the traveler knows where they are leaving from but wants destination or "
        "date ideas; use serpapi_flights_search for a fixed route and dates."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "departure_id": {
                "type": "string",
                "description": (
                    "Uppercase airport code or city /m/ or /g/ KGMID. Comma-separated IDs are "
                    "supported."
                ),
            },
            "arrival_id": {
                "type": "string",
                "description": "Optional destination airport code or city /m/ or /g/ KGMID.",
            },
            "arrival_area_id": {
                "type": "string",
                "description": (
                    "Optional region or country /m/ or /g/ KGMID. Do not combine with arrival_id."
                ),
            },
            "outbound_date": {
                "type": "string",
                "format": "date",
                "description": "Optional fixed outbound date in YYYY-MM-DD format.",
            },
            "return_date": {
                "type": "string",
                "format": "date",
                "description": "Optional fixed return date in YYYY-MM-DD format.",
            },
            "trip_type": {
                "type": "string",
                "enum": ["one_way", "round_trip"],
                "description": "Optional; inferred from whether a fixed return_date is present.",
            },
            "month": {
                "type": "integer",
                "minimum": 0,
                "maximum": 12,
                "description": (
                    "Flexible travel month from 1 to 12; 0 searches the next six months."
                ),
            },
            "travel_duration": {
                "type": "string",
                "enum": ["weekend", "one_week", "two_weeks"],
                "default": "one_week",
                "description": "Trip length for flexible-date exploration.",
            },
            "travel_class": {
                "type": "string",
                "enum": ["economy", "premium_economy", "business", "first"],
                "default": "economy",
                "description": "Cabin class.",
            },
            "adults": {
                "type": "integer",
                "minimum": 1,
                "maximum": 9,
                "default": 1,
                "description": "Number of adult travelers.",
            },
            "children": {
                "type": "integer",
                "minimum": 0,
                "maximum": 9,
                "default": 0,
                "description": "Number of child travelers.",
            },
            "currency": {
                "type": "string",
                "description": "Optional three-letter currency code, such as USD or EUR.",
            },
            "language": {
                "type": "string",
                "description": "Optional two-letter language code, such as 'en' or 'fr'.",
            },
            "country": {
                "type": "string",
                "description": "Optional two-letter market country code, such as 'us' or 'in'.",
            },
            "stops": {
                "type": "string",
                "enum": ["any", "nonstop", "one_or_fewer", "two_or_fewer"],
                "default": "any",
                "description": "Maximum number of stops.",
            },
            "maximum_price": {
                "type": "number",
                "minimum": 0,
                "description": "Optional maximum flight price in the selected currency.",
            },
            "output": _OUTPUT_PROPERTY,
        },
        "required": ["departure_id"],
        "additionalProperties": False,
    },
}
