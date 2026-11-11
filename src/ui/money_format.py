"""How an amount of money is written, in one place: the cash display and the floating text."""

from pygamine.util.localization import tr


def format_money(amount: int) -> str:
    """`amount` as the language file writes money: `money.amount` places the currency sign and
    `money.thousands` separates the thousands, e.g. "12,345$" (English) or "12.345$" (Turkish).
    A negative amount keeps its minus in front of the digits: "-1,200$"."""
    digits = f"{abs(amount):,}".replace(",", tr("money.thousands"))
    return tr("money.amount", amount=("-" if amount < 0 else "") + digits)
