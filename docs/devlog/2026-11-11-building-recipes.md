# Building recipes
<!-- index | refs: #59, PR #71 | area: Buildings -->

**Date:** 2026-11-11 · **Area:** Buildings · **Issues:** [#59](https://github.com/vectorviolet/highrise/issues/59)

## Context

Today's building sprites (`assets/images/buildings/<age>/level1..6.png`) are hand-made composites
of the Kenney Hexagon Buildings pieces. Levels 1 and 2, 3 and 4, and 5 and 6 look identical and
every base level has the door on the left. #59 proposes composing sprites in code from recipes in
`config/buildings.yaml` (floors bottom to top, then a roof).

Nothing in the game uses the recipes yet. `scripts/render_building_styles.py` reads
`config/buildings.yaml` and the raw pack pieces and writes the images below.

How a sprite is composed (same rule for all ages): the ground floor piece (65x89) sits at the
bottom, each further floor 23 px higher (the game's own floor step), and the roof is aligned so its
base lands on the top floor's top edge. Footprint (65 px wide) and foot position (bottom edge)
match today's.

## Round 1 (owner feedback)

Two draft styles were compared (A close to today, B with random gates, windows and roofs). Owner
feedback:

- The only per-building variety is the **door side** (left or right): picked at random when the
  building is first built and kept through every level. On a merge the result keeps the door side
  of the building that stays in place. No random gates, windows or roofs.
- The game needs **more levels than 6** before 1.0, and every level must be readable at a glance:
  each level adds exactly one fixed, visible change, with the height growing every few levels.

## Round 2: two level ladders

Rows per sheet: today's six sprites, ladder L1, ladder L2, and a door-left (L) / door-right (R)
row for L1 levels 2, 5 and 8, which is the only variety.

- **L1, shutters reserved (11 levels):** no shutter pieces, so shutters stay free for a later
  per-building renovation upgrade.
- **L2, shutters used (14 levels):** shutters may also be level steps.

![wood](img/building-ladders-wood.png)
![rock](img/building-ladders-rock.png)
![stone](img/building-ladders-stone.png)

What each level adds:

| Level | L1 | L2 |
|---|---|---|
| 1 | a plain door under a low roof | a plain door under a low roof |
| 2 | a window beside the door | a window beside the door |
| 3 | the door becomes a wide gate | the window gets shutters |
| 4 | a second floor with a window | the door becomes a wide gate |
| 5 | the second floor gets a second window | a second floor with a window |
| 6 | the roof rises to a point | the second floor gets a second window |
| 7 | a third floor with a window | the second floor gets shutters |
| 8 | the third floor gets a second window | the roof rises to a point |
| 9 | the roof grows taller | a third floor with a window |
| 10 | the roof becomes a curved spire | the third floor gets a second window |
| 11 | a fourth floor | the third floor gets shutters |
| 12 | | the roof grows taller |
| 13 | | the roof becomes a curved spire |
| 14 | | a fourth floor |

Observations: the floor seam lines come from the pieces themselves (each floor piece has a light
top edge) and the pack has no seamless wall piece, so removing them would mean editing the art.
Shutters are clear on rock (orange) but nearly invisible on wood and stone. The wide gate replaces
the window (the pack has no gate-plus-window piece). The Short to Straight roof step and the
Straight to Tall step are subtle on their own.

Pack pieces used (all from `Tiles/` of the Kenney Hexagon Buildings pack, CC0), per age: floors
`DoorLeft`, `DoorRight`, `DoorWindow`, `DoorWindowMirror`, `DoorWindowBlinds`,
`DoorWindowBlindsMirror`, `GateLeft`, `GateRight`, `WindowLeft`, `WindowRight`, `Windows`,
`WindowBlinds`; roofs `RoofShort`, `RoofStraight`, `RoofTall`, `RoofPointy`. Rock uses the pack's
`red` roofs. Phase 2 would copy these into `assets/` with `SOURCES.yaml` entries.

## Decision

Pending owner: ladder L1 or L2 (and any per-age tweaks).

## Rejected alternatives

- Style B's random gates, windows and roofs per building (owner: only the door side varies).
- Style A (levels 1/2, 3/4 and 5/6 each a pair of lookalikes): not readable at a glance.

## Result

Phase 2 (game loads recipes, old PNGs removed, door side saved, more levels) waits for the pick.
