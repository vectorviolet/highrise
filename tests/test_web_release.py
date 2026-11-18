"""Exercise publishing guards against manual runs and partial desktop releases."""

from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

JOBS = yaml.safe_load(Path(".github/workflows/release.yml").read_text())["jobs"]
PUBLISH_JOBS = (
    "release",
    "publish-itch",
    "publish-web",
    "attach-web",
    "attach-installer",
)


def allowed(
    job,
    event="push",
    ref="refs/tags/v1.1.0",
    release="success",
    web="success",
    canceled=False,
):
    expression = JOBS[job]["if"].removeprefix("${{").removesuffix("}}")
    expression = (
        expression.replace("&&", " and ")
        .replace("||", " or ")
        .replace("!", " not ")
        .strip()
    )
    context = dict(
        github=SimpleNamespace(event_name=event, ref=ref),
        needs=SimpleNamespace(
            web=SimpleNamespace(result=web),
            release=SimpleNamespace(result=release),
            installer=SimpleNamespace(result="success"),
        ),
        cancelled=lambda: canceled,  # codespell:ignore cancelled
        startsWith=lambda value, prefix: value.startswith(prefix),
    )
    return eval(expression, {"__builtins__": {}}, context)


@pytest.mark.parametrize("job", PUBLISH_JOBS)
@pytest.mark.parametrize("ref", ["refs/heads/main", "refs/tags/v1.1.0"])
def test_manual_runs_never_publish(job, ref):
    assert not allowed(job, event="workflow_dispatch", ref=ref)


@pytest.mark.parametrize("job", PUBLISH_JOBS)
def test_version_tag_push_can_publish(job):
    assert allowed(job)
    assert not allowed(job, ref="refs/heads/main")


@pytest.mark.parametrize(
    "result,expected",
    [
        ("success", True),
        ("skipped", True),
        ("failure", False),
        ("cancelled", False),  # codespell:ignore cancelled
    ],
)
def test_web_attachment_preserves_failed_desktop_drafts(result, expected):
    assert allowed("attach-web", release=result) == expected
    assert not allowed("attach-web", release=result, web="failure")
    assert not allowed("attach-web", release=result, canceled=True)
