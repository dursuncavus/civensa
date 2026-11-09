"""CIV-189: guide output contract and real first-login session boundary."""
import json
from pathlib import Path
import re
import secrets

import httpx
from PIL import Image
import pytest

from app.security import hash_password
from scripts import fr_rehearsal as fr
from scripts.guide_screenshots import local_http, MAX_PNG_BYTES

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / 'docs/guides/mudurluk-fr-2026'


def test_committed_guide_contract():
    body = (GUIDE/'KILAVUZ.md').read_text()
    assert len(body.split()) <= 2500
    headings = re.findall(r'^## (.+)$', body, re.M)
    assert headings == ['Başlamadan önce', 'Giriş ve parola', 'Personel ve Müdür',
                        'Gösterge gerçekleşmesi ve kanıt', 'EK-1 bölümleri ve EK-2',
                        'Gönderme (Müdür)', 'İade ve düzeltme', 'Onay sonrası',
                        'Faaliyet sonuçları', 'Yardım', 'Daha sonra eklenecek bölümler']
    assert '[EKLENECEK — faaliyet sonucu girişi, Ali Abi cevabı bekleniyor]' not in body
    assert '[EKLENECEK — gösterge Excel ile toplu giriş]' not in body
    assert "`Excel'den içe aktar`" in body
    assert "Sorularınız ve sorunlarınız için Strateji Geliştirme Müdürlüğü'ne ulaşın." in body
    results = body.split('## Faaliyet sonuçları\n', 1)[1].split('\n## ', 1)[0]
    assert 'Her faaliyet için ayrı bir sonuç girilmez.' in results
    assert 'Gösterge gerçekleşmelerini ve kanıtlarını yukarıda anlatıldığı gibi girin.' in results
    assert "2026 faaliyetlerinden biri için kısa bir açıklama gerekiyorsa ilgili EK-1 bölümünün `Bölüm içeriği` alanına yazın." in results
    sources = [p for p in (ROOT/'app/templates').rglob('*') if p.is_file()]
    sources += [p for p in (ROOT/'app/static').rglob('*.js') if p.is_file()]
    # All quoted UI text must exist verbatim; no normalized/paraphrased labels.
    for label in set(re.findall(r'`([^`]+)`', body)):
        assert any(label in p.read_text() for p in sources), label
    filenames = {name+'.png' for name in fr.GUIDE_SHOTS.values()}
    assert len(filenames) == len(fr.GUIDE_SHOTS) <= 40
    assert {p.name for p in (GUIDE/'img').glob('*.png')} == filenames
    references = re.findall(r'!\[[^\]]*\]\(img/([^)]*)\)', body)
    assert set(references) == filenames
    rows = json.loads((ROOT/'docs/reports/civ-189/steps.json').read_text())
    assert len(rows) == len(filenames)
    assert {row['screenshot'] for row in rows} == filenames
    index = (GUIDE/'INDEX.md').read_text()
    assert 'SENTETİK' in index
    for row in rows:
        name = row['screenshot']
        assert row['role'] in {'fen_staff', 'fen_director'}
        assert fr.guide_filename(row['role'], row['step']) == name
        assert name in index
        assert row['result'] in {'OK', 'SLOW'}
        assert not row['server_errors'] and not row['js']
        assert (GUIDE/'img'/name).stat().st_size <= MAX_PNG_BYTES
        with Image.open(GUIDE/'img'/name) as png:
            assert png.size == ((390,900) if '-mobil' in name else (1440,900))


@pytest.mark.postgres
def test_guide_first_password_real_session(db, sample):
    actor = sample['user']
    password, replacement = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    actor.password_hash = hash_password(password)
    actor.must_change_password = True
    db.commit()
    data = {'guide': True, 'rehearsal': True,
            'accounts': {'department':actor.email}, 'password':password,
            '_server_errors':[]}
    with local_http(db.get_bind(),data) as base, httpx.Client(trust_env=False, headers={'Accept':'text/html'}) as browser:
        headers = {'X-Guide-Account':'department'}
        response = browser.post(base+'/login', headers=headers,
                                data={'email':actor.email, 'password':password})
        assert response.status_code == 303
        assert response.headers['location'] == '/change-password'
        response = browser.get(base+'/change-password',headers=headers)
        assert response.status_code == 200
        csrf = re.search(r'name="csrf-token" content="([^"]+)"',response.text).group(1)
        response = browser.post(base+'/api/me/change-password',
                                headers={**headers,'X-CSRF-Token':csrf},
                                json={'current_password':password,
                                      'new_password':replacement,
                                      'confirmation':replacement})
        assert response.status_code == 200
        assert browser.get(base+'/modules',headers=headers).status_code == 200
        assert browser.get(base+'/modules',headers={'X-Guide-Account':'anonymous'}).status_code == 303
        assert not data['_server_errors']


def test_guide_mode_restores_output_paths(monkeypatch):
    previous = fr.OUT, fr.SCREENS
    def fail(url, *, guide):
        assert guide
        assert fr.OUT == ROOT/'docs/reports/civ-189'
        assert fr.SCREENS == GUIDE/'img'
        raise RuntimeError('simulated capture failure')
    monkeypatch.setattr(fr, '_run', fail)
    with pytest.raises(RuntimeError):
        fr.run(None, guide=True)
    assert (fr.OUT,fr.SCREENS) == previous
    assert fr.guide_filename('strategy','Giriş ekranı') is None
