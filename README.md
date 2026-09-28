# SerpApi for Hermes Agent

[![PyPI version](https://img.shields.io/pypi/v/serpapi-hermes-plugin.svg)](https://pypi.org/project/serpapi-hermes-plugin/)
[![CI](https://github.com/serpapi/serpapi-hermes-plugin/actions/workflows/ci.yml/badge.svg)](https://github.com/serpapi/serpapi-hermes-plugin/actions/workflows/ci.yml)
[![Python versions](https://img.shields.io/pypi/pyversions/serpapi-hermes-plugin.svg)](https://pypi.org/project/serpapi-hermes-plugin/)
[![License: MIT](https://img.shields.io/pypi/l/serpapi-hermes-plugin.svg)](https://github.com/serpapi/serpapi-hermes-plugin/blob/main/LICENSE)

Give [Hermes Agent](https://hermes-agent.nousresearch.com/) fresh web, local, news, shopping, hotel, flight, and destination results with [SerpApi](https://serpapi.com/).

The plugin adds SerpApi to Hermes in two ways:

- Hermes's built-in `web_search` uses the fast Google Light engine.
- Dedicated Maps, News, Shopping, Hotels, Flights, and Travel Explore tools let Hermes choose the right SerpApi engine for each request.
- Direct SerpApi tools return token-efficient Markdown by default, including tables, links, and YAML frontmatter designed for agents.

## Ask Hermes to install it

You can let Hermes install and configure the plugin for you. Paste the message below into a Hermes chat, then approve the install or terminal commands if Hermes prompts you:

```text
Install and configure the SerpApi plugin from its official GitHub repository:

hermes plugins install serpapi/serpapi-hermes-plugin --enable

Request my approval for install or terminal commands whenever required; do not
bypass approvals. Follow Hermes's prompts to install Python dependencies and
enable the plugin named serpapi.

If Hermes asks whether to allow this plugin to replace built-in tools, answer
no; serpapi-hermes-plugin does not need tool-override access.

Use my existing SERPAPI_API_KEY if configured. Otherwise, ask me for my SerpApi
Private API Key when installation or setup requests it. I can copy it from
https://serpapi.com/dashboard. Save it through Hermes's configuration in
~/.hermes/.env without printing, logging, or committing it.

Configure SerpApi as the Hermes web search backend, tell me whether Hermes must
be restarted, and verify that web search, Maps, News, Shopping, Hotels, Flights,
and Travel Explore tools are available. Use this key for future SerpApi
searches and never expose it in output.
```

## Install

You need a working [Hermes Agent installation](https://hermes-agent.nousresearch.com/docs/getting-started/quickstart/) and a SerpApi account. Choose one installation method below. Both register the plugin as `serpapi` and provide the same search tools.

### From GitHub (recommended)

Use Hermes's [plugin installer](https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins/#managing-plugins):

```bash
hermes plugins install serpapi/serpapi-hermes-plugin --enable
```

Follow the prompts for Python dependencies, enablement, and your SerpApi API key. Use a current Hermes version with [plugin dependency management](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins#python-dependencies); older installers may clone the plugin without installing its dependencies.

To update a Git installation later:

```bash
hermes plugins update serpapi
```

### From PyPI

For Hermes installations whose Python environment you manage yourself, install the published package into the interpreter that runs Hermes:

```bash
uv pip install --python /path/to/hermes/python serpapi-hermes-plugin
hermes plugins enable serpapi
```

If your Hermes installation uses `~/.hermes/hermes-agent/venv`, the install command is:

```bash
uv pip install --python ~/.hermes/hermes-agent/venv/bin/python serpapi-hermes-plugin
```

The explicit [`--python`](https://docs.astral.sh/uv/pip/environments/#using-arbitrary-python-environments) selects Hermes's environment without activating it. If that environment already has pip and is activated, `python -m pip install serpapi-hermes-plugin` is equivalent. Use the GitHub option for current Hermes-managed installations, as described in Hermes's [pip distribution guidance](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins#distribute-via-pip).

Restart any running Hermes session after installation.

## Get your SerpApi API key

1. [Create a SerpApi account](https://serpapi.com/users/sign_up), or sign in to
   your existing account.
2. Open the [SerpApi dashboard](https://serpapi.com/dashboard).
3. Find your **Private API Key** in the dashboard and copy it.

One API key powers every engine in this plugin. Keep it private and never add it
to source control.

## Connect the API key to Hermes

If the plugin is not enabled yet, enable it:

```bash
hermes plugins enable serpapi
```

If prompted about permission to replace built-in tools, answer **no**. This
plugin adds new tools and a web-search provider; it does not replace built-in
tool handlers.

Open Hermes's interactive tool configuration:

```bash
hermes tools
```

In the **Web Search & Extract** section:

1. Select **SerpApi**.
2. Paste the Private API Key copied from your SerpApi dashboard.
3. Confirm the selection.

Hermes saves the key as `SERPAPI_API_KEY` in its environment configuration and
selects SerpApi for future `web_search` calls. Restart Hermes if a session was
already running.

## Manual API-key setup

Instead of using `hermes tools`, add the key to `~/.hermes/.env`:

```dotenv
SERPAPI_API_KEY=your_private_api_key
```

Then configure `~/.hermes/config.yaml`:

```yaml
plugins:
  enabled:
    - serpapi

web:
  search_backend: serpapi
```

You may also export `SERPAPI_API_KEY` in the environment that starts Hermes.
The environment variable takes precedence over the value in `~/.hermes/.env`.

## Search capabilities

Hermes's built-in `web_search` contract requires structured web records, so the plugin requests JSON for that provider and converts it to Hermes's standard response. The six directly registered SerpApi tools request [`output=md`](https://serpapi.com/search-api#api-parameters-output) by default and return SerpApi's Markdown without reparsing it. This preserves result tables and links while using fewer tokens than full JSON.

Each direct tool also accepts `output: "json"` when the agent needs structured fields such as a Google Flights `departure_token`. Markdown remains the schema default.

| What you ask for | Hermes tool | SerpApi engine |
|---|---|---|
| General web research | `web_search` | `google_light` |
| Places and local businesses | `serpapi_maps_search` | `google_maps` |
| Current and recent news | `serpapi_news_search` | `google_news_light` |
| Products, prices, and merchants | `serpapi_shopping_search` | `google_shopping_light` |
| Hotels and vacation rentals | `serpapi_hotels_search` | [`google_hotels`](https://serpapi.com/google-hotels-api) |
| Fixed-route flight fares | `serpapi_flights_search` | [`google_flights`](https://serpapi.com/google-flights-api) |
| Flexible destinations and dates | `serpapi_travel_explore_search` | [`google_travel_explore`](https://serpapi.com/google-travel-explore-api) |

Hermes chooses a tool from your request. Each tool selects and validates its own SerpApi engine, so you do not need to specify an engine name. Flight and Travel Explore location fields accept individual uppercase airport codes such as `LHR`, `CDG`, or `AUS`, as well as `/m/` or `/g/` location KGMIDs. Use Travel Explore when the traveler has a city or region in mind but no exact airport.

Example prompts:

- "Search the web for the latest Python 3.14 release notes."
- "Find highly rated coffee shops near Times Square."
- "Show me recent news about reusable rockets."
- "Find well-reviewed laptops under $1,200 with free shipping."
- "Find four-star hotels in Kyoto for October 10 to October 15."
- "Compare nonstop business-class flights from JFK to LAX next month."
- "Where can I go from Bengaluru for a one-week beach trip in December?"

Google Flights returns outbound choices first for round trips. To inspect return-flight choices, call `serpapi_flights_search` with `output: "json"`, select a `departure_token`, then call the tool again with that token and the same route and dates.

## Contributing

See [CONTRIBUTING.md](https://github.com/serpapi/serpapi-hermes-plugin/blob/main/CONTRIBUTING.md)
for development setup, tests, pull request guidelines, and the release process.

## License

[MIT](https://github.com/serpapi/serpapi-hermes-plugin/blob/main/LICENSE)
