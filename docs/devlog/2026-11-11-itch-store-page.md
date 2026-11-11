# itch.io store page text and checklist
<!-- index | refs: #82 | area: Docs -->

**Date:** 2026-11-11 · **Area:** Docs · **Issue:** [#82](https://github.com/vectorviolet/highrise/issues/82)

## Context

Highrise had store images in `docs/store/` but no page text and no edit-page checklist. Chokepoint's
`docs/store/README.md` and `description.html` are the proven template.

## What was copied and what changed

Copied from Chokepoint: the file layout, the HTML rules (only headings, paragraphs, lists, links,
`strong`, `code` and one image, no inline styles or tables), the section order (pitch, features,
controls, installing, credits, source, author), the edit-page checklist fields, and the tip to
re-upload the preview GIF to itch.io.

Changed for Highrise: the pitch and how to play (BUILD, merge, BOOST, EXPAND, NEXT AGE with age
tasks), the feature list, the controls, the install names and the Butler channels (`windows`,
`linux`, `osx`), and the credits (Kenney CC0 packs, Titillium Web, the Sakura Girl track, and the
AI-generated icon). Facts come from `README.md`, `config/`, `CHANGELOG.md` and `CREDITS.md`. The
screenshot list has only three images, so the checklist says a fourth is wanted.

## Decision

Pending the owner's OK: the tagline, the tags and the itch.io AI disclosure answers are proposals.
The owner pastes the text into itch.io.

## Rejected alternatives

- A stats section like Chokepoint's: Highrise's numbers are still placeholders (#10).

## Revisit if

- Controls, ages or features change: update `description.html` in the same PR.
