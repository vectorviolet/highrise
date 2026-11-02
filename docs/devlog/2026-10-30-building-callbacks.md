# Building movement and callback wiring
<!-- index | refs: #3, PR #20, #21 -->

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
  merge, leaving two level-N buildings stacked on one tile. `Game.next_age` now
  does nothing (and costs nothing) until the board has settled: no building
  moving and no arrived merge waiting for its next-frame finish
  (`Buildings.is_busy`).
- Selling the surviving building mid-merge crashed the merge finish. Now the
  merge is cancelled: the other building stays at its level on that tile, no
  level-up and no merge sound. Selling the sliding building just removes it.
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
