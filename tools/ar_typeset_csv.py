"""python tools/ar_typeset_csv.py RAPOR.json CSV_DIZINI"""
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.ar_typeset_csv import table_csv
from app.ar_typeset_contract import verify_contract


def main():
    if len(sys.argv) != 3:
        raise SystemExit('Kullanım: python tools/ar_typeset_csv.py RAPOR.json CSV_DİZİNİ')
    contract = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    if contract.get('schema_version') != 'ar-typeset/1':
        raise SystemExit('Desteklenmeyen dizgi sözleşmesi. ar-typeset/1 JSON dosyasını kullanın.')
    if not verify_contract(contract):
        raise SystemExit('Dizgi dosyasının SHA-256 doğrulaması başarısız. Dosyayı rapor ekranından yeniden indirin.')
    directory = Path(sys.argv[2]); directory.mkdir(parents=True, exist_ok=True)
    index = {}
    for table in contract['tables']:
        filename = 'tablo-' + hashlib.sha256(table['id'].encode()).hexdigest() + '.csv'
        (directory / filename).write_bytes(table_csv(contract, table['id']))
        index[table['id']] = {'file': filename, 'title': table['title']}
    (directory / 'tablolar.json').write_text(json.dumps(index, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
