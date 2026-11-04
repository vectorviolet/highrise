# 0002. Player settings in their own table
<!-- index | refs: #29, PR #34 -->

- **Status:** Accepted (owner, 2026-11-04)
- **Date:** 2026-11-04
- **Issues / PRs:** [#29](https://github.com/vectorviolet/highrise/issues/29), [PR #34](https://github.com/vectorviolet/highrise/pull/34)

## Context

The Game settings page adds two settings that must survive a restart: the language and Skip intro.
The volumes already live in the `game` table, next to the save itself (age, map size, money), which
New Game resets. Existing players have a `game` table without any new column, and
`GamePersistenceMixin` has no migration step.

## Decision

- The two settings live in a separate `settings` table (`language TEXT`, `skip_intro INTEGER`) with
  one row, created and seeded with the defaults (English, intro shown) by `init_database()`.
- Settings are **saved the moment they change**. The page has no Save or Cancel button: the language
  applies instantly, and a setting that needs confirming is not instant.
- **New Game keeps them.** `delete_data()` resets the save (age, size, money, buildings) and never
  touches `settings`.
- **No migration.** `CREATE TABLE IF NOT EXISTS` adds the table to an old database, and the `game`
  table keeps its columns, so saves from before this change load unchanged.
- `Game.run()` reads the settings before the splash: the language applies before any panel is built,
  and Skip intro decides whether the splash runs. An unknown saved language falls back to English.

## Consequences

- A setting added later is a column on `settings` (with an `ALTER TABLE ... ADD COLUMN` for existing
  databases) and does not need to touch the save.
- The volumes stay in `game` and keep their Save and Cancel buttons; moving them is a separate change.
- Because the row is seeded in `init_database()`, the `UPDATE` statements never miss a row.
