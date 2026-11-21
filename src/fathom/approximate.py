"""Approximate display ("about 5") for issue #44: an UNCONFIRMED READING of Zach's rule, not wired in.

Zach, 2026-11-17 (Fathom#44): "Click to display full number, round to 0 when the last significant
digit is 1 or 9. Round to 5 if the penultimate sig digit is 4 or 5 and the final sig digit is > 7 or
< 3, respectively."

Reading used here (awaiting his Yes / No / Adjust):
1. Round the magnitude to two significant figures (half up). Two, because that is what turns
   his 2026-11-11 example 4.93 into "about 5".
2. If the second figure is 1 or 9, round it to 0 (4.9 -> 5, 4.1 -> 4, 91 -> 90).
3. Else if the figures are 4 then 8-9, or 5 then 0-2, snap to 5 (4.8 -> 5, 5.2 -> 5, 48 -> 50).
4. Otherwise keep two figures (4.7 stays 4.7).
The exact value is never changed; callers show it on click. Stored values are untouched (spec 008).
"""

from decimal import Decimal, ROUND_HALF_UP
import math


def approximate(value, figures=2):
    """Return the display number for `value` under the reading above, or `value` when it can't apply."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value == 0:
        return value
    d = Decimal(repr(value)) if isinstance(value, float) else Decimal(value)
    sign, mag = (-1 if d < 0 else 1), abs(d)
    exp = mag.adjusted() - (figures - 1)
    q = Decimal(1).scaleb(exp)
    r = mag.quantize(q, rounding=ROUND_HALF_UP)
    if r.adjusted() != mag.adjusted():  # carried into a new place (9.96 -> 10): already round
        return _out(sign * r, value)
    digits = r.as_tuple().digits
    head, last = digits[-2] if len(digits) > 1 else 0, digits[-1]
    if last in (1, 9):
        r = r.quantize(Decimal(1).scaleb(exp + 1), rounding=ROUND_HALF_UP)
    elif (head == 4 and last > 7) or (head == 5 and last < 3):
        pair = Decimal(1).scaleb(exp + 2)  # keep the figures before the final pair: 148 -> 150, not 50
        r = (r // pair) * pair + Decimal(5).scaleb(exp + 1)
    return _out(sign * r, value)


def _out(d, original):
    if d == d.to_integral_value():
        return int(d)
    return float(d)


def is_approximate(value, figures=2):
    """True when the display number differs from the exact value (so it needs the "about" mark)."""
    shown = approximate(value, figures)
    return shown is not value and shown != value
