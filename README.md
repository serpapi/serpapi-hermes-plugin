# SerpApi for Hermes Agent

Give [Hermes Agent](https://hermes-agent.nousresearch.com/) fast, fresh search
results from the web, Google Maps, Google News, and Google Shopping with
[SerpApi](https://serpapi.com/).

The plugin adds SerpApi to Hermes in two ways:

- Hermes's built-in `web_search` uses the fast Google Light engine.
- Dedicated Maps, News, and Shopping tools let Hermes choose the right SerpApi
  engine for local places, current reporting, and product searches.

## Ask Hermes to install it

You can let Hermes install and configure the plugin for you. Paste the message
below into a Hermes chat, then approve the install or terminal commands if
Hermes prompts you:

```text
Install serpapi-hermes-plugin into the same Python environment that runs this
Hermes Agent. If this is a standard Hermes installation, run:

cd ~/.hermes/hermes-agent
uv pip install --python venv/bin/python serpapi-hermes-plugin

Otherwise, use the active Hermes Python environment to run:

uv pip install --python /path/to/hermes/python serpapi-hermes-plugin

Request my approval for install or terminal commands whenever required; do not
bypass approvals. After the package is installed, run:

hermes plugins enable serpapi

If Hermes asks whether to allow this plugin to replace built-in tools, answer
no; serpapi-hermes-plugin does not need tool-override access.

Then ask me for my SerpApi Private API Key, which I can copy from the SerpApi
dashboard. Do not ask for the key until installation and enablement succeed.
After I provide it, save it as SERPAPI_API_KEY in ~/.hermes/.env without
printing, logging, or committing it. Configure SerpApi as the Hermes web search
backend, tell me whether Hermes must be restarted, and verify that web search,
Maps, News, and Shopping tools are available. Use this key for future SerpApi
searches and never expose it in output.
```

## Install

You need a working
[Hermes Agent installation](https://hermes-agent.nousresearch.com/docs/getting-started/quickstart/)
and a SerpApi account.

Install the plugin from PyPI in the same Python environment as Hermes. If you
installed Hermes with its standard installer, use its `venv` interpreter
explicitly:

```bash
cd ~/.hermes/hermes-agent
uv pip install --python venv/bin/python serpapi-hermes-plugin
```

The explicit `--python` is important: the standard Hermes installer creates a
directory named `venv`, while bare `uv pip install` automatically looks for a
directory named `.venv`.

For a custom Hermes installation, point uv at the Python interpreter that runs
Hermes:

```bash
uv pip install --python /path/to/hermes/python serpapi-hermes-plugin
```

If that environment already has pip and is activated, the equivalent command
is `python -m pip install serpapi-hermes-plugin`.

Restart any running Hermes session after installation.

## Get your SerpApi API key

1. [Create a SerpApi account](https://serpapi.com/users/sign_up), or sign in to
   your existing account.
2. Open the [SerpApi dashboard](https://serpapi.com/dashboard).
3. Find your **Private API Key** in the dashboard and copy it.

One API key powers every engine in this plugin. Keep it private and never add it
to source control.

## Connect the API key to Hermes

Enable the installed plugin:

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

| What you ask for | Hermes tool | SerpApi engine |
|---|---|---|
| General web research | `web_search` | `google_light` |
| Places and local businesses | `serpapi_maps_search` | `google_maps` |
| Current and recent news | `serpapi_news_search` | `google_news_light` |
| Products, prices, and merchants | `serpapi_shopping_search` | `google_shopping_light` |

Hermes chooses a tool from your request. Each tool selects and validates its own
SerpApi engine, so you do not need to specify an engine name.

Example prompts:

- "Search the web for the latest Python 3.14 release notes."
- "Find highly rated coffee shops near Times Square."
- "Show me recent news about reusable rockets."
- "Find well-reviewed laptops under $1,200 with free shipping."

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, tests, pull request
guidelines, and the release process.

## License

[MIT](LICENSE)
