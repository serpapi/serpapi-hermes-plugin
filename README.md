# SerpApi for Hermes Agent

[![PyPI version](https://img.shields.io/pypi/v/serpapi-hermes-plugin.svg)](https://pypi.org/project/serpapi-hermes-plugin/)
[![CI](https://github.com/serpapi/serpapi-hermes-plugin/actions/workflows/ci.yml/badge.svg)](https://github.com/serpapi/serpapi-hermes-plugin/actions/workflows/ci.yml)
[![Python versions](https://img.shields.io/pypi/pyversions/serpapi-hermes-plugin.svg)](https://pypi.org/project/serpapi-hermes-plugin/)
[![License: MIT](https://img.shields.io/pypi/l/serpapi-hermes-plugin.svg)](https://github.com/serpapi/serpapi-hermes-plugin/blob/main/LICENSE)

Use [SerpApi](https://serpapi.com/) in [Hermes Agent](https://hermes-agent.nousresearch.com/) for web search, Maps, News, Shopping, Hotels, Flights, Travel Explore, and page extraction.

Queries and requested URLs are sent to SerpApi using your API key. SerpApi fetches the requested pages; the plugin adds no telemetry.

The plugin provides:

- Hermes's built-in `web_search` uses the fast Google Light engine.
- Dedicated Maps, News, Shopping, Hotels, Flights, and Travel Explore tools let Hermes choose the right SerpApi engine. They return Markdown by default, with JSON available.
- `web_extract` reads page content through SerpApi. `serpapi_extract` adds scraping, URL mapping, and crawling, with compact content or full JSON through `compact_mode: false`.

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

Configure SerpApi as the Hermes web search and extract backend, tell me whether Hermes must be restarted, and verify that web search, page extraction, Maps, News, Shopping, Hotels, Flights, and Travel Explore tools are available. Use this key for future SerpApi requests and never expose it in output.
```

## Install

You need [Hermes Agent](https://hermes-agent.nousresearch.com/docs/getting-started/quickstart/) 0.21.6 or later and a SerpApi account. Choose one installation method below. Both register the plugin as `serpapi` and provide the same search and extraction tools.

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

GitHub installs follow the repository; [catalog installs](https://hermes-agent.nousresearch.com/docs/plugins/serpapi) receive maintainer-reviewed releases through the same update command.

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

Hermes saves the key as `SERPAPI_API_KEY` in its environment configuration and selects SerpApi for future `web_search` calls. Also select SerpApi as the extract backend, or set `web.extract_backend: serpapi` as shown below. Restart Hermes if a session was already running.

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
  extract_backend: serpapi
```

You may also export `SERPAPI_API_KEY` in the environment that starts Hermes.
The environment variable takes precedence over the value in `~/.hermes/.env`.

## Search and extraction capabilities

Ask Hermes what you need; it chooses the tool and supplies the parameters. Direct search tools return Markdown by default and support JSON when structured data is needed.

| What you ask for | Hermes tool | SerpApi engine |
|---|---|---|
| General web research | `web_search` | `google_light` |
| Read page content | `web_extract` | [`extract`](https://serpapi.com/extract-api) |
| Scrape pages, map URLs, or crawl a site | `serpapi_extract` | `extract` |
| Places and local businesses | `serpapi_maps_search` | `google_maps` |
| Current and recent news | `serpapi_news_search` | `google_news_light` |
| Products, prices, and merchants | `serpapi_shopping_search` | `google_shopping_light` |
| Hotels and vacation rentals | `serpapi_hotels_search` | [`google_hotels`](https://serpapi.com/google-hotels-api) |
| Fixed-route flight fares | `serpapi_flights_search` | [`google_flights`](https://serpapi.com/google-flights-api) |
| Flexible destinations and dates | `serpapi_travel_explore_search` | [`google_travel_explore`](https://serpapi.com/google-travel-explore-api) |

Example prompts:

- "Search the web for the latest Python 3.15 release notes."
- "Read https://www.python.org/about/ and summarize it."
- "Extract the product details and prices from this page."
- "Map this website and read the three pages most relevant to my question."
- "Find highly rated coffee shops near Times Square."
- "Show me recent news about reusable rockets."
- "Find well-reviewed laptops under $1,200 with free shipping."
- "Find four-star hotels in Kyoto for a five-night stay next month."
- "Compare nonstop business-class flights from JFK to LAX next month."
- "Where can I go from Bengaluru for a one-week beach trip in December?"

## Page extraction

With `web.extract_backend: serpapi`, Hermes uses SerpApi to read pages. The `serpapi_extract` tool also lets the agent choose between:

- `scrape`: Read one page (default).
- `map`: Discover a website's URLs.
- `crawl`: Follow links and read multiple pages.

Results are compact by default, with full JSON available through `compact_mode: false`. Search URLs return results from their dedicated engines. The agent can limit crawl size and depth, include sitemaps or subdomains, and filter page elements.

Pages are fetched without running JavaScript. Crawling uses one search credit per successfully extracted page. See the [Extract API documentation](https://serpapi.com/extract-api) for details.

## Contributing

See [CONTRIBUTING.md](https://github.com/serpapi/serpapi-hermes-plugin/blob/main/CONTRIBUTING.md)
for development setup, tests, pull request guidelines, and the release process.

## License

[MIT](https://github.com/serpapi/serpapi-hermes-plugin/blob/main/LICENSE)
