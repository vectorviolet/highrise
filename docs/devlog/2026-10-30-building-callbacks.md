# Building movement and callback wiring
<!-- index | refs: #3, PR #20 -->

**Date:** 2026-10-30 · **Area:** Refactoring · **Issue:** [#3](https://github.com/vectorviolet/highrise/issues/3)

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

## Result

Arrival detection, idle snapping and merge completion have separate methods.
Settled merges are still collected before list changes; a newly arrived building
still merges on the next frame, and the collection is sorted after the batch.
Payout wiring covers purchases, loaded buildings, age changes and merge results.
Regression tests check the affected timing, movement, callbacks and income.
