"""Undo only CIV-202's modal close forms before comparing frozen POST controls.

The search is outside a form. All legacy form actions, controls, CSRF values,
permissions, removal disclosures and links still compare without normalization.
"""
import re


def undo_program_dialog_controls(html):
    return re.sub(r'<form method="dialog"><button class="button">Kapat</button></form>', '', html)
