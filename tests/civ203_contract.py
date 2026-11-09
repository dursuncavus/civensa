"""CIV-203 deliberate screen changes, undone before the older frozen contracts.

The dashboard/users screens now lead with a numbered "what / how many / where"
to-do list and fold the raw counters under a closed
``<details><summary>Bütün sayılar</summary>``. These helpers reverse exactly
that change so the pre-CIV-203 frozen contracts keep comparing the original
counter layout.
"""
import re


def dashboard_todo_removed(html):
    """Drop the to-do list and un-fold both raw-counter <details> blocks."""
    html = re.sub(
        r'[ \t]*<section class="dashboard-todo"[^>]*>.*?</section>\n',
        '', html, flags=re.S)
    html = re.sub(
        r'[ \t]*<details class="dashboard-counts-details">\n'
        r'[ \t]*<summary>Bütün sayılar</summary>\n',
        '', html)
    html = re.sub(r'\n[ \t]*</details>', '', html)
    return html


def users_todo_removed(html):
    """Drop the to-do list and un-fold the raw summary <details> block."""
    html = re.sub(
        r'[ \t]*<section class="users-todo"[^>]*>.*?</section>\s*',
        '', html, flags=re.S)
    html = re.sub(
        r'<details class="users-counts-details">\s*<summary>Bütün sayılar</summary>\s*'
        r'(<p class="muted users-summary">.*?</p>)\s*</details>',
        r'\1', html, flags=re.S)
    return html
