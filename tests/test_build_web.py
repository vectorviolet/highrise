"""scripts/build_web.py (#97): what the web stage includes and leaves out.
pygbag itself is never run here (it needs internet)."""

import importlib.util
import ast
import asyncio
import io
import re
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "build_web.py"


@pytest.fixture(scope="module")
def build_web():
    spec = importlib.util.spec_from_file_location("build_web", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def staged(build_web, tmp_path_factory):
    """Staged once for the module; the tests only read it."""
    return build_web.stage(tmp_path_factory.mktemp("web") / "highrise")


def _files(folder: Path) -> set[str]:
    return {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()}


def test_stage_has_the_entry_point_as_main_py(staged):
    real = SCRIPT.parent.parent / "web" / "main.py"
    assert (staged / "main.py").read_bytes() == real.read_bytes()


def test_stage_has_the_game_engine_config_and_assets(staged):
    assert (staged / "src" / "app" / "game.py").is_file()
    assert (staged / "src" / "pygamine" / "pygamine" / "__init__.py").is_file()
    assert (staged / "config" / "settings.yaml").is_file()
    assert (staged / "assets" / "sounds" / "bg.ogg").is_file()
    assert (staged / "assets" / "SOURCES.yaml").is_file()
    # Logos the web menu still draws (config/assets.yaml, source: branding).
    branding = staged / "src" / "pygamine" / "pygamine" / "branding"
    assert (branding / "vectorviolet" / "lockup-light-solid.png").is_file()


def test_stage_leaves_out_everything_the_browser_never_uses(staged):
    files = _files(staged)
    top = {f.split("/")[0] for f in files}
    assert top == {"main.py", "src", "config", "assets"}  # no tests, saves, .git
    assert not any(f.startswith("src/pygamine/") and "/tests/" in f for f in files)
    assert not any("__pycache__" in f or f.endswith(".pyc") for f in files)
    assert "assets/maps/tiled_project.tiled-project" not in files
    assert not any("branding/vectorviolet/splash" in f for f in files)
    assert not any(f.endswith(".mp3") for f in files)
    # Only the engine's package is staged, not its repo (docs, tests, lock file).
    assert {f.split("/")[2] for f in files if f.startswith("src/pygamine/")} == {
        "pygamine"
    }


def test_stage_has_every_module_and_package_of_src(staged):
    src = SCRIPT.parent.parent / "src"
    for item in src.iterdir():
        if item.name in ("pygamine", "__pycache__") or item.suffix == ".pyc":
            continue
        assert (staged / "src" / item.name).exists(), f"src/{item.name} not staged"


def _fake_root(build_web, tmp_path, skip=None):
    """A minimal repo root with the web files (except `skip`, a relative path)."""
    root = tmp_path / "repo"
    for rel in (
        build_web.ENTRY_POINT_REL,
        build_web.TEMPLATE_REL,
        build_web.LOGO_REL,
    ):
        if rel != skip:
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text("")
    return root


def test_stage_copies_top_level_modules_of_src(build_web, tmp_path):
    root = _fake_root(build_web, tmp_path)
    (root / "src" / "pygamine" / "pygamine").mkdir(parents=True)
    (root / "src" / "pygamine" / "pygamine" / "__init__.py").write_text("")
    (root / "src" / "helper.py").write_text("X = 1")
    (root / "config").mkdir()
    (root / "assets").mkdir(exist_ok=True)
    staged = build_web.stage(tmp_path / "out", root=root)
    assert (staged / "src" / "helper.py").read_text() == "X = 1"


def test_stage_is_not_pyinstallers_work_path(build_web):
    assert build_web.STAGE_DIR != build_web.BUILD_DIR / "highrise"
    assert build_web.STAGE_DIR.name == "highrise"  # pygbag's app name


def test_stage_vendors_pure_python_yaml_only(staged):
    yaml_files = _files(staged / "src" / "yaml")
    assert "__init__.py" in yaml_files
    assert not any(f.endswith((".so", ".pyd")) for f in yaml_files)


def test_stage_replaces_an_old_stage(build_web, tmp_path):
    dest = tmp_path / "highrise"
    dest.mkdir()
    (dest / "stale.txt").write_text("old")
    build_web.stage(dest)
    assert not (dest / "stale.txt").exists()


def test_stage_stops_with_a_clear_message_without_the_submodule(build_web, tmp_path):
    root = _fake_root(build_web, tmp_path)
    with pytest.raises(SystemExit, match="submodule"):
        build_web.stage(tmp_path / "out", root=root)


@pytest.mark.parametrize("name", ["ENTRY_POINT_REL", "TEMPLATE_REL", "LOGO_REL"])
def test_stage_stops_early_when_a_web_file_is_missing(build_web, tmp_path, name):
    missing = getattr(build_web, name)
    root = _fake_root(build_web, tmp_path, skip=missing)
    with pytest.raises(SystemExit, match="Missing"):
        build_web.stage(tmp_path / "out", root=root)
    assert not (tmp_path / "out").exists()


def test_stage_only_run_catches_a_missing_template(build_web, monkeypatch, tmp_path):
    root = _fake_root(build_web, tmp_path, skip=build_web.TEMPLATE_REL)
    real_stage = build_web.stage
    monkeypatch.setattr(
        build_web, "stage", lambda: real_stage(tmp_path / "out", root=root)
    )
    with pytest.raises(SystemExit, match="web page template"):
        build_web.main(["--stage-only"])


def test_pygbag_is_pinned_and_run_with_can_close(build_web, monkeypatch, tmp_path):
    calls = []

    class Done:
        returncode = 0

    def fake_run(command, *, timeout):
        calls.append(command)
        index = tmp_path / "build" / "web" / "index.html"
        index.parent.mkdir(parents=True)
        index.write_text("<html>")
        return Done()

    monkeypatch.setattr(build_web.shutil, "which", lambda name: "uvx")
    monkeypatch.setattr(build_web.subprocess, "run", fake_run)
    build_web.run_pygbag(tmp_path)
    (command,) = calls
    assert f"pygbag=={build_web.PYGBAG_VERSION}" in command
    assert command[command.index("--can_close") + 1] == "1"
    assert command[-2:] == ["--build", str(tmp_path)]
    assert command[command.index("--template") + 1] == str(build_web.TEMPLATE)
    assert command[command.index("--icon") + 1] == str(build_web.ICON)


def test_pygbag_failure_is_retried_once_then_reported(build_web, monkeypatch, tmp_path):
    attempts = []

    class Failed:
        returncode = 1

    monkeypatch.setattr(build_web.shutil, "which", lambda name: "uvx")
    monkeypatch.setattr(
        build_web.subprocess,
        "run",
        lambda command, **kwargs: attempts.append(1) or Failed(),
    )
    with pytest.raises(SystemExit, match="internet"):
        build_web.run_pygbag(tmp_path)
    assert len(attempts) == 2


def test_pygbag_success_on_the_retry_is_accepted(build_web, monkeypatch, tmp_path):
    results = [1, 0]

    class Result:
        def __init__(self, code):
            self.returncode = code

    def fake_run(command, *, timeout):
        code = results.pop(0)
        if code == 0:
            index = tmp_path / "build" / "web" / "index.html"
            index.parent.mkdir(parents=True)
            index.write_text("<html>")
        return Result(code)

    monkeypatch.setattr(build_web.shutil, "which", lambda name: "uvx")
    monkeypatch.setattr(build_web.subprocess, "run", fake_run)
    build_web.run_pygbag(tmp_path)
    assert results == []


TEMPLATE_TEXT = (SCRIPT.parent.parent / "web" / "template.tmpl").read_text(
    encoding="utf-8"
)


def _luminance(color: str) -> float:
    channels = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = [
        c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels
    ]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(a: str, b: str) -> float:
    high, low = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def test_template_keeps_pygbags_loader_hooks():
    for hook in (
        "async def custom_site()",
        "platform.run_main(",
        "MM.UME",
        "custom_onload",
        'id="status"',
        'id="progress"',
        'id="infobox"',
        'id="canvas"',
    ):
        assert hook in TEMPLATE_TEXT, hook


def test_template_replaces_the_stock_unreadable_look():
    assert "CLICK TO PLAY" in TEMPLATE_TEXT
    assert "Ready to start" not in TEMPLATE_TEXT
    assert 'background = "#7f7f7f"' not in TEMPLATE_TEXT
    assert "powderblue" not in TEMPLATE_TEXT
    assert "background: green" not in TEMPLATE_TEXT
    assert 'src="logo.png"' in TEMPLATE_TEXT


def test_template_removes_the_loading_page_before_the_game_starts():
    """The logo must not take layout space above the canvas once the game runs."""
    start = TEMPLATE_TEXT.index("await shell.source(main")
    before_start = TEMPLATE_TEXT[:start]
    # After the click prompt (the wait on MM.UME), the loading page is hidden.
    after_click = before_start[
        before_start.rindex("while not platform.window.MM.UME") :
    ]
    for element in ("logo", "transfer", "infobox"):
        assert f'platform.window.{element}.style.display = "none"' in after_click, (
            element
        )


@pytest.mark.parametrize(
    ("text", "background"),
    [
        ("#ffffff", "#000000"),  # loading status on the page
        ("#ffffff", "#10161e"),
        ("#fbbc20", "#10161e"),  # CLICK TO PLAY on its plate
        ("#a8e063", "#10161e"),  # progress bar on its track
        ("#a8e063", "#000000"),
    ],
)
def test_template_color_pairs_have_7_to_1_contrast(text, background):
    assert text in TEMPLATE_TEXT and background in TEMPLATE_TEXT
    assert _contrast(text, background) >= 7


def test_build_copies_the_logo_next_to_index_html(build_web, monkeypatch, tmp_path):
    stage_dir = tmp_path / "stage"
    index = stage_dir / "build" / "web" / "index.html"
    index.parent.mkdir(parents=True)
    index.write_text("<html>")
    out = tmp_path / "out"
    monkeypatch.setattr(build_web, "stage", lambda: stage_dir)
    monkeypatch.setattr(build_web, "run_pygbag", lambda stage: None)
    monkeypatch.setattr(build_web, "OUT_DIR", out)
    assert build_web.build() == out
    assert (out / "logo.png").read_bytes() == build_web.LOGO.read_bytes()
    assert (out / "index.html").is_file()


def test_template_cdn_version_matches_the_pinned_pygbag(build_web):
    versions = set(
        re.findall(r"pygame-web\.github\.io/cdn/(\d+\.\d+\.\d+)", TEMPLATE_TEXT)
    )
    assert versions == {build_web.PYGBAG_VERSION}
    assert f"Pygbag Version : {build_web.PYGBAG_VERSION}" in TEMPLATE_TEXT


def test_infobox_actual_declarations_have_7_to_1_contrast():
    rules = re.search(r"#infobox\s*\{([^}]+)\}", TEMPLATE_TEXT)[1]
    colors = dict(
        re.findall(r"(?:^|;)\s*(color|background)\s*:\s*(#[0-9a-f]{6})", rules)
    )
    assert _contrast(colors["color"], colors["background"]) >= 7


def test_pygbag_timeout_is_bounded_and_retried(build_web, monkeypatch, tmp_path):
    attempts = []

    def timeout_run(command, *, timeout):
        attempts.append(timeout)
        raise subprocess.TimeoutExpired(command, timeout)

    monkeypatch.setattr(build_web.shutil, "which", lambda name: "uvx")
    monkeypatch.setattr(build_web.subprocess, "run", timeout_run)
    with pytest.raises(SystemExit, match="failed twice"):
        build_web.run_pygbag(tmp_path)
    assert attempts == [build_web.BUILD_TIMEOUT_SECONDS] * 2


def test_failed_logo_copy_preserves_previous_bundle(build_web, monkeypatch, tmp_path):
    stage = tmp_path / "stage"
    (stage / "build" / "web").mkdir(parents=True)
    (stage / "build" / "web" / "index.html").write_text("new")
    out = tmp_path / "web"
    out.mkdir()
    (out / "index.html").write_text("old")
    monkeypatch.setattr(build_web, "stage", lambda: stage)
    monkeypatch.setattr(build_web, "run_pygbag", lambda stage: None)
    monkeypatch.setattr(build_web, "OUT_DIR", out)
    monkeypatch.setattr(build_web, "LOGO", tmp_path / "missing.png")
    with pytest.raises(FileNotFoundError):
        build_web.build()
    assert (out / "index.html").read_text() == "old"


def test_failed_promotion_restores_previous_bundle(build_web, monkeypatch, tmp_path):
    out, replacement = tmp_path / "web", tmp_path / "replacement"
    out.mkdir()
    replacement.mkdir()
    (out / "index.html").write_text("old")
    (replacement / "index.html").write_text("new")
    rename = Path.rename

    def fail_replacement(path, target):
        if path == replacement:
            raise PermissionError("destination is busy")
        return rename(path, target)

    monkeypatch.setattr(Path, "rename", fail_replacement)
    with pytest.raises(PermissionError):
        build_web.promote_bundle(replacement, out)
    assert (out / "index.html").read_text() == "old"
    assert (replacement / "index.html").read_text() == "new"


@pytest.mark.parametrize("host", ["localhost", "game.itch.zone"])
@pytest.mark.parametrize("download_fails", [False, True])
def test_loader_reports_failed_download_or_corrupt_archive(
    tmp_path, monkeypatch, host, download_fails
):
    # Execute the real Python loader with fake browser I/O. It must stop before
    # running the app and replace the click prompt with a retry instruction.
    source = TEMPLATE_TEXT[
        TEMPLATE_TEXT.index("async def custom_site()") : TEMPLATE_TEXT.index(
            "asyncio.run( custom_site() )"
        )
    ]
    module = ast.parse(source)

    class Download:
        async def __aenter__(self):
            if download_fails:
                raise OSError("network unavailable")
            return io.BytesIO(b"not a valid archive")

        async def __aexit__(self, *args):
            return False

    window = SimpleNamespace(
        transfer=SimpleNamespace(style=SimpleNamespace()),
        canvas=SimpleNamespace(style=SimpleNamespace()),
        location=SimpleNamespace(host=host),
        infobox=SimpleNamespace(innerText=""),
        show_infobox=Mock(),
    )
    platform = SimpleNamespace(
        window=window,
        document=SimpleNamespace(body=SimpleNamespace(style=SimpleNamespace())),
        fopen=lambda *args: Download(),
        run_main=Mock(),
    )
    monkeypatch.setitem(sys.modules, "embed", SimpleNamespace())
    namespace = {
        "platform": platform,
        "Path": lambda path: tmp_path / "game",
        "true": True,
    }
    exec(compile(module, "template.tmpl", "exec"), namespace)
    asyncio.run(namespace["custom_site"]())
    assert "Please reload" in window.infobox.innerText
    window.show_infobox.assert_called_once()
    platform.run_main.assert_not_called()
