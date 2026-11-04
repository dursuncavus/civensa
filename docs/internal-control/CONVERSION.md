# İç Kontrol plan 2024–2026 → Civensa template (D-331)

Source: `source/ic-kontrol-eylem-plani-2024-2026.pdf` (SHA256 fb81c707…4a03, 63 PDF pages).
Output: `ic-kontrol-plani-2024-2026.xlsx` (CIV-048 template: Plan 13 columns + Standart Başlığı, Bilgi). Converted by the lead (D-85), 30 Oct 2026.

## Method
Action tables PDF pp. 33–37 (KOS), 39 (RDS), 41–42 (KFS), 44–45 (BİS), 46 (İS) were rotated upright and read cell by cell from the table rulings (each cell = text between ruling lines; merged cells carried to every row they span). The rotated spread's upper half is the left book page (book p. = 2×PDF p. − 2), the lower half the right one.

## Checks (DOĞRULANDI 30 Oct)
- 77 general conditions, 49 actions with a responsible unit, 98 Plan rows.
- Condition counts per standard match Table 7 (PDF p. 32) except RDS 6 and KFS 11 (2 in the tables, 3 in Table 7).
- All 28 dated actions in the tables = the 28 actions in the responsibility summary (PDF pp. 47–48); dates equal except RDS 6.2.1.
- The repository's own `parse_workbook` + `validate_source` (run against the 34 pilot department names from the first-load records) give 77 conditions / 49 actions; the only blocking items are 8 unmatched unit names, which the import screen's mapping step resolves. No warnings.
- Table 7 says 30 actions; no count of the tables gives 30 (49 actions, 28 dated, 21 continuous) → owner/Ali question.

## Machine word check (D-362, 2 Nov 2026)
Every word of every workbook cell was compared with the PDF text layer of the action pages (pdftotext, pp. 33–37, 39, 41–42, 44–46; ș→ş, hyphenation joined). Result: all text words found except code spellings, dates written as month names in the PDF, the known hyphen joins, and one real defect — Plan!E19 (KOS 1.6 Mevcut Durum) had letter-spaced text ("a k t a rı lm ış v e b u ...") copied from the PDF; fixed to "Tüm belgeler elektronik ortama aktarılmış ve bu belgelere sağlıklı bir şekilde ulaşılmaktadır." (only cell changed). This check proves words, not placement: a correct text in the wrong row is not caught → independent row-placement check by Gemini (D-362).

## Machine placement check (D-366, 3 Nov 2026)
Replaces the Gemini row check (D-364, not usable). Each action row was rebuilt from the PDF itself: word boxes from `pdftotext -bbox` (pp. 33–37, 39, 41–42, 44–46) assigned to cells by the table rulings (pdfplumber edges: column separators and, per column, row separators, so merged cells follow their span). For every action code the PDF row's Öngörülen Eylem, Sorumlu Birim, İşbirliği, Çıktı/Sonuç, Başlangıç, Bitiş and Açıklama were compared with the workbook row of the same code (ignoring spaces, hyphen joins and ș/ş; month-name dates converted).
Result (DOĞRULANDI): 49/49 actions found in the PDF, 7/7 columns equal for all 49 — 0 placement differences. The only code spelling differences are the kept source spellings in Genel Şart Kodu (e.g. `KOS.2.1`, rule 3). Two condition-only rows carry the PDF text "EYLEM UYGUN GÖRÜLMEMİŞTİR." in the responsible column (KOS 3.6.1, KOS 3.7.1) — already open question 1. Row check closed; no owner work.

## Conversion rules (lead decisions, reversible before commit)
1. Rows without a responsible unit are condition-only (D-182): action columns and Açıklama left empty. This includes the 6 actions the plan says will not be done (KOS 1.4.6, KOS 3.6.1, KOS 3.7.1, KFS 7.2.1, İS 18.1.1, İS 18.2.1) — owner/Ali to confirm.
2. One condition holds one current-state text, so the distinct Mevcut Durum texts of a condition's rows are joined in source order with line breaks.
3. Codes: İZS → İS (the system's component code); `KF.11.1.2` → `KFS.11.1.2`. Other source code spellings are kept.
4. Dates written as "09 Aralık 2024" → `09.12.2024`; "Sürekli/SÜREKLİ" kept.
5. Typos: "Tüm Müdülükler" → "Tüm Müdürlükler" (an alias cannot map to all departments); KFS 8.3.1 responsible "Mali Hizmetler Müdürlüğü Strateji Geliştirme Müdürlüğü" split into two lines; hyphenation "tanım-layarak", "öngörül-müştür" joined.
6. Unit names otherwise as in the source; mapping happens in the import screen (aliases are permanent).
7. Bilgi: title "Büyükçekmece Belediye Başkanlığı 2024-2026 İç Kontrol Uyum Eylem Planı", 2024–2026, "V. Versiyon", Onay Tarihi empty (not in the PDF).

## Open (owner / Ali Abi) — checklist page https://claude.ai/artifact/QzL9iNZkfzmgssdCYunZXF
- 6 actions without a responsible unit: keep as condition-only?
- RDS 6.2.1 dates: table 01.03.2023–01.03.2023 vs summary 02.06.2025–30.01.2026.
- RDS 6.3 and KFS 11.2 missing from the tables; PDF's RDS 6.2 text resembles the official 6.3 text (BELİRSİZ, lead's knowledge).
- KFS 10.1 second row shows a different condition text (looks like 10.2's); first kept.
- Plan approval date.
- KOS 1.1.8 responsible "Üst Yönetim İç Kontrol İzleme ve Yönlendirme Kurulu": one body or two?
- Unit mappings (8): İÇKEP Hazırlama Grubu, İKİYK Kurulu, İKİY, Üst Yönetim İç Kontrol İzleme ve Yönlendirme Kurulu, Teftiş Kurulu Müdürlüğü, Detsek Hizmetler Müdürlüğü, İnsan Kaynakları Eğitim Müdürlüğü, Afet İşleri Müdürlüğü.
