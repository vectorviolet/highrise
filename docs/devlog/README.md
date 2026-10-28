# Devlog

How Highrise is built: one entry per feature or design decision, with the options we looked at,
what we chose, who chose it and why. [`CHANGELOG.md`](../../CHANGELOG.md) stays the short list of
what changed; this folder holds the detail.

Dates are the day the PR was merged (UTC), or the day of the decision for entries without a merged
PR. "Owner" is the project owner; "Claude" is the Claude Code session that implemented the change.

## Entries

| Date | Title | Area | Issues / PRs |
|---|---|---|---|
| 2026-10-28 | [Panels from UI Pack v2](2026-10-28-ui-pack-v2-panels.md) | Art, UI | #12, PR #13 |

## Adding an entry

Every PR that adds a feature or settles a design decision adds an entry here, or updates the
existing one, and a row in the table above. Bug fixes get an entry when there was a real choice to
make or the cause is worth remembering.

- File name: `YYYY-MM-DD-short-title.md`, dated by the merge (or decision) day.
- Images: PNG screenshots of this game or mock-ups made from it, in [`img/`](img/), at most 1280 px
  wide. Name them `<issue>-<what>.png`. Crop to the part that matters. No hot-linked images.
- Where an option has no screenshot, describe it in words. Don't fake one.
- Say who decided: "owner", or "default chosen by Claude, approved by the owner" (for example by
  merging a PR that listed the choice for review). Only write down reasons someone actually gave.

## Template

```markdown
# Title

**Date:** YYYY-MM-DD · **Area:** UI · **Issue:** [#N](https://github.com/vectorviolet/highrise/issues/N) · **PR:** [#M](https://github.com/vectorviolet/highrise/pull/M)

## Context

The problem or request, and where it came from.

## Options

<table>
<tr>
<td><img src="img/N-option-a.png" width="400"><br>A: one line on this option.</td>
<td><img src="img/N-option-b.png" width="400"><br>B: one line on this option.</td>
</tr>
</table>

## Decision

What we chose, who chose it, and why.

## Rejected alternatives

- The alternative, and why not.

## Result

<img src="img/N-result.png" width="640">

Merged in PR #M.

## Revisit if

- What would make us look at this again.
```
