# SerpApi for Hermes Agent

[![PyPI version](https://img.shields.io/pypi/v/serpapi-hermes-plugin.svg)](https://pypi.org/project/serpapi-hermes-plugin/)
[![License: MIT](https://img.shields.io/pypi/l/serpapi-hermes-plugin.svg)](https://github.com/serpapi/serpapi-hermes-plugin/blob/main/LICENSE)

Give [Hermes Agent](https://hermes-agent.nousresearch.com/) live search results from [SerpApi](https://serpapi.com/). With this plugin, Hermes searches the web, Google Maps, News, Shopping, Hotels, and Flights. It also reads, maps, and crawls web pages.

Install it from the [Hermes Marketplace](https://hermes-agent.nousresearch.com/marketplace/serpapi):

```bash
hermes plugins install serpapi
```

Or ask Hermes in the desktop app:

```text
Install the serpapi plugin
```

In a terminal, Hermes asks for your SerpApi API key if it has none saved, hides it as you type, and saves it for you. In the desktop app, enter the key on the install card under **Advanced**. [Sign up for free](https://serpapi.com/users/sign_up) to get one.

## Set up

1. Get your API key. [Create a SerpApi account](https://serpapi.com/users/sign_up) or sign in, then copy the key from [serpapi.com/manage-api-key](https://serpapi.com/manage-api-key).

2. Install the plugin:

   ```bash
   hermes plugins install serpapi
   ```

   Hermes asks for your API key if it has none saved. Paste it. Hermes hides the key as you type and saves it to your profile's `.env` file. Then accept the prompts to enable the plugin and install its dependencies.

3. Make SerpApi your web search provider:

   ```bash
   hermes config set web.search_backend serpapi
   hermes config set web.extract_backend serpapi
   ```

   You can also pick **SerpApi** in the `hermes tools` menu, under **Web Search & Extract**.

4. Start a new Hermes session. If you run the Hermes gateway, restart it with `hermes gateway restart`.

## Try it

Ask in plain language and Hermes picks the right search.

- "Search the web for the Python 3.15 release notes."
- "Find top-rated coffee shops near Times Square."
- "Show me recent news about reusable rockets."
- "Find laptops under $1,200 with free shipping."
- "Find four-star hotels in Kyoto for five nights next month."
- "Compare nonstop business-class flights from JFK to LAX next month."
- "Where can I go from Bengaluru for a one-week beach trip in December?"
- "Read https://www.python.org/about/ and summarize it."
- "Map docs.python.org and list the pages about asyncio."

## What Hermes can do

| You ask for | Hermes uses | SerpApi API |
|---|---|---|
| Web results | `web_search` | [Google Light Search API](https://serpapi.com/google-light-api) |
| The content of a page | `web_extract` | [Extract API](https://serpapi.com/extract-api) |
| A page, a site's URLs, or a crawl | `serpapi_extract` | [Extract API](https://serpapi.com/extract-api) |
| Places and local businesses | `serpapi_maps_search` | [Google Maps API](https://serpapi.com/google-maps-api) |
| Current and recent news | `serpapi_news_search` | [Google News Light API](https://serpapi.com/google-news-light-api) |
| Products, prices, and merchants | `serpapi_shopping_search` | [Google Shopping Light API](https://serpapi.com/google-shopping-light-api) |
| Hotels and vacation rentals | `serpapi_hotels_search` | [Google Hotels API](https://serpapi.com/google-hotels-api) |
| Fares on a fixed route | `serpapi_flights_search` | [Google Flights API](https://serpapi.com/google-flights-api) |
| Destinations for flexible dates | `serpapi_travel_explore_search` | [Google Travel Explore API](https://serpapi.com/google-travel-explore-api) |

The first two rows are Hermes's own web tools, which use SerpApi once you finish step 3 of the setup. The other seven come with the plugin.

One API key covers all of them. Searches and page reads use the search credits in your [SerpApi plan](https://serpapi.com/pricing). Cached results are free, and your [dashboard](https://serpapi.com/dashboard) shows your usage.

## Page extraction

Hermes can read the web in three ways:

- Read one page. Ask Hermes to read or summarize a URL.
- Map a website. Hermes gets a list of the site's pages.
- Crawl a website. Hermes follows the site's links and reads each page on the way.

Before you crawl a site:

- A crawl uses one search credit for each page it extracts. It extracts up to 10 pages by default, and you can raise the limit to 100. Failed pages and cached responses are free.
- A page that needs JavaScript to show its content can come back incomplete.
- SerpApi respects each website's `robots.txt` and skips the pages a site blocks.
- By default, Hermes refuses private and internal network addresses.

The [Extract API documentation](https://serpapi.com/extract-api) has the details.

## Your data

- The plugin sends your search queries, their options (such as location, dates, and filters), and the URLs you ask Hermes to read to `https://serpapi.com/search`, together with your API key. It contacts no other service.
- SerpApi's servers run each search and fetch each page, so the sites you read receive SerpApi's request. Before it reads a page, Hermes looks up the address from your machine and, by default, blocks private and internal ones.
- Hermes saves your key as `SERPAPI_API_KEY` in your profile's `.env` file, which is `~/.hermes/.env` for the default profile. The plugin reads the key through Hermes and removes it from results and error messages before the model sees them.
- The plugin collects no telemetry, runs no shell commands or background processes, and reads none of your files.

SerpApi's [privacy policy and terms](https://serpapi.com/legal) cover the requests it receives.

## Update or remove

Get the latest version:

```bash
hermes plugins update serpapi
```

Remove the plugin and reset your web search provider:

```bash
hermes plugins remove serpapi
hermes config unset web.search_backend
hermes config unset web.extract_backend
```

If you picked SerpApi in the `hermes tools` menu, the shared `web.backend` setting names it too. Check with `hermes config get web.backend`. If it says `serpapi`, choose another provider in the menu or run `hermes config unset web.backend`.

Your API key stays in your profile's `.env` file until you delete that line.

These commands manage Marketplace and GitHub installs. For a PyPI install, see "From PyPI" below.

## Troubleshooting

| You see | Do this |
|---|---|
| `SERPAPI_API_KEY is not set` | Run `hermes tools`, open **Web Search & Extract**, select **SerpApi**, and paste your key. You can also add `SERPAPI_API_KEY=your_private_api_key` to `~/.hermes/.env`. |
| `SerpApi rejected the API key` | Copy the key again from [serpapi.com/manage-api-key](https://serpapi.com/manage-api-key) and replace the saved one. |
| `SerpApi quota exhausted` | Your plan ran out of searches or hit its hourly limit. Check your [dashboard](https://serpapi.com/dashboard). |
| Hermes has no SerpApi tools | Run `hermes plugins list`. If `serpapi` shows `not enabled`, run `hermes plugins enable serpapi`. Hermes hides the tools until it finds your API key. Start a new session after either fix. |
| `web_search` uses another provider | Run the two `hermes config set` commands from step 3. They take priority over the `hermes tools` menu. |
| `Blocked: URL targets a private, internal, or unresolved address` | By default, Hermes blocks private and internal addresses. Use a public `http` or `https` URL. |
| The install asks for a newer Hermes | Run `hermes update`. The plugin needs Hermes Agent 0.21.6 or later. |
| The plugin stays disabled after a scripted install | Add `--enable --yes-deps`, as shown under "Scripts, Docker, and CI". |
| The plugin is missing in another profile | Hermes installs plugins per profile. Run `hermes -p <profile> plugins install serpapi`. |

For other problems, [open an issue](https://github.com/serpapi/serpapi-hermes-plugin/issues).

## Other ways to install

The Marketplace command above covers most setups. These cover the rest.

### Ask Hermes in the desktop app

Name the plugin in a chat:

```text
Install the serpapi plugin
```

Hermes finds the plugin in the Marketplace and shows an install card. If Hermes has no API key saved, open **Advanced**, enter the key under **Credentials**, and click **Install** there. With a key saved, click **Install** on the card. Then make SerpApi your web search and extract provider, as in step 3 of the setup.

You can also install without a chat. Open the [Marketplace page](https://hermes-agent.nousresearch.com/marketplace/serpapi) and click **Install in Hermes**, or find SerpApi under **Capabilities → Plugins** in the app. Each route installs the same version as the terminal command.

### Ask Hermes in a terminal or messaging chat

Hermes shows the install card in the desktop app. In a terminal or messaging chat, give Hermes the commands to run and approve them as it asks:

```text
Install the SerpApi plugin from the Hermes Marketplace and make it my web
search and extract backend. Request my approval for terminal commands whenever
Hermes requires it; do not bypass approvals.

1. Check that SERPAPI_API_KEY is saved in my Hermes profile. Do not print it,
   and do not ask me to paste it into this chat. If it is missing, stop and
   tell me to run "hermes plugins install serpapi" in a terminal, where Hermes
   asks for the key and hides it.
2. If serpapi is not installed, run:
   hermes plugins install serpapi --enable --yes-deps
   If it is already installed, enable it with "hermes plugins enable serpapi"
   instead of reinstalling it.
3. Run: hermes config set web.search_backend serpapi
4. Run: hermes config set web.extract_backend serpapi
5. Run: hermes plugins list, and confirm that serpapi shows as enabled.

Finish by telling me whether I need to restart Hermes.
```

### Scripts, Docker, and CI

An unattended install has nobody to answer Hermes's prompts. Save your API key in your profile's `.env` file first, as shown under "Edit the config files". Then run:

```bash
hermes plugins install serpapi --enable --yes-deps
hermes config set web.search_backend serpapi
hermes config set web.extract_backend serpapi
```

With the key saved, Hermes skips the key prompt. `--yes-deps` approves the plugin's two Python dependencies, `httpx` and `markdown-it-py`.

### From GitHub

To try changes before they reach the Marketplace, install from this repository:

```bash
hermes plugins install serpapi/serpapi-hermes-plugin --enable
```

This installs the code on this repository's `main` branch, which may include changes not yet available in the Marketplace. Hermes shows a warning, because the Marketplace review hasn't covered that code. Update it with `hermes plugins update serpapi`.

### From PyPI

Use PyPI if you run Hermes from a Python environment you manage yourself. Hermes's standard installer manages its own environment, and the Marketplace command is the right route there.

Install the package into the interpreter that runs Hermes, then enable it:

```bash
uv pip install --python /path/to/hermes/python serpapi-hermes-plugin
hermes plugins enable serpapi
```

Add your key to your profile's `.env` file as shown below, and finish step 3 of the setup.

`hermes plugins update` and `hermes plugins remove` don't manage a PyPI install. Upgrade or uninstall the package with the same tool:

```bash
uv pip install --python /path/to/hermes/python --upgrade serpapi-hermes-plugin
uv pip uninstall --python /path/to/hermes/python serpapi-hermes-plugin
```

### Edit the config files

Add the key to your profile's `.env` file. For the default profile, that is `~/.hermes/.env`:

```dotenv
SERPAPI_API_KEY=your_private_api_key
```

Then enable the plugin and select the backends in your profile's `config.yaml`, which is `~/.hermes/config.yaml` for the default profile. Merge these settings into any existing configuration:

```yaml
plugins:
  enabled:
    - serpapi

web:
  search_backend: serpapi
  extract_backend: serpapi
```

## Learn more

- [Introducing SerpApi's Hermes Agent Plugin](https://serpapi.com/blog/introducing-serpapis-hermes-agent-plugin/)
- [How to Give Hermes Agent Real-Time Web Search Results](https://serpapi.com/blog/how-to-give-hermes-agent-real-time-web-search-results/)
- [Web Search & Extract in the Hermes docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/web-search)

## Contributing

See [CONTRIBUTING.md](https://github.com/serpapi/serpapi-hermes-plugin/blob/main/CONTRIBUTING.md) for development setup, tests, and the release process.

## License

[MIT](https://github.com/serpapi/serpapi-hermes-plugin/blob/main/LICENSE)
