"""CIV-170: visible terminal confirmation, one-screen ÖZET and per-directorate progress."""
from copy import deepcopy
import json
import re

import pytest

from scripts import first_load_live as live
from tests.first_load_checkpoint import TerminalStub
from test_first_load_live import backup_files, printed, target


BOOK_2026_SHA256 = live.book_config(2026)[1]


def result_2026():
    """The execute() result shape a successful --year 2026 --apply produces."""
    return dict(mode='uygula',
                counts=dict(departments=34, created_departments=34, cards=64, indicators=263,
                            activities=291, economic_values=1340),
                departments=[dict(source_name='Sağlık İşleri Müdürlüğü', action='create',
                                  name='Sağlık İşleri Müdürlüğü')],
                skipped=[], failed=[], validation=[],
                protected_2027_before='abc123', protected_2027_after='abc123')


def argv_2026_apply():
    return ['--year', '2026', '--organization-id', '1', '--actor-id', '1',
            '--apply', '--backup', 'unused.dump']


def no_connection(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('the confirmation refusal must happen before any connection or write')
    monkeypatch.setattr('sqlalchemy.create_engine', forbidden)
    monkeypatch.setattr(live, 'execute', forbidden)
    monkeypatch.setattr('builtins.input', forbidden)  # never read a redirected stdin


def run_with_result(monkeypatch, result):
    monkeypatch.setenv(live.TARGET_ENV, 'postgresql://unused@localhost/never_connect')
    monkeypatch.setattr(live, 'verify_book', lambda path, **kwargs: dict(departments=[]))
    monkeypatch.setattr(live, 'verify_backup', lambda path: None)
    monkeypatch.setattr(live, 'execute', lambda *args, **kwargs: result)

    class Engine:
        disposed = False

        def dispose(self):
            self.disposed = True

    engine = Engine()
    monkeypatch.setattr('sqlalchemy.create_engine', lambda *args, **kwargs: engine)
    return engine


def test_prompt_is_written_to_terminal_not_stdout(monkeypatch, capsys):
    terminal = TerminalStub(BOOK_2026_SHA256[:12])
    monkeypatch.setattr(live, 'open_terminal', lambda: terminal)
    engine = run_with_result(monkeypatch, result_2026())
    assert live.main(argv_2026_apply()) == 0
    out, err = capsys.readouterr()
    assert terminal.prompt == (f'Yazma onayı: kitap SHA256 ilk 12 karakterini yazın '
                               f'({BOOK_2026_SHA256[:12]}): ')
    # Redirected stdout/stderr never hide the prompt; the terminal is the only reader.
    assert 'Yazma onayı' not in out and 'Yazma onayı' not in err
    assert engine.disposed


def test_wrong_confirmation_refuses_with_zero_rows(monkeypatch, capsys):
    monkeypatch.setenv(live.TARGET_ENV, 'postgresql://unused@localhost/never_connect')
    monkeypatch.setattr(live, 'verify_book', lambda path, **kwargs: dict(departments=[]))
    monkeypatch.setattr(live, 'verify_backup', lambda path: None)
    monkeypatch.setattr(live, 'open_terminal', lambda: TerminalStub('261cd17fd0be'))
    no_connection(monkeypatch)
    assert live.main(argv_2026_apply()) == 1
    captured = capsys.readouterr()
    assert captured.out == ''
    assert 'Kitap SHA256 onayı uyuşmuyor; 0 satır yazıldı.' in captured.err


def test_missing_terminal_refuses_with_zero_rows(monkeypatch, capsys):
    monkeypatch.setenv(live.TARGET_ENV, 'postgresql://unused@localhost/never_connect')
    monkeypatch.setattr(live, 'verify_book', lambda path, **kwargs: dict(departments=[]))
    monkeypatch.setattr(live, 'verify_backup', lambda path: None)
    monkeypatch.setattr(live, 'open_terminal', lambda: None)
    no_connection(monkeypatch)
    assert live.main(argv_2026_apply()) == 1
    captured = capsys.readouterr()
    assert captured.out == ''
    assert ('DURDU: Onay için etkileşimli terminal gerekli; komutu tee/grep olmadan '
            'doğrudan çalıştırın. 0 satır yazıldı.') in captured.err


def test_summary_is_printed_before_and_after_the_json(monkeypatch, capsys):
    monkeypatch.setattr(live, 'open_terminal', lambda: TerminalStub(BOOK_2026_SHA256[:12]))
    result = result_2026()
    run_with_result(monkeypatch, result)
    assert live.main(argv_2026_apply()) == 0
    out, err = capsys.readouterr()
    assert out.rstrip().endswith('}')  # nothing of the JSON is disturbed
    head, json_text = out.split('\n{', 1)
    assert json.loads('{' + json_text) == result
    assert out.count('ÖZET') == 1
    before = head[head.index('ÖZET'):].splitlines()
    after = err.rstrip().splitlines()
    assert before == after  # the same block is repeated as the last terminal lines
    block = '\n'.join(before)
    assert len(before) <= 15
    assert 'Mod: UYGULAMA' in block
    assert 'Yıl: 2026' in block
    assert f'Kitap SHA256: {BOOK_2026_SHA256[:12]}' in block
    assert 'Müdürlük: eşleşen 0 · oluşturulan 1 · atlanan 0 · başarısız 0' in block
    assert 'program kartı\u00a064' in block
    assert 'gösterge\u00a0263' in block
    assert 'faaliyet\u00a0291' in block
    assert 'ekonomik değer\u00a01340' in block
    assert 'Reddedilen işlem: 0 · atlanan müdürlük: 0' in block
    assert '2027 korunuyor: EVET' in block


def test_summary_reports_a_2027_change_attempt_as_hayir(monkeypatch, capsys):
    monkeypatch.setattr(live, 'open_terminal', lambda: TerminalStub(BOOK_2026_SHA256[:12]))
    result = result_2026()
    result['protected_2027_after'] = 'different'
    run_with_result(monkeypatch, result)
    assert live.main(argv_2026_apply()) == 0
    out, err = capsys.readouterr()
    assert '2027 korunuyor: HAYIR' in out.split('\n{', 1)[0]
    assert '2027 korunuyor: HAYIR' in err


def test_clear_preprint_summary_has_its_own_mode(monkeypatch, capsys):
    from scripts import clear_preprint_2027 as clear
    monkeypatch.setenv(live.TARGET_ENV, 'postgresql://unused@localhost/never_connect')
    monkeypatch.setattr(live, 'verify_book', lambda path, **kwargs: dict(departments=[]))
    monkeypatch.setattr(live, 'verify_backup', lambda path: None)
    monkeypatch.setattr(live, 'open_terminal', lambda: TerminalStub(clear.CONFIRMATION))
    result = dict(mode='clear-preprint-apply', already_cleared=False,
                  counts=dict(indicators=33, indicator_values=120, activities=10,
                              activity_cost_values=4, department_cost_values=5,
                              submission_events=0, submissions=3, subprogram_scopes=0,
                              department_scopes=0, activity_catalogue_links=2),
                  departments=[dict(department_id=1, name='Sağlık İşleri Müdürlüğü', batch_id=4,
                                    counts=dict(indicators=1, indicator_values=2, activities=0,
                                                activity_cost_values=0, department_cost_values=0,
                                                submissions=1))], batches=[3, 4])
    monkeypatch.setattr(clear, 'execute', lambda *args, **kwargs: result)

    class Engine:
        def dispose(self):
            pass
    monkeypatch.setattr('sqlalchemy.create_engine', lambda *args, **kwargs: Engine())
    assert live.main(['--clear-preprint', '--apply', '--backup', 'unused.dump',
                      '--organization-id', '1', '--actor-id', '1']) == 0
    out, err = capsys.readouterr()
    block = out.split('\n{', 1)[0]
    assert 'Mod: TEMİZLİK' in block
    assert 'Müdürlük: temizlenen 1' in block
    assert 'gösterge\u00a033' in block
    assert '2027 korunuyor' not in block


@pytest.mark.postgres
def test_progress_lines_go_to_stderr_for_plan_and_apply(target, printed, tmp_path, monkeypatch, capsys):
    engine, ids = target
    data = deepcopy(printed)
    data['departments'] = data['departments'][:2]
    names = [department['name'] for department in data['departments']]
    monkeypatch.setattr(live, 'verify_book', lambda path, **kwargs: data)
    monkeypatch.setenv(live.TARGET_ENV, engine.url.set(query={}).render_as_string(hide_password=False))
    argv = ['--organization-id', str(ids['organization_id']), '--actor-id', str(ids['actor_id'])]

    assert live.main(argv) == 0
    plan_out, plan_err = capsys.readouterr()
    progress = [line for line in plan_err.splitlines() if line.startswith('[')]
    assert len(progress) == 2
    assert progress[0].startswith(f'[1/2] {names[0]} · Oluştur · ')
    assert progress[1].startswith(f'[2/2] {names[1]} · Oluştur · ')
    assert all(re.fullmatch(r'\[\d/2\] .+ · (Oluştur|Eşleştir|Atla) · \d+\.\d sn', line)
               for line in progress)
    assert 'PLAN: Hedefe 0 satır yazıldı.' in plan_out
    assert 'ÖZET' in plan_out.split('\n{', 1)[0]
    assert plan_out.rstrip().endswith('}')

    monkeypatch.setattr(live, 'open_terminal', lambda: TerminalStub(live.BOOK_SHA256[:12]))
    dump, _ = backup_files(tmp_path)
    assert live.main(argv + ['--apply', '--backup', str(dump)]) == 0
    apply_out, apply_err = capsys.readouterr()
    progress = [line for line in apply_err.splitlines() if line.startswith('[')]
    assert len(progress) == 2
    assert progress[0].startswith(f'[1/2] {names[0]} · Yüklendi · ')
    assert progress[1].startswith(f'[2/2] {names[1]} · Yüklendi · ')
    assert all(re.fullmatch(r'\[\d/2\] .+ · Yüklendi · \d+\.\d sn', line) for line in progress)
    assert 'UYGULAMA SONUCU:' in apply_out
    assert 'Yüklendi:' not in apply_err
    assert apply_err.rstrip().splitlines()[-1].startswith('Doğrulama hatası: ')
    assert '2027 korunuyor' not in apply_err


class InterruptedTerminal(TerminalStub):
    def readline(self):
        raise KeyboardInterrupt


@pytest.mark.parametrize('terminal', [TerminalStub(eof=True), InterruptedTerminal()], ids=['eof', 'ctrl-c'])
def test_terminal_eof_and_ctrl_c_refuse_like_before(terminal, monkeypatch, capsys):
    monkeypatch.setenv(live.TARGET_ENV, 'postgresql://unused@localhost/never_connect')
    monkeypatch.setattr(live, 'verify_book', lambda path, **kwargs: dict(departments=[]))
    monkeypatch.setattr(live, 'verify_backup', lambda path: None)
    monkeypatch.setattr(live, 'open_terminal', lambda: terminal)
    no_connection(monkeypatch)
    assert live.main(argv_2026_apply()) == 1
    captured = capsys.readouterr()
    assert captured.out == ''
    assert 'DURDU: Yazma onayı alınamadı; 0 satır yazıldı.' in captured.err
