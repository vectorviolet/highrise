# 0001. Wire building callbacks at creation
<!-- index | refs: #3, PR #20 -->

- **Status:** Proposed
- **Date:** 2026-10-30
- **Issues / PRs:** [#3](https://github.com/vectorviolet/highrise/issues/3), [PR #20](https://github.com/vectorviolet/highrise/pull/20), audit items 7, 17 and 18

## Context

The Buildings collection creates replacement buildings after merges and age
changes. It depended on AssetManager and GameAudio solely to play the merge
sound. Game.update scanned every building each frame to attach missing payout
callbacks, including callbacks on those replacements.

## Decision

Follow the approved audit's callback approach. Buildings accepts on_merge and
on_payout callbacks. Its create method constructs a Building with on_payout
already attached; the caller decides where to put it in the collection. Game's
purchase/load path, age changes, and merge completion use that method. Game
handles the merge callback and plays the same asset through its audio instance.

Keep the collection's existing two-phase merge process and column sort. Extract
arrival detection and idle snapping without changing thresholds or frame order.

## Consequences

The collection no longer imports asset or audio services, and Game no longer
repairs callback wiring every frame. New production creation paths must use
Buildings.create. Directly constructing or appending a Building remains available
for isolated tests; it does not automatically attach the collection's callback.

Tests cover payout wiring at purchase, age change and merge, one notification per
merge, both movement directions on each axis, and the existing frame delay
between arrival and merge completion. Saves and cost/income formulas are unchanged.

## Alternatives considered

- Keep per-frame callback repair: hides incomplete construction and repeatedly
  scans the collection.
- Introduce an event bus or separate factory class: unnecessary for two callbacks.
- Override every list mutation to attach callbacks: broadens the list subclass's
  contract when the production creation paths can be explicit instead.
