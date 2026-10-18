Lead's original IDML -> load Word tools (run on 15 Oct and 17 Oct).
extract.py <unzipped idml dir> tables.json ; gen.py tables.json name_map.json out.docx
gen.py drops the per-card 'Alt Program Kapsamında Yürütülecek Faaliyet Maliyetleri' tables (SMALL).
CIV-042 ports these into scripts/ with tests; this folder is reference only.
