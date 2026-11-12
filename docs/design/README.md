# Design masters

Master art that is not loaded by the game at runtime. Same layout as chokepoint.

- `icon.png`: the 1024 px game icon (shown in the README and on the store page).
- `social-preview.png`: the 1280x640 GitHub social preview, built from `banner.png` by
  `scripts/make_social_preview.py` and uploaded by hand in the repository's settings.
- `cover.png`: the 1402x1122 cover (the merge art with the title). The 630x500 file to upload to
  itch.io is `docs/store/cover-itchio.png`.
- `banner.png`: the 1920x600 itch.io banner. The 960x300 preview is `docs/store/banner-itchio.png`.
- `art/`: the text-free key arts, unchanged: `cover-merge-island.png` and `banner-wide.png` (the
  sources of the cover and the banner), `art-ages-sunset.png` and `art-golden-hour-city.png` (kept as
  key art, not used by the store yet).
- The cover and the banner are built from `art/` by `scripts/make_cover.py` (title and tagline in
  one shared definition): `uv run --group dev python scripts/make_cover.py`.
- The executable's icon lives in `packaging/icon.ico` (6 sizes, a build input read by
  `highrise.spec`, not bundled as an asset). The window icon is `assets/images/icon/icon_64.png`.

**Provenance:** the icon (all sizes), the cover, the banner and the key arts are the only
AI-generated graphics: the owner generated them with OpenAI Codex (image generation), post-processed
the icon with a NumPy script and the cover and banner with `scripts/make_cover.py`, and approved
shipping them. Not CC0. The earlier cover was made with Gemini ("nano banana"); the Codex cover
replaces it. See [the icon devlog entry](../devlog/2026-11-11-game-icon.md) and
[the cover and banner entry](../devlog/2026-11-11-cover-and-banner.md).
