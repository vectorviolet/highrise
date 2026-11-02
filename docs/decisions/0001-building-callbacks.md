# 0001. Wire building callbacks at creation
<!-- index | refs: #3, PR #20, #21, PR #22 -->

- **Status:** Proposed
- **Date:** 2026-10-30
- **Issues / PRs:** [#3](https://github.com/vectorviolet/highrise/issues/3), [PR #20](https://github.com/vectorviolet/highrise/pull/20), audit items 7, 17 and 18; amended by [#21](https://github.com/vectorviolet/highrise/issues/21)

## Context

The Buildings collection creates replacement buildings after merges and age
changes. It depended on AssetManager and GameAudio solely to play the merge
sound. Game.update scanned every building each frame to attach missing payout
callbacks, including callbacks on those replacements.

## Decision

Follow the approved audit's callback approach. Buildings accepts on_merge and
on_payout callbacks. Building takes on_payout as a required keyword-only constructor
argument (None means no income). Buildings' create method constructs a Building
with the collection's on_payout; the caller decides where to put it in the collection. Game's
purchase/load path, age changes, and merge completion use that method. Game
handles the merge callback and plays the same asset through its audio instance.

Keep the collection's existing two-phase merge process and column sort. Extract
arrival detection and idle snapping without changing thresholds or frame order.
Because a merge finishes a frame after arrival, board-changing input waits while
Buildings.is_busy() (one guard in the game's event handling), and saving
finishes pending merges first (#21).

## Consequences

The collection no longer imports asset or audio services, and Game no longer
repairs callback wiring every frame. Production creation paths use
Buildings.create. Constructing a Building directly requires choosing on_payout,
so a forgotten callback is a TypeError instead of a building that silently pays
nothing (amended in #21; the first version attached the callback after
construction).

Tests cover payout wiring at purchase, age change and merge, one notification per
merge, both movement directions on each axis, and the existing frame delay
between arrival and merge completion. Saves and cost/income formulas are unchanged.

## Alternatives considered

- Keep per-frame callback repair: hides incomplete construction and repeatedly
  scans the collection.
- Introduce an event bus or separate factory class: unnecessary for two callbacks.
- Override every list mutation to attach callbacks: broadens the list subclass's
  contract, and every mutation (append, insert, extend, +=, item and slice
  assignment) must be covered; missing one silently brings the bug back. A
  required constructor argument is enforced by Python itself (#21).
- Attach on_payout after construction, in create only (the first version): any
  direct Building(...) silently paid nothing (#21).
