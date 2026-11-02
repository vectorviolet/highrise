# Building movement and callback wiring
<!-- index | refs: #3, PR #20, #21, PR #22 -->

**Date:** 2026-10-30 · **Area:** Refactoring · **Issue:** [#3](https://github.com/vectorviolet/highrise/issues/3) · **Follow-up:** [#21](https://github.com/vectorviolet/highrise/issues/21)

## Context

Continue the approved structure audit after the cloud extraction in PR #19.
This change implements items 7, 17 and 18: smaller movement methods, a merge
callback in place of the collection's audio dependency, and payout callbacks
attached at creation rather than repaired in each frame.

## Options

- Retain audio coupling and the per-frame scan: less initial change, but keeps
  the two responsibilities the audit identified.
- Pass two callbacks and centralize construction in Buildings.create: the
  proposed implementation, following the audit's plan.

Both options have the same visible result, so no comparison screenshots are
included. No UI, art or game-design choice is being made.

## Decision

Codex implemented the callback option for owner review. Game remains responsible
for the merge sound and paying the player. Buildings remains responsible for
movement and replacement construction. See [ADR 0001](../decisions/0001-building-callbacks.md).

### Why

- The collection only imported the asset manager and the audio service to play
  one sound. With an `on_merge` callback, Buildings is plain game logic and Game
  keeps all audio in one place.
- The per-frame payout scan in `Game.update` repaired wiring that construction
  should have got right, and it hid any creation path that forgot it. Wiring
  the payout when a building is built removes the scan and the hiding.
- Two callbacks are enough for this; nothing else needs to listen.

### Rejected alternatives

From [ADR 0001](../decisions/0001-building-callbacks.md):

- Keep the per-frame callback repair: hides incomplete construction and scans
  every building every frame.
- An event bus or a separate factory class: more machinery than two callbacks
  need.
- Override every list mutation to attach the payout callback: widens the list
  subclass's contract and has to cover every way a list can change (`append`,
  `insert`, `extend`, `+=`, item and slice assignment). The follow-up below
  makes the payout a required constructor argument instead.

## Result

Arrival detection, idle snapping and merge completion have separate methods.
Settled merges are still collected before list changes; a newly arrived building
still merges on the next frame, and the collection is sorted after the batch.
Payout wiring covers purchases, loaded buildings, age changes and merge results.
Regression tests check the affected timing, movement, callbacks and income.

## Follow-up (#21)

The post-merge review of PR #20 found an older bug and some loose ends:

- NEXT AGE during a slide or merge rebuilt every building and dropped the
  merge, leaving two level-N buildings stacked on one tile. Selling, arrow keys
  and building had the same kind of gap, at least in the frame between a
  slider's arrival and its merge. Now one guard in the game's event handling
  ignores every board-changing action (moves, build, sell, NEXT AGE) while
  `Buildings.is_busy()`: a building is moving, or an arrived merge waits for
  its next-frame finish. Merges take about 0.2 s, like the existing move
  block. Per-action checks were rejected: the review found four actions that
  had missed one.
- An info panel opened on a building mid-merge kept pointing at it after the
  merge replaced it, and SELL then crashed. The panel now closes when its
  building leaves the board (simpler than rebinding it to the merge result),
  and selling never removes a building that isn't on the board.
- Saving mid-merge stored both buildings on one tile. Saving now finishes
  pending merges first, as the animation would, so the save loads as the
  finished result.
- A directly built `Building` silently paid nothing. `on_payout` is now a
  required keyword-only constructor argument (`None` means no income), so
  forgetting it raises a `TypeError`; `Buildings.create` still passes the
  collection's callback. This was picked over attaching the callback in
  overridden list methods because Python enforces the argument itself, while
  overriding means covering every list mutation and missing one brings the
  silent bug back. Tests check that purchase, load, age change and merge all
  pay.
- Cleanups: the merge sound path is cached like the other sounds,
  `Building.snap_to_target()`, one `Buildings.sort_by_column()` and one
  per-axis arrival check.
