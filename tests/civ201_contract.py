"""Undo only CIV-201 presentation markup for older frozen contracts.

Fixture bytes and form attributes stay untouched. Current browser acceptance
checks the numeric class and single-year display independently.
"""
import re


def undo_numeric_headers(html):
    return re.sub(r'<th class="pilot-numeric">', '<th>', html)


def open_containing_dialog(locator):
    """Let historical browser assertions inspect the same data in its new detail."""
    target = locator.evaluate("el => el.closest('dialog')?.id")
    if target:
        dialog = locator.page.locator('[id="' + target + '"]')
        if not dialog.evaluate('el => el.open'):
            locator.page.locator('[data-open-dialog="' + target + '"]').click()
