"""Build the browser version of the game with pygbag (issue #97, ADR 0004).

    uv run python scripts/build_web.py              # stage, build, write build/web/
    uv run python scripts/build_web.py --stage-only # offline after uv sync; skips pygbag

The staged folder (build/web-stage/highrise/) holds only what the web build needs:
`web/main.py` as `main.py`, the app's `src/` packages, pygamine's package
(without its splash clip, which the web build never shows), `config/`,
`assets/`, and PyYAML's pure-Python files
(the browser has no compiled PyYAML). No tests, no .git, no saves.

pygbag is pinned and run through `uvx`; it downloads the browser runtime, so
the build needs internet. The result is build/web/ with index.html at its root,
ready to zip or to push to itch.io's html5 channel. The loading and "click to
play" page is our own template (web/template.tmpl) instead of pygbag's stock one;
the logo it shows is copied next to index.html.
"""

import argparse
import importlib.util
import shutil
import subprocess
import sys
from uuid import uuid4
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD_DIR = ROOT / "build"
# Not build/highrise: PyInstaller's work path is there. The folder's own name
# is the app name pygbag gives the bundle (highrise.apk).
STAGE_DIR = BUILD_DIR / "web-stage" / "highrise"
OUT_DIR = BUILD_DIR / "web"

# Keep in step with the 0.9.3 CDN URLs in web/template.tmpl (a test checks it).
PYGBAG_VERSION = "0.9.3"
# pygbag 0.9.3 ships its own browser Python; this only picks the host
# interpreter that runs the pygbag tool itself.
PYGBAG_HOST_PYTHON = "3.12"

# Paths relative to the repo root; stage() checks them in whichever root it is given.
ENTRY_POINT_REL = Path("web") / "main.py"
# The loading / "click to play" page (pygbag's stock one is unreadable).
TEMPLATE_REL = Path("web") / "template.tmpl"
# The logo the template shows, copied to build/web/logo.png.
LOGO_REL = Path("docs") / "design" / "cover.png"
TEMPLATE = ROOT / TEMPLATE_REL
LOGO = ROOT / LOGO_REL
ICON = ROOT / "assets" / "images" / "icon" / "icon_64.png"
BUILD_TIMEOUT_SECONDS = 300
# Copied whole into the stage.
COPIED_DIRS = ("config", "assets")
# Paths (relative to the folder named in the comment) the web build never reads.
EXCLUDED_ASSETS: tuple[str, ...] = ()
EXCLUDED_PYGAMINE = (
    "branding/vectorviolet/splash",  # video frames of the splash screen
    "branding/vectorviolet/splash.ogg",
)
# Never copied from anywhere.
_IGNORED = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo")


def _ignore(
    root: Path, excluded: tuple[str, ...]
) -> Callable[[str, list[str]], set[str]]:
    """A shutil.copytree `ignore` that also drops the `excluded` paths of `root`."""
    skip = {Path(rel).as_posix() for rel in excluded}

    def ignore(directory: str, names: list[str]) -> set[str]:
        dropped = set(_IGNORED(directory, names))
        here = Path(directory).relative_to(root)
        dropped.update(n for n in names if (here / n).as_posix() in skip)
        return dropped

    return ignore


def vendor_yaml(dest_src: Path) -> None:
    """Copy PyYAML's pure-Python package into `dest_src/yaml`."""
    spec = importlib.util.find_spec("yaml")
    assert spec is not None and spec.origin is not None, "PyYAML is not installed"
    package = Path(spec.origin).parent
    shutil.copytree(
        package,
        dest_src / "yaml",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.so", "*.pyd"),
    )


def stage(dest: Path = STAGE_DIR, root: Path = ROOT) -> Path:
    """Build a clean stage folder at `dest` and return it. An old one is removed."""
    # Fail before the slow pygbag run (and in CI's --stage-only) on a missing file.
    for rel, what in (
        (ENTRY_POINT_REL, "web entry point"),
        (TEMPLATE_REL, "web page template"),
        (LOGO_REL, "logo for the web page"),
    ):
        if not (root / rel).is_file():
            raise SystemExit(f"Missing {what}: {root / rel}")
    entry = root / ENTRY_POINT_REL
    pygamine = root / "src" / "pygamine" / "pygamine"
    if not pygamine.is_dir():
        raise SystemExit(
            f"Missing {pygamine}: run `git submodule update --init` first."
        )
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    shutil.copy2(entry, dest / "main.py")
    src = dest / "src"
    src.mkdir()
    for item in sorted((root / "src").iterdir()):
        # src/pygamine is the engine's repo: only its package goes in.
        if item.name in ("pygamine", "__pycache__") or item.suffix == ".pyc":
            continue
        if item.is_dir():
            shutil.copytree(item, src / item.name, ignore=_IGNORED)
        else:
            shutil.copy2(item, src / item.name)
    shutil.copytree(
        pygamine,
        src / "pygamine" / "pygamine",
        ignore=_ignore(pygamine, EXCLUDED_PYGAMINE),
    )
    for name in COPIED_DIRS:
        excluded = EXCLUDED_ASSETS if name == "assets" else ()
        shutil.copytree(root / name, dest / name, ignore=_ignore(root / name, excluded))
    vendor_yaml(src)
    return dest


def run_pygbag(stage_dir: Path, template: Path = TEMPLATE) -> None:
    """Run pygbag on the stage, once more if the first try fails (flaky network)."""
    uvx = shutil.which("uvx")
    if uvx is None:
        raise SystemExit("uvx is needed to run the pinned pygbag; install uv first.")
    command = [
        uvx,
        "--python",
        PYGBAG_HOST_PYTHON,
        f"pygbag=={PYGBAG_VERSION}",
        "--can_close",
        "1",
        "--template",
        str(template),
        "--icon",
        str(ICON),
        "--build",
        str(stage_dir),
    ]
    for attempt in (1, 2):
        try:
            succeeded = (
                subprocess.run(command, timeout=BUILD_TIMEOUT_SECONDS).returncode == 0
            )
        except subprocess.TimeoutExpired:
            succeeded = False
            print("pygbag timed out.", file=sys.stderr)
        if succeeded and (stage_dir / "build" / "web" / "index.html").is_file():
            return
        if attempt == 1:
            print(
                "pygbag failed; retrying once (it needs internet)...", file=sys.stderr
            )
    raise SystemExit(
        "pygbag failed twice. It downloads the browser runtime, so check the "
        "internet connection and run the script again."
    )


def build() -> Path:
    """Stage, run pygbag and copy the result to build/web/. Returns that folder."""
    stage_dir = stage()
    run_pygbag(stage_dir)
    # Assemble on the same filesystem before touching the served bundle.
    OUT_DIR.parent.mkdir(parents=True, exist_ok=True)
    # A TemporaryDirectory uses a private ACL on Windows. A sibling created by
    # copytree inherits the build folder's permissions, so a preview server
    # running without elevation can still serve it after promotion.
    replacement = OUT_DIR.with_name(f"{OUT_DIR.name}.next-{uuid4().hex}")
    try:
        shutil.copytree(stage_dir / "build" / "web", replacement)
        shutil.copy2(LOGO, replacement / "logo.png")
        promote_bundle(replacement, OUT_DIR)
    finally:
        if replacement.exists():
            assert replacement.resolve().parent == OUT_DIR.resolve().parent
            shutil.rmtree(replacement)
    return OUT_DIR


def promote_bundle(replacement: Path, destination: Path) -> None:
    """Swap complete bundles; retain the old one if the replacement cannot move."""
    backup = destination.with_name(destination.name + ".previous")
    if backup.exists():
        raise RuntimeError(
            f"Previous bundle still at {backup}; inspect it before rebuilding"
        )
    if destination.exists():
        destination.rename(backup)
    try:
        replacement.rename(destination)
    except OSError:
        if backup.exists():
            backup.rename(destination)
        raise
    if backup.exists():
        shutil.rmtree(backup)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--stage-only",
        action="store_true",
        help="only stage, skipping pygbag; offline after the project environment is synced with uv sync",
    )
    args = parser.parse_args(argv)
    if args.stage_only:
        print(f"Staged: {stage()}")
        return 0
    print(f"Web build ready: {build()} (open index.html through a web server)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
