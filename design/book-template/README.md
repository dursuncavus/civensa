# Civensa book template generator (v1, 18 Oct 2026)

Design tooling only — not part of the application. Produces the InDesign starter template
(`Civensa_Kitap_Sablonu.idml`) and editable sample charts (SVG/PDF) for the PP / Activity Report books.

Inputs expected next to this folder (not committed, large or third-party):
- `../idml/` — the unzipped d3 print IDML (`tests/fixtures/first_load/source/pp2027_print_d3.idml`), used as scaffold
  for preferences, default styles, inks and stroke styles.
- `../gf/ofl/firasans*` — Fira Sans, Fira Sans Condensed, Fira Sans Extra Condensed TTFs (SIL OFL, google/fonts repo).

Run: `python3 build_idml.py` then `python3 charts.py` (needs fontTools, matplotlib). Output in `out/`.
`longest.json` holds the longest real text per table role extracted from the d3 IDML.
See BENIOKU.txt (Turkish) for the delivered package description.
