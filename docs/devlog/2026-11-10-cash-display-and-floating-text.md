# Cash display restyle and floating money text
<!-- index | refs: #48, #50, PR #54 -->

**Date:** 2026-11-10 · **Area:** UI · **Issues:** [#48](https://github.com/vectorviolet/highrise/issues/48), [#50](https://github.com/vectorviolet/highrise/issues/50)  · **PR:** [#54](https://github.com/vectorviolet/highrise/pull/54)

## Context

The cash display was plain green text on a black box. It didn't match the Kenney UI Pack buttons
next to it, and it was taller and sat lower than them. Separately, money changes had no feedback:
payouts, sales and spending only changed the number.

## Options

### Cash display look (#48)

All three use the same plate asset family as the HUD buttons, nine-sliced to 280x60 at the buttons'
top and bottom line. The amount is right-aligned inside the plate.

![The three candidates side by side](img/48-cash-candidates.png)

1. **Dark plate, coin, white text.** The UI Pack gray button plate, darkened, with a gold coin
   drawn in code (no new asset).
2. **Button-style yellow plate, dark text.** The yellow gloss plate, like the buttons' own style.
3. **Dark plate, gold text.** The same dark plate, no coin.

Ten digits still fit, in every candidate:

![Candidates with a ten-digit amount](img/48-cash-large-amount.png)

Alignment is checked at every UI scale (80 to 125 percent); candidate 1 at 80, 100 and 125 percent:

![Candidate 1 at 80, 100 and 125 percent](img/48-cash-alignment-scales.png)

### Floating text (#50)

Frames at 0, 300, 700 and 1100 ms: a sale (+840$) over the sold building, two payouts (+12$, +6$)
over the buildings that paid, and a spend (-400$) falling onto the cash display.

![Floating text frames](img/50-floating-text-frames.png)

Neither pygamine nor Chokepoint has a reusable helper: Chokepoint's kill text lives inside its
kill-feedback class (battle time, camera, coin flight). The Highrise version is a small
self-contained class, `ui/floating_text.py`, driven by a time value passed in by the caller.

## Decision

- **Cash display look:** the owner picked candidate 1 (dark plate, gold coin, white text) after
  comparing all three in game. Candidates 2 and 3 and the `ui.cash_display` switch are removed;
  the comparison images above stay as the record of the options.
- **Alignment:** the plate and the buttons share `y: 20`, `height: 60` in `config/panels.yaml`;
  `tests/test_cash_display.py` checks top, bottom and height at every UI scale.
- **Floating text:** the numbers (colors, sizes, lifetime, rise and fall, cap) are in
  `config/settings.yaml` under `floating_text`. Text size and distances scale with the UI scale.
  Every payout gets its own text: the owner dropped the per-building merge window after
  play-testing, so there is no merge code or setting.
- **Spend text direction:** the cash display sits at the bottom screen edge, so a text falling
  from it would leave the screen. The red text starts just above the plate and falls onto it,
  fading out. This is the one deviation from the issue's wording; the owner can overrule it.
- **Payout callback:** `on_payout` now receives the building as well as the amount, so the
  floating text can find its source.

## Rejected alternatives

- A coin image from another Kenney pack: needs a new asset and license entry; a coin drawn in code
  looks right at every scale.
- Padding on the text box to make room for the coin: padding isn't scaled by the panel loader.
  The coin is its own object and the text is anchored to the plate's right edge instead.

## Result

The cash display and the floating text work at every UI scale; tests cover the amounts, signs, colors and expiry.

## Review follow-ups

- One formatter, `ui/money_format.py`, writes every amount from the language keys
  and `money.thousands`, so the cash display, the floating text and the toolbar and sell prices
  always match. The owner chose a thousands separator with the sign after the digits: "12,345$" in
  English and "12.345$" in Turkish (a dot), set per language in the lang files.
- Texts over the world are hidden while the info panel is open, so they never cover it.
- After a play-test: gain texts are smaller (24 pt, `gain_font_size`; spends stay 30 pt,
  `spend_font_size`), and the red spend text is right-aligned with the amount it falls onto. Texts
  are also clamped to the screen.

![The spend text next to the plate at 80, 100 and 125 percent](img/50-spend-text-right-aligned.png)
