# Icon and design file layout
<!-- index | refs: #84, PR #87 | area: Packaging -->

**Date:** 2026-11-11 · **Area:** Packaging · **Issue:** [#84](https://github.com/vectorviolet/highrise/issues/84)

## Context

Highrise and chokepoint kept their icons in different places: highrise had the exe icon inside
`assets/` and the master art in `docs/store/`.

## Decision

Use chokepoint's layout in both repos:

- `packaging/icon.ico` is the exe icon, a build input that no longer ships as a game asset.
  `highrise.spec` picks it per OS (`packaging/icon.icns` on macOS if present; a missing icon is fine).
- `docs/design/` holds the master art (`icon.png`, `cover.png`) and the provenance note.
- `docs/store/` keeps the page text and the cover to upload (`cover-itchio.png`).

Current state: `docs/design/` has since gained `banner.png` and `art/`, and `docs/store/` the
banner preview ([cover and banner](2026-11-11-cover-and-banner.md)).
- The window icon stays in `assets/images/icon/icon_64.png`, loaded at runtime.

## Rejected

- **Keeping a different layout per repo:** every cross-repo change (CI, packaging, docs) needs
  two mental maps for the same files.

## Result

No image content changed; only paths, the spec and the links that point at them.
