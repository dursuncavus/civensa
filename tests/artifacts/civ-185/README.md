# CIV-185 acceptance artifacts

All images use synthetic local data. Desktop/deck images are 1920 × 1080;
the mobile capture is 390 pixels wide and includes the full page.
The deck screenshots use an approved local İdare release with three approved units.

- `civ185-spot-green.png`, `civ185-spot-dark.png`: alternating spot backgrounds and report-bound numbers.
- `civ185-feature-cards.png`: three cards; the middle card has no image area.
- `civ185-spot-pdf.png`: final number in `#pdf` with no counting animation.
- `civ185-highlights-desktop.png`, `civ185-highlights-mobile.png`: authenticated Strateji page.
- `size-stress.txt`: synthetic 5-spot, 12-distinct-unit-card, 16-photo deck byte count.
- `baseline-comparison.txt`: comparison with the task's phase5 base templates and recipe; no-highlight unit and İdare bytes match.

Regenerate screenshots with `CIVENSA_SUNUM_SCREENSHOTS` pointing to an output directory
and run `tests/test_sunum_highlights.py` against disposable PostgreSQL 16+.
For managed Chromium, set `CIVENSA_CHROMIUM_PATH=/usr/bin/chromium` and
`CIVENSA_SUNUM_HTTP_FIXTURE=1` to serve the offline bytes through Playwright interception.
No browser network service is required.

## Fixture catalogue

The three unit fixture has complete staff and budget data. The pure catalogue
regression additionally exercises unverified actuals and duplicate exact indicator
names; neither is offered. A real second approved unit snapshot and İdare release
exercise removal of a selected indicator without changing the first release.

| Key | Display |
| --- | --- |
| `org:staff_total` | 38 kişi |
| `org:budget_final` | 6.000,00 TL |
| `org:budget_actual` | 4.600,00 TL |
| `org:budget_rate` | 76,67 yüzde |
| `unit:1:staff` | 22 kişi |
| `unit:1:spending` | 700,00 TL |
| `unit:2:staff` | 10 kişi |
| `unit:2:spending` | 1.500,00 TL |
| `unit:3:staff` | 6 kişi |
| `unit:3:spending` | 2.400,00 TL |
| `ind:1:c81c919cc3db42bd:actual` | 75 Adet |
| `ind:1:8ff75102d2d99941:actual` | 10 Adet |
| `ind:2:6f4f37de4aaa1291:actual` | 0 Adet |
| `ind:2:16f8d977604520ad:actual` | 30 Adet |

The institution budget scale is shared with its KPI. Unit spending is scaled to
millions from 1,000,000 TL; numbers and units change together. Indicator name
identity uses exact UTF-8 text, with no trimming or normalization.

The size fixture uses deterministic illustrative photos; arbitrary high-entropy
uploads can still hit the existing enforced 8 MB limit and receive its Turkish
error. No external assets are loaded.
