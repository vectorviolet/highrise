# Store page (itch.io)

The itch.io page at <https://umutcanekinci.itch.io/highrise> is edited by hand on itch.io. This
folder holds what goes into it:

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
- **Classification:** Games. **Kind of project:** Downloadable. **Release status:** In
  development until 1.0, then Released.
- **Platforms:** Windows, macOS, Linux (the three the release workflow builds).
- **Genre:** Strategy. (Puzzle is the alternative.)
- **Tags (proposal):** only relevant ones, preferring itch.io's suggestions: City Builder,
  Isometric, Puzzle, 2048, Singleplayer, Relaxing, Open Source, Pygame. Don't tag the game's own name.
- **Languages:** English, Turkish (the two the game ships).
- **Inputs:** Keyboard, Mouse.
- **AI disclosure (proposal):** answer it on the edit page to match the description's line. Claude Code
  was a coding assistant (code). The game icon was generated with OpenAI Codex and post-processed
  (graphics: the icon only). The other art is Kenney's CC0 packs and the music is by Sakura Girl, so
  answer no AI for those. Check what itch.io's form asks about code, graphics, sound and text.
- **Screenshots:** at least 4 are wanted, uploaded to the page's gallery in this order (all in
  `docs/screenshots/`, 1920x1080): `02_build_mode.png`, `03_inspection.png` and
  `01_main_menu.png`. That is only three, so add a fourth (for example a later age or a boosted
  city). itch.io shows them apart from the description, so the description only embeds the
  preview GIF.
- **Images:** `description.html` links the GIF from GitHub so it works when pasted as is. Better:
  upload `docs/preview.gif` through itch.io's editor and swap the image on the page for the
  uploaded one, so it loads fast and doesn't break if the file moves in the repo.
- **Theme:** colors that match the game, not plain black on white: the cover's sky blue
  (about `#54D8E7`) as the background, the icon's dark navy (about `#1E1D3B`) for text and
  panels, and the logo's yellow for links.
- **Cover:** `docs/store/cover-itchio.png` (630x500, itch.io's cover size) goes on the edit page.
  `docs/store/cover.png` (2304x1824) is the larger master.
- **Icon:** `docs/store/icon.png` (1024x1024).
- **Trailer:** none yet (the GIF only).

When the game changes in a way players see (controls, features, ages), update
`description.html` in the same PR and paste it again.
