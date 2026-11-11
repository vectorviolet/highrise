"""How an amount of money (the cash display, the floating text) or a multiplier (the boosters' info
panel) is written, in one place."""

from pygamine.util.localization import tr


def format_money(amount: int) -> str:
    """`amount` as the language file writes money: `money.amount` places the currency sign and
    `money.thousands` separates the thousands, e.g. "12,345$" (English) or "12.345$" (Turkish).
    A negative amount keeps its minus in front of the digits: "-1,200$"."""
    digits = f"{abs(amount):,}".replace(",", tr("money.thousands"))
    return tr("money.amount", amount=("-" if amount < 0 else "") + digits)


def format_multiplier(multiplier: float) -> str:
    """A booster's multiplier as the language writes its number, e.g. 1.35 -> "1.35"
    (English) or "1,35" (Turkish, `common.decimal`); a whole one has no decimals."""
    return f"{multiplier:g}".replace(".", tr("common.decimal"))
