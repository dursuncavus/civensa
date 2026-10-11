"""Spreadsheet-safe CSV cells for exports that users open in Excel/Calc (A1-F9)."""
import re
from decimal import Decimal

# Cells starting with these characters can be evaluated as a formula on import.
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
# Turkish-locale Excel splits on ";" (and then on line breaks inside a quoted cell) when it
# opens a CSV, so text after ";", CR or LF can start a new cell too.
_LIST_SEPARATOR_FORMULA = re.compile(r'([;\r\n])(?=[ "]*[=+\-@\t\r])')


def csv_text(value) -> str:
    """Neutralise an untrusted text cell; CSV quoting alone does not stop formulas."""
    text = "" if value is None else str(value)
    text = _LIST_SEPARATOR_FORMULA.sub(r"\1'", text)
    return "'" + text if text.startswith(FORMULA_PREFIXES) else text


def csv_row(cells) -> list:
    """Typed numbers stay numeric; every other cell is treated as untrusted text."""
    return [cell if isinstance(cell, (int, float, Decimal)) else csv_text(cell) for cell in cells]


def csv_cell_matches(cell, stored) -> bool:
    """Compare a re-imported cell with the stored text, accepting the neutralised export form."""
    cell, stored = str(cell or "").strip(), str(stored or "").strip()
    return cell == stored or cell == csv_text(stored)
