"""CIV-195: Strateji FR 2026 guide output contract and mode isolation."""
import json
from pathlib import Path
import re
import secrets

import httpx
from PIL import Image
import pytest

from app.security import hash_password
from scripts import fr_rehearsal as fr
from scripts.guide_screenshots import (
    MAX_PNG_BYTES,
    STRATEJI_GUIDE_OUT,
    STRATEJI_GUIDE_SCREENS,
    STRATEJI_GUIDE_SHOTS,
    local_http,
    strateji_guide_filename,
    strateji_guide_run,
    write_strateji_guide_index,
)

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / 'docs/guides/strateji-fr-2026'


def test_committed_strateji_guide_contract():
    body = (GUIDE / 'KILAVUZ.md').read_text(encoding='utf-8')
    assert len(body.split()) <= 2000
    headings = re.findall(r'^## (.+)$', body, re.M)
    assert headings == [
        'Başlamadan önce',
        'Hesaplar',
        '2026 yayını',
        'Rapor dönemini açma',
        'İzleme',
        'İnceleme, iade, onay',
        'Dışa aktarma',
        "Gösterge gerçekleşmelerini Excel'den aktarma",
        'Yardım',
    ]
    assert '[EKLENECEK' not in body
    assert '../mudurluk-fr-2026/KILAVUZ.md' in body
    assert 'Teknik sorunları sistem yöneticisine iletin.' in body
    for label in [
        'Rapor bölümleri ve beyanlar (EK-1)',
        'Gösterge gerçekleşmeleri',
        'Taslak — Word (onaysız)',
        'Taslak — PDF (onaysız)',
    ]:
        assert '`' + label + '`' in body
    for old in ['Faaliyet Raporu · EK-1', 'Faaliyet raporları']:
        assert '`' + old + '`' not in body
    sources = [p for p in (ROOT / 'app/templates').rglob('*') if p.is_file()]
    sources += [p for p in (ROOT / 'app/static').rglob('*.js') if p.is_file()]
    for label in set(re.findall(r'`([^`]+)`', body)):
        assert any(label in p.read_text(encoding='utf-8') for p in sources), label
    filenames = {name + '.png' for name in STRATEJI_GUIDE_SHOTS.values()}
    assert len(filenames) == len(STRATEJI_GUIDE_SHOTS) <= 30
    assert {p.name for p in (GUIDE / 'img').glob('*.png')} == filenames
    references = re.findall(r'!\[[^\]]*\]\(img/([^)]*)\)', body)
    assert references == [name + '.png' for name in STRATEJI_GUIDE_SHOTS.values()]
    rows = json.loads((STRATEJI_GUIDE_OUT / 'steps.json').read_text(encoding='utf-8'))
    assert len(rows) == len(filenames)
    assert {row['screenshot'] for row in rows} == filenames
    index = (GUIDE / 'INDEX.md').read_text(encoding='utf-8')
    assert 'SENTETİK' in index
    assert '--strateji-guide' in index
    for row in rows:
        name = row['screenshot']
        assert row['role'] == 'strategy'
        assert strateji_guide_filename(row['role'], row['step']) == name
        assert name in index
        assert row['result'] in {'OK', 'SLOW'}
        assert not row['server_errors'] and not row['js']
        assert (GUIDE / 'img' / name).stat().st_size <= MAX_PNG_BYTES
        with Image.open(GUIDE / 'img' / name) as png:
            assert png.size == (1440, 900)


@pytest.mark.postgres
def test_strateji_guide_password_reset_and_bulk_deactivate_http(db, sample):
    strategy = sample['strategy']
    staff = sample['user']
    password = secrets.token_urlsafe(32)
    strategy.password_hash = hash_password(password)
    staff.password_hash = hash_password(password)
    db.commit()

    data = {
        'guide': True,
        'rehearsal': True,
        'accounts': {'strategy': strategy.email},
        'password': password,
        '_server_errors': [],
    }
    with local_http(db.get_bind(), data) as base, httpx.Client(
        trust_env=False, headers={'Accept': 'text/html'}
    ) as browser:
        headers = {'X-Guide-Account': 'strategy'}
        login_resp = browser.post(
            base + '/login',
            headers=headers,
            data={'email': strategy.email, 'password': password},
        )
        assert login_resp.status_code == 303
        users_page = browser.get(base + '/users', headers=headers)
        assert users_page.status_code == 200
        csrf = re.search(r'name="csrf-token" content="([^"]+)"', users_page.text).group(1)
        reset_resp = browser.post(
            f'{base}/api/users/{staff.id}/reset-password',
            headers={**headers, 'X-CSRF-Token': csrf},
            json={'password': secrets.token_urlsafe(12)},
        )
        assert reset_resp.status_code == 200
        deact_resp = browser.post(
            f'{base}/api/users/bulk-deactivate',
            headers={**headers, 'X-CSRF-Token': csrf},
            json={'user_ids': [staff.id], 'reason': 'SENTETİK: yanlış grup kapatıldı.'},
        )
        assert deact_resp.status_code == 200
        assert deact_resp.json()['deactivated'] == 1
        assert not data['_server_errors']


def test_strateji_guide_mode_restores_rehearsal_globals(monkeypatch):
    previous = (
        fr.OUT,
        fr.SCREENS,
        fr.Rehearsal,
        fr.guide_filename,
        fr.write_guide_index,
        fr.setup,
    )

    def fail(url, *, guide):
        assert guide
        assert fr.OUT == STRATEJI_GUIDE_OUT
        assert fr.SCREENS == STRATEJI_GUIDE_SCREENS
        assert fr.guide_filename is strateji_guide_filename
        assert fr.write_guide_index is write_strateji_guide_index
        assert issubclass(fr.Rehearsal, previous[2])
        assert fr.Rehearsal is not previous[2]
        assert fr.setup is previous[5]
        raise RuntimeError('simulated strateji guide failure')

    monkeypatch.setattr(fr, '_run', fail)
    with pytest.raises(RuntimeError):
        strateji_guide_run(None)
    assert (
        fr.OUT,
        fr.SCREENS,
        fr.Rehearsal,
        fr.guide_filename,
        fr.write_guide_index,
        fr.setup,
    ) == previous
    assert strateji_guide_filename('fen_staff', 'Giriş ekranı') is None
    assert strateji_guide_filename('strategy', 'Giriş ekranı') == '01-giris.png'
