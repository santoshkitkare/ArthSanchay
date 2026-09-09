"""Decimal helpers and Indian digit-grouping (lakh/crore) formatting (FR-VIZ-8, NFR-3)."""
from decimal import ROUND_HALF_UP, Decimal

CENTS = Decimal("0.01")


def quantize_money(value: Decimal) -> Decimal:
    """Round to 2 decimal places for serialisation. Internal math stays at full precision."""
    return value.quantize(CENTS, rounding=ROUND_HALF_UP)


def format_inr(value: Decimal, *, decimals: int = 0) -> str:
    """Format using the Indian digit-grouping convention: last 3 digits, then groups of 2.
    e.g. 150000000 -> "15,00,00,000". Used for server-generated text (email, logs), the
    frontend performs its own formatting for the UI.
    """
    sign = "-" if value < 0 else ""
    value = abs(value)
    q = value.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)
    int_part, _, frac_part = str(q).partition(".")
    if len(int_part) <= 3:
        grouped = int_part
    else:
        last3 = int_part[-3:]
        rest = int_part[:-3]
        parts = []
        while len(rest) > 2:
            parts.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.insert(0, rest)
        grouped = ",".join(parts) + "," + last3
    out = f"{sign}\u20b9{grouped}"
    if decimals:
        out += f".{frac_part}"
    return out
