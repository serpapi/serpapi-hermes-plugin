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

The live suite makes real requests through every search and extraction path. It checks Markdown and JSON search responses, result limits, regional languages, compact and full scrape/map/crawl responses, crawl limits, CSS filtering, and API errors. Live crawls are capped at two pages:

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

## Git installation and Hermes catalog updates

The repository root is a Hermes directory plugin. Its `__init__.py` loads the implementation from `src/serpapi_hermes_plugin/` using a relative import, and its `pyproject.toml` declares the runtime dependencies for Hermes to install. PyPI continues to use the `hermes_agent.plugins` entry point. Keep both manifests current when changing tools, credentials, or the release version.

With a current Hermes checkout and the plugin's dependencies available, validate the repository before publishing Git-install changes:

```bash
hermes plugins doctor /path/to/serpapi-hermes-plugin --ci
hermes plugins validate /path/to/serpapi-hermes-plugin --install-deps
```

[SerpApi is listed in the Hermes catalog](https://hermes-agent.nousresearch.com/docs/plugins/serpapi). Hermes pins each catalog release to a reviewed commit. Its [admission policy](https://github.com/NousResearch/hermes-agent/blob/main/plugin-catalog/README.md) requires a maintainer-reviewed PR for every update and forbids plugin self-updaters. GitHub installs can follow our repository through `hermes plugins update serpapi`; catalog installs follow the reviewed pin.

Prepare catalog updates manually after publishing a release:

1. Update `plugin-catalog/serpapi.yaml` in a current `NousResearch/hermes-agent` checkout with the release's full 40-character SHA, matching version, and capabilities from `plugin.yaml`.
2. Pin the README and image URLs to that same SHA.
3. Run `python scripts/validate_plugin_catalog.py plugin-catalog/serpapi.yaml` there, then run Hermes's plugin admission checks against the released plugin checkout.
4. Submit a PR with the release comparison link, relevant changes, network disclosures, and actual validation results.

The seven direct tools belong in `provides_tools`. Hermes owns `web_search` and `web_extract`, which use our provider; they are not extra catalog tools. Preserve the current catalog tier. Only Nous maintainers assign `verified` or `official`; vendor verification can be requested in the PR description.

The listing header uses `assets/catalog-banner.png` at a 2:1 aspect ratio. Keep artwork in the released commit; catalog images and any future screenshots must point to that same SHA. The listing renders the README from the pin too, so documentation and artwork changes need a catalog update.
