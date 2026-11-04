"""The UI scale setting: the steps the player can pick, in percent."""

# Percent of the authored layout (config/panels.yaml) that panels, menus, the HUD,
# popups, tooltips and their text are drawn at. The game world is never scaled.
UI_SCALES = (80, 90, 100, 110, 125)

# The owner picks the new default from the screenshots on issue #38; until
# then the UI is drawn as authored.
DEFAULT_UI_SCALE = 100


def step_ui_scale(current: int, delta: int) -> int:
    """The scale `delta` steps from `current` in UI_SCALES, stopping at both ends."""
    index = UI_SCALES.index(current) + delta
    return UI_SCALES[max(0, min(len(UI_SCALES) - 1, index))]
