import tomllib
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_project_urls_use_the_serpapi_repository() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    urls = project["urls"]

    assert project["name"] == "serpapi-hermes-plugin"
    assert urls["Homepage"] == "https://github.com/serpapi/serpapi-hermes-plugin"
    assert urls["Repository"] == "https://github.com/serpapi/serpapi-hermes-plugin"
    assert urls["Issues"] == "https://github.com/serpapi/serpapi-hermes-plugin/issues"
def test_release_workflow_keeps_oidc_permission_in_publish_job() -> None:
    workflow = (ROOT / ".github/workflows/release.yml").read_text()
    publish_job = workflow.split("\n  publish:\n", maxsplit=1)[1]

    assert "release:\n    types: [published]" in workflow
    assert workflow.count("id-token: write") == 1
    assert "needs: verify-distributions" in publish_job
    assert "name: pypi" in publish_job
    assert "id-token: write" in publish_job
    assert "pypa/gh-action-pypi-publish@" in publish_job
    assert "actions/checkout@" not in publish_job
    assert "uv build" not in publish_job
    assert "PYPI_API_TOKEN" not in workflow
