"""How an amount of money is written, in one place: the cash display and the floating text."""

from pygamine.util.localization import tr


def format_money(amount: int) -> str:
    """`amount` as the language file's `money.amount` writes it, e.g. "1000$"."""
    return tr("money.amount", amount=amount)
