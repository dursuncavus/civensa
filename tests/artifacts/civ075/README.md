# CIV-075 synthetic PDF samples

These reports contain only the disposable test fixtures (Test Belediyesi, fictional units and signatories). No live service or database was used.

- `birim-taslak.pdf` and `idare-taslak.pdf`: cover, definition order, Turkish characters, draft notes and escaped user text.
- `birim-onayli.pdf` and `idare-onayli.pdf`: frozen snapshot, resources and official assurances; repeated HTTP downloads are byte identical even after the live fixture is changed.
- `idare-mali-tablolar-taslak.pdf`: synthetic financial slots, Turkish money, null/zero, landscape tables, statements and indicators.

Regenerate with the repository development requirements installed and `CIVENSA_TEST_POSTGRES_URL` pointing to disposable PostgreSQL 16+:

```sh
CIVENSA_PDF_ARTIFACTS=tests/artifacts/civ075 CIVENSA_CHROMIUM_PATH=/usr/bin/chromium python -m pytest -q --require-postgres tests/test_activity_sections_pdf.py
```

Omit `CIVENSA_CHROMIUM_PATH` when using the Playwright-managed Chromium installed by CI. Frozen fixture hashes can differ between regeneration runs because each run creates a fresh snapshot; determinism is asserted for repeat downloads of the same frozen document. ReportLab invariant output fixes PDF timestamps and document IDs. The footer identifies the frozen source hash, which is distinct from the PDF file hash below.

These small synthetic samples do not constitute large-report pagination or official design acceptance; that remains with Ali Abi and the graphic designer.

| File | Pages | PDF SHA-256 |
| --- | ---: | --- |
| `birim-onayli.pdf` | 7 | `46e4ee1a2cf6abb48940a8f8bceee119bf42c5b6050d424b78fc7a1d63779d83` |
| `birim-taslak.pdf` | 13 | `c67097a45bddbf45b99c7b6c3e975373bc899e18e557b96cdd24cca966bf14af` |
| `idare-mali-tablolar-taslak.pdf` | 19 | `b6fa2d15f80d3c9ea57fac10221f1d21454e7abfe05accf65ca7c25439d3a46f` |
| `idare-onayli.pdf` | 7 | `df8ceed6fab1ce7f7b488ec3f404ff900c955f1731ea75d1062f7c016932f261` |
| `idare-taslak.pdf` | 15 | `4766ee15576881cc36dcdc8d12e64c2cbc4189558261feb4ce46b699ec557795` |
