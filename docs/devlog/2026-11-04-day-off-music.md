# Background music: Sakura Girl - Day Off
<!-- index | refs: #35, PR #40 | area: Audio -->

**Date:** 2026-11-04 · **Area:** Audio · **Issue:** [#35](https://github.com/vectorviolet/highrise/issues/35) · **PR:** [#40](https://github.com/vectorviolet/highrise/pull/40)

## Context

Highrise had no music: the previous track was unlicensed and was removed, and the game hides the
MUSIC VOLUME row while there is no `bg` sound. Any new track needs a license that allows bundling it
in the game.

## Decision

The owner chose **Day Off** by Sakura Girl (2026-11-04), the same artist as Chokepoint's "Clown".

- **License check:** the track's SoundCloud page lists the license as CC BY 3.0. The owner verified
  this on 2026-11-04. The file is the artist's free Hypeddit download. `assets/SOURCES.yaml` records
  both, and the CC BY 3.0 text ships in `licenses/assets/`.
- **Attribution** as the artist asks, in CREDITS.md and the README: "Music : Sakura Girl - Day Off"
  and the link youtu.be/vAv9KtrU_5c. Highrise has no in-game credits screen.
- **Format:** the MP3 ships byte-identical (7.4 MB), as Chokepoint does with Clown. Re-encoding was
  rejected: it would be a modified copy of the work for a problem that belongs to the engine. The
  engine decodes the whole track into memory because pygamine plays music as a `mixer.Sound`;
  streaming it with `pygame.mixer.music` is tracked in
  [pygamine#37](https://github.com/vectorviolet/pygamine/issues/37).

## Result

The track loops in the menu and in game, and the MUSIC VOLUME setting works again.
