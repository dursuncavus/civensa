"""Undo only CIV-201 presentation markup for older frozen contracts.

Fixture bytes and form attributes stay untouched. Current browser acceptance
checks the numeric class and single-year display independently.
"""
import re


def undo_numeric_headers(html):
    return re.sub(r'<th class="pilot-numeric">', '<th>', html)
