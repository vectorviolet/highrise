# Store page (itch.io)

The itch.io page at <https://umutcanekinci.itch.io/highrise> is edited by hand on itch.io. This
folder holds what goes into it:

- `cover-itchio.png` and `banner-itchio.png`: the cover (630x500) and the banner preview
  (960x300) to upload. Both are made by `scripts/make_cover.py` from the art in `docs/design/art/`.
- `description.html`: the page's description. Paste it into the description field in HTML
  mode. It uses only headings, paragraphs, lists, links, `strong`, `code` and one image, with no inline
  styles or tables, so it reads well on phones.

The release workflow (`.github/workflows/release.yml`) uploads the builds with Butler to the
`windows`, `linux` and `osx` channels; it never touches the page text. The same builds are on the
[GitHub releases](https://github.com/vectorviolet/highrise/releases/latest).

The tagline, tags and AI disclosure answers below are **proposals**: the owner approves them
before they go on the page.

## Checklist for the edit page

Fields that live outside the description, following itch.io's
[quality guidelines](https://itch.io/docs/creators/quality-guidelines):

- **Short description or tagline (proposal):** "Merge buildings 2048-style and grow a city through
  four ages."
- **Classification:** Games. **Kind of project:** Downloadable. **Release status:**
  Released (1.0.0 is out).
- **Platforms:** Windows, macOS, Linux (the three the release workflow builds).
- **Genre:** Strategy. (Puzzle is the alternative.)
- **Tags:** see [Field values](#field-values) below.
- **Languages:** English, Turkish (the two the game ships).
- **Inputs:** Keyboard, Mouse.
- **AI disclosure (proposal):** answer it on the edit page to match the description's line. Claude Code
  was a coding assistant (code). The game icon, the cover, the banner and the key arts were generated
  with OpenAI Codex and post-processed (graphics: those pictures only). The in-game art is Kenney's
  CC0 packs (not AI) and the music is by Sakura Girl (not AI), so answer no AI for those. Check what itch.io's form asks about code, graphics, sound and text.
- **Screenshots:** at least 4 are wanted, uploaded to the page's gallery in this order (all in
  `docs/screenshots/`, 1920x1080): `02_build_mode.png`, `03_inspection.png` and
  `01_main_menu.png`. That is only three, so add a fourth (for example a later age or a boosted
  city). itch.io shows them apart from the description, so the description only embeds the
  preview GIF.
- **Images:** `description.html` links the GIF from GitHub so it works when pasted as is. Better:
  upload `docs/preview.gif` through itch.io's editor and swap the image on the page for the
  uploaded one, so it loads fast and doesn't break if the file moves in the repo.
- **Theme (checklist item, proposal):** colors that match the cover and banner, not plain black on
  white: the sky blue (about `#54D8E7`) as the page background, the dark navy (about `#1E1D3B`) for
  text and panels, and the tagline's yellow (`#FFE278`) for links. Set it in the theme editor on the
  live page and check that the text stays readable.
- **Cover:** `docs/store/cover-itchio.png` (630x500, itch.io's cover size) goes on the edit page.
  `docs/design/cover.png` (1402x1122, the art's native size) is the larger master.
- **Banner:** `docs/design/banner.png` (1920x600) goes in the page's banner field (itch.io shows it
  about 960 px wide, some players 1200 px, so 1920 px is 2x). `docs/store/banner-itchio.png` (960x300)
  is the preview. Keep the key content in the central 80% of the height, and check it in the theme
  editor on the live page.
- **Icon:** `docs/design/icon.png` (1024x1024).
- **Trailer:** none yet (the GIF only).

## Field values

What the edit page holds today and what to set for the fields that are still empty or wrong. The
owner edits the page by hand; this list is the source to copy from.

| Field | Value |
|---|---|
| Title / project URL | Highrise / `highrise` |
| Short description or tagline | An isometric city-builder where same-level buildings merge 2048-style. (as on the page; it does not repeat the title) |
| Classification / kind / release status | Games / Downloadable / Released |
| Pricing | $0 or donate, suggested donation $2.00 (the owner's choice, as set) |
| Uploads | `highrise-windows.zip`, `highrise-linux.zip`, `highrise-osx.zip`. The release workflow's butler jobs push the unpacked builds to the `windows`, `linux` and `osx` channels and itch.io names the files after the channels (the GitHub release zips are `highrise-windows.zip`, `highrise-linux.zip` and `highrise-macos.zip`). Tick the matching platform on each file's "Executable for" boxes (Windows, Linux, macOS), so itch.io shows the right download buttons and platform filters |
| Description | paste `docs/store/description.html` in HTML mode |
| Genre | Strategy |
| Tags (max 10; itch.io says not to repeat the genre or platforms, so drop "strategy") | City Builder, Isometric, Puzzle, 2048, Casual, Relaxing, Idle, 2D, Singleplayer, Open Source. Prefer itch.io's own suggestions when it offers a near match; don't tag the game's own name |
| AI generation disclosure | **Yes.** Kinds: **Graphics** (the icon, cover, banner and key arts, made with OpenAI Codex), **Text & Dialog** (the store text, README and the Turkish strings were drafted with Claude and reviewed by the owner), **Code** (Claude Code as a coding assistant). Not Sounds: the sound effects are Kenney's CC0 packs and the music is by Sakura Girl. |
| Statement of AI usage (shown publicly) | Built with Claude Code as a coding assistant; game design, art direction, playtesting and review by the developer. The game icon, the cover, the banner and the key arts were generated with OpenAI Codex and post-processed. The in-game buildings, UI and sounds are Kenney's CC0 packs. |
| App store links | none |
| Custom noun | leave blank (default "game") |
| Download and install instructions | see the block below |
| Community | Comments and the discussion board are both disabled now. Suggested: turn **Comments** on (a small game gets its feedback there) and leave the discussion board off; the owner decides |
| Visibility and access | Draft until the page is ready (cover, banner, 4+ screenshots, tags, theme), then Public |
| Cover image | `docs/store/cover-itchio.png` (630x500) |
| Banner | `docs/design/banner.png` (1920x600) |
| Gameplay video or trailer | none yet |
| Screenshots (3 to 5) | `02_build_mode.png`, `03_inspection.png`, `01_main_menu.png`, plus one or two from the candidates in `docs/devlog/img/screenshots-2026-11/` (a later age, the NEXT AGE checklist, Turkish settings), retaken at 1920x1080 |

**Download and install instructions** (paste into the field):

```
Download the zip for your system, unzip it and run the game. No Python or installer needed.

Windows: run highrise.exe. The game isn't code-signed, so the first launch may show "Windows protected your PC": click More info, then Run anyway.
macOS: open Highrise.app. The app isn't signed, so macOS blocks the first launch: open System Settings > Privacy & Security, click Open Anyway next to Highrise, then Open.
Linux: run ./highrise/highrise from the unzipped folder.

Your city is saved on this computer; press CONTINUE to resume it.
```

When the game changes in a way players see (controls, features, ages), update
`description.html` in the same PR and paste it again.
