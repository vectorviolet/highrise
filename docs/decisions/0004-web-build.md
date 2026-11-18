# 0004. Browser build using Chokepoint's pygbag recipe
<!-- index | refs: #97 -->

- **Status:** Implemented for review
- **Date:** 2026-11-17
- **Issue:** [#97](https://github.com/vectorviolet/highrise/issues/97)

## Context

Chokepoint already runs in desktop browsers through pygbag 0.9.3. Highrise uses the
same engine, but its startup initializes a SQLite database, loads its board and
builds panels before entering the loop. Calling Application.run_async alone skips
those steps. Browser filesystem writes also disappear when the page reloads.

## Decision

Reuse the pinned build tool, loader template, pure-Python PyYAML staging, async
engine loop and browser helpers from Chokepoint. Keep native game startup and
browser startup on the same initialization path. Skip the threaded splash on web,
unlock audio after a click, and convert the existing licensed music to OGG.

Browser progress and settings use a Highrise-specific JSON SaveStore in
localStorage. Desktop saves continue to use SQLite with the existing migrations.
The web path must not import SQLite or ship a developer database. Saving completes
pending merges and preserves buildings, boosters, income fractions, tasks, age,
money and settings. Reloading and continuing must restore that state.

Browser menus expose fullscreen instead of desktop window modes and resolution.
Exit opens a Thanks for playing page. Translucent blits use the engine's ALPHA_BLIT
constant, as in Chokepoint. The existing cover illustrates the loading page.

## Alternatives

- Another web spike would repeat work already completed by Chokepoint.
- SQLite on a temporary browser filesystem would lose progress on reload and add
  a compiled dependency; localStorage is already supported by the engine.
- Replacing desktop SQLite would introduce an unnecessary save migration.
- A blocking startup splash would prevent the browser from rendering frames.

## Validation

Test startup and storage with mocked browser objects, run the desktop suite and
smoke test with temporary saves, then build and play in a visible, focused browser.
Verify Continue after a page reload, settings persistence, fullscreen, Exit and
frame time. Hidden tabs are throttled and cannot establish rendering performance.
