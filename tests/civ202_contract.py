"""Undo CIV-202 modal controls before comparing the frozen form/link contract.

The search and modal triggers are outside forms. Modal triggers undo to their
legacy section links; direct section anchors still open the right dialog.
All legacy form actions, controls, CSRF values,
permissions, removal disclosures and links still compare without normalization.
"""
import re


def undo_program_dialog_controls(html):
    html = re.sub(r'<form method="dialog"><button class="button">Kapat</button></form>', '', html)
    return re.sub(
        r'<button type="button" class="button" data-program-dialog="program-(cards|assignments|catalogue|sources|finance|economics)-dialog">\s*Ayrıntıyı aç\s*</button>',
        lambda match: '<a href="#rp-' + match[1] + '">Ayrıntıyı aç</a>', html)
