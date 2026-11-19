# 0004. Browser build using Chokepoint's pygbag recipe
<!-- index | refs: #97, PR #102 -->

- **Status:** Proposed
- **Date:** 2026-11-18
- **Issues / PRs:** [#97](https://github.com/vectorviolet/highrise/issues/97), [PR #102](https://github.com/vectorviolet/highrise/pull/102)

## Context

Chokepoint already runs in desktop browsers through pygbag 0.9.3. Highrise uses the same engine,
but its startup opens a SQLite database, loads its board and builds panels before the loop, and
browser filesystem writes disappear when the page reloads. The build recipe here is a fork of
Chokepoint's (`scripts/build_web.py`, `web/template.tmpl`, the itch.io limit check in
`release.yml`, `util/web.py`); a fix to one should be checked against the other.

## Decision

- **Build:** reuse Chokepoint's pinned pygbag, loader template, pure-Python PyYAML staging and
  async engine loop. Native and browser startup share one initialization path
  (`Game._prepare_run`); the browser skips the threaded splash.
- **Saves:** the browser uses pygamine's public `SaveStore` (JSON in localStorage, store names
  `highrise-save` and `highrise-settings`); desktop keeps SQLite and its migrations. The web
  path never imports SQLite. A restore reads the save once and holds every value to a valid one
  before the board changes, reusing the desktop's clamping (`_restore_building`). A save that
  cannot be read is kept until an explicit New Game. Because a closed tab raises no QUIT, the
  board saves 2 s after each build, sell, move, merge, NEXT AGE or expand, on ESC, and every
  10 s while the board is open if money or the board changed (payouts). One notice says when
  nothing survives a reload: a probe of localStorage (`util/web.storage_available`, since
  blocked storage makes `SaveStore` fall back to memory) and a read-back after each save
  (a refused write).
- **Music:** `bg.mp3` became `bg.ogg` everywhere (the same CC BY 3.0 track; CC BY 3.0 section 3
  allows a format-only change, and SOURCES.yaml records the transcode). One file serves both builds.
- **Rendering:** translucent blits use pygamine's `ALPHA_BLIT` (the browser's SDL2 build lacks
  `BLEND_ALPHA_SDL2`); it changes nothing on desktop.
- **Frame rate:** the browser presents 60 frames a second, but motion (buildings sliding, clouds)
  steps per update at the desktop's 165 a second. A desktop update steps the buildings twice (the
  game panel's own update and the world's) and the clouds once; the browser runs the same
  number of steps per second by elapsed time, and everything else (panels, timers, texts) once
  a frame.
- **Release:** `web` and `publish-web` run only on a version-tag push; the GitHub Release gets
  `highrise-web.zip` only after the desktop release succeeded, so a failed desktop build never
  leaves a published web-only release.
- Browser menus show fullscreen instead of window modes and resolution; Exit opens a Thanks
  for playing page.

## Consequences

Desktop persistence is unchanged. Browser persistence is one small module. Tests use a fake
`platform.window` (the `browser` fixture in `tests/conftest.py`). A refused write shows a notice
but there is no retry queue: the next change saves again.

## Alternatives considered

- SQLite on a temporary browser filesystem: lost on reload and needs a compiled dependency.
- Replacing desktop SQLite: an unneeded save migration.
- A write-outcome type with separate notices for progress and settings, a session cache and a
  hand-written snapshot validator: built first, then removed as more code than the problem
  needs (see the devlog).
- Keeping the MP3 on desktop and swapping in OGG only for the web stage: two files to track for
  one license note.
