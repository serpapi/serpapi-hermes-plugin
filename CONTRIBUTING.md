# Contributing to `serpapi-hermes-plugin`

Thanks for helping improve the SerpApi plugin for Hermes Agent.

## Development setup

Install the locked development environment with
[`uv`](https://docs.astral.sh/uv/):

```bash
uv sync --locked --dev
```

## Tests and checks

Run the linter and offline test suite before opening a pull request:

```bash
uv run ruff check .
uv run pytest -m "not live"
```

The live suite makes real requests through every plugin search path and checks
the returned web results, places, news articles, and products:

```bash
SERPAPI_API_KEY=your_private_api_key uv run pytest -m live
```

Pull requests from branches in this repository to `main` run this live suite on
Python 3.14 after the offline test matrix passes. The repository must have a
`SERPAPI_API_KEY` GitHub Actions secret for the job to authenticate. GitHub does
not expose Actions secrets to pull requests from forks or Dependabot, so the
live job is intentionally skipped for those pull requests.

## Pull requests

- Keep each pull request focused on one change.
- Add or update tests when behavior changes.
- Update the documentation when the user-facing workflow changes.
- Make sure the linter and offline test suite pass.

## Releasing

Releases are published from
[`serpapi/serpapi-hermes-plugin`](https://github.com/serpapi/serpapi-hermes-plugin)
to [PyPI](https://pypi.org/project/serpapi-hermes-plugin/) by GitHub Actions.
The release workflow uses PyPI trusted publishing, so the repository does not
need a `PYPI_API_TOKEN` secret.

### One-time trusted-publisher setup

1. In the GitHub repository, open **Settings → Environments** and create an
   environment named `pypi`.
2. Add the desired deployment protection rules to that environment. Requiring
   approval from a package maintainer before publishing is recommended.
3. Configure the publisher on PyPI with these exact values:

   | PyPI field | Value |
   |---|---|
   | PyPI project name | `serpapi-hermes-plugin` |
   | GitHub owner | `serpapi` |
   | GitHub repository | `serpapi-hermes-plugin` |
   | Workflow filename | `release.yml` |
   | Environment | `pypi` |

If the PyPI project does not exist yet, create a pending publisher from your
PyPI account's **Publishing** page. The first successful workflow run will
create the project. If it already exists, add the publisher from the project's
**Manage → Publishing** page.

The owner, repository, workflow filename, and environment must exactly match
`.github/workflows/release.yml`. Do not add a PyPI API token to GitHub.

### Publish a release

1. Set the package version and refresh the lock file:

   ```bash
   uv version 0.1.0
   uv lock
   ```

   Set the same version in the root `plugin.yaml` and `src/serpapi_hermes_plugin/plugin.yaml` so Git and PyPI installations report the same release.

2. Run the same checks used by CI:

   ```bash
   uv sync --locked --dev
   uv run ruff check .
   uv run pytest
   uv build
   uv run twine check dist/*
   ```

3. Merge the version change into `main` and wait for CI to pass.
4. On GitHub, create and publish a release whose tag is `v` followed by the
   package version, such as `v0.1.0`.
5. Approve the `pypi` deployment if the environment requires approval.

Publishing the GitHub Release starts the **Publish release to PyPI** workflow.
It tests every supported Python version, checks that the tag matches the package
version, builds and tests both distributions, and only then publishes the exact
verified files to PyPI using a short-lived OIDC credential.

PyPI does not allow an uploaded version to be replaced. If publishing fails
after an artifact has reached PyPI, increment the package version and create a
new GitHub Release.

### Release references

- [PyPI: adding a trusted publisher](https://docs.pypi.org/trusted-publishers/adding-a-publisher/)
- [PyPI: creating a project with a pending publisher](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
- [PyPI: publishing with a trusted publisher](https://docs.pypi.org/trusted-publishers/using-a-publisher/)

## Git installation and Hermes catalog submission

The repository root is a Hermes directory plugin. Its `__init__.py` loads the implementation from `src/serpapi_hermes_plugin/` using a relative import, and its `pyproject.toml` declares the runtime dependencies for Hermes to install. PyPI continues to use the `hermes_agent.plugins` entry point. Keep both manifests current when changing tools, credentials, or the release version.

With a current Hermes checkout and the plugin's dependencies available, validate the repository before publishing Git-install changes:

```bash
hermes plugins doctor /path/to/serpapi-hermes-plugin --ci
hermes plugins validate /path/to/serpapi-hermes-plugin
```

The [Hermes catalog](https://hermes-agent.nousresearch.com/docs/user-guide/features/plugin-catalog#submitting-a-plugin-to-the-catalog) accepts submissions through reviewed pull requests to `NousResearch/hermes-agent`. Publishing to PyPI or pushing this repository does not create a catalog listing.

1. Publish a release/tag containing the Git entry point and its manifest. Use a new version if the current version has already been released.
2. Resolve that release to its full 40-character commit SHA. The catalog pin must reference the published commit containing these files; a branch, tag name, or uncommitted checkout cannot be the pin.
3. As an owner or maintainer of this repository, open a PR against `NousResearch/hermes-agent` adding `plugin-catalog/serpapi.yaml` using the template below. Replace both placeholders with the released values.
4. Run `python scripts/validate_plugin_catalog.py plugin-catalog/serpapi.yaml` in the Hermes checkout and pass the PR's catalog CI. CI clones the pinned commit and runs `hermes plugins validate --install-deps` against it, including registration, dependency, and security checks.

```yaml
name: serpapi
repo: https://github.com/serpapi/serpapi-hermes-plugin
sha: REPLACE_WITH_RELEASE_COMMIT_SHA
description: "SerpApi web, Maps, News, Shopping, Hotels, Flights, and Travel Explore for Hermes Agent."
maintainer: serpapi
tier: community
category: web
title: SerpApi
version: "REPLACE_WITH_RELEASE_VERSION"
docs_url: https://github.com/serpapi/serpapi-hermes-plugin#readme
capabilities:
  provides_tools:
    - serpapi_maps_search
    - serpapi_news_search
    - serpapi_shopping_search
    - serpapi_hotels_search
    - serpapi_flights_search
    - serpapi_travel_explore_search
  provides_hooks: []
  provides_middleware: []
  requires_env:
    - SERPAPI_API_KEY
```

The catalog's `community` tier applies because NousResearch does not maintain this plugin. The six listed tools are registered by this plugin; `web_search` belongs to Hermes and uses our registered web-search provider, so it is not an additional tool in the catalog entry.

After the catalog PR is merged and available to clients, users can run `hermes plugins install serpapi`. Each later catalog release needs another PR updating `sha` and `version`. Optional catalog images and screenshots must use supported GitHub URLs pinned to the same commit. See the [catalog admission policy and schema](https://github.com/NousResearch/hermes-agent/blob/main/plugin-catalog/README.md) for the full requirements.
