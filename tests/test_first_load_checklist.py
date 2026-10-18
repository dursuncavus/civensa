from copy import deepcopy

import pytest

from scripts.first_load_audit import checklist, finding_actions, unique_sentences


def cell(row=2):
    return dict(page='128', table=49, row=row, column=5, book='100,00', word='100,00', book_available=True)


def finding(group='finance_missing', **kwargs):
    return dict(department='Test Müdürlüğü', side='SOURCE', group=group, key='activity:1:2027',
                error=kwargs.pop('error', 'Kaynak doğrulama mesajı.'), cells=[cell()], **kwargs)


def finances(total, inside, outside):
    return [dict(activity='0001.Park bakımı', year=2027, value_kind='budget', funding_type=fund,
                 amount=value, raw_text='' if value is None else str(value))
            for fund, value in [('total', total), ('inside', inside), ('outside', outside)]]


@pytest.mark.parametrize('inside,outside,label', [('100', None, 'Bütçe Dışı'), (None, '100', 'Bütçe İçi')])
def test_blank_funding_gives_conditional_zero_action_and_merges_paired_messages(inside, outside, label):
    first = finding(stored=finances('100', inside, outside))
    second = dict(first, group='activity_value', error='Kaynak tutarı doğrulanmalı.')
    result = checklist(dict(departments=[]), [], dict(findings=[first, second], transfers=[]))
    assert result['book_messages'] == 2
    assert len(result['items']) == 1
    action = result['items'][0]['action']
    assert f'{label} hücresi boş.' in action
    assert 'kaynak yoksa 0,00 yazın.' in action
    assert action.count('hücresi boş.') == 1
    assert 'doğrulanmalı' not in action


def test_financing_total_action_computes_expected_value_and_signed_difference():
    actions, _ = finding_actions(finding(group='activity_total', stored=finances('100', '90', '20')))
    assert '90,00 + 20,00 = 110,00, kitapta 100,00 yazıyor (fark -10,00)' in actions[0]


def economic_finding(causes):
    return finding(group='program_group', stored=[], causes=[dict(cause=c, message='Bu metin ayrıştırılmaz.') for c in causes],
        economic=dict(spec=(2027, 'budget'), categories=[
            dict(category='personnel', label='Personel', amount='80', raw_text='80', cells=[cell(2)]),
            dict(category='sgk', label='SGK', amount='20', raw_text='20', cells=[cell(3)]),
            dict(category='goods_services', label='Mal ve Hizmet', amount='100', raw_text='100', cells=[cell(4)])],
            totals={'inside': {'amount': '100'}}, personnel='100'),
        allocation_cell=dict(year=2027, kind='budget', category='personnel', funding_type='inside', amount='80', cells=[cell()]),
        book_cells=[cell()])


def test_inside_total_uses_structured_cause_and_identifies_copied_row():
    actions, notes = finding_actions(economic_finding(['inside_total_mismatch']))
    assert 'Kategori satırlarının toplamı 200,00, Bütçe İçi Toplam 100,00 (fark -100,00)' in actions[0]
    assert notes == ['Not: satır 4 (Mal ve Hizmet) toplamla aynı değeri taşıyor.']


def test_economic_blank_funding_uses_the_same_conditional_zero_rule():
    value = economic_finding(['source_cell_unverified'])
    value['economic']['totals'] = {
        'inside': dict(amount='100', raw_text='100,00', state='verified'),
        'outside': dict(amount=None, raw_text='', state='needs_review'),
        'total': dict(amount='100', raw_text='100,00', state='verified')}
    actions, _ = finding_actions(value)
    assert actions == ['Bütçe Dışı hücresi boş. Bütçe dışı kaynak yoksa 0,00 yazın.']
    value['economic']['totals']['outside']['raw_text'] = '-'
    assert '0,00 yazın' not in ' '.join(finding_actions(value)[0])


def test_ambiguous_indicator_displays_decimal_and_thousands_options():
    actions, _ = finding_actions(finding(group='indicator', stored=[{'raw_text': '132,915'}]))
    assert actions == ['Değer belirsiz: ondalık mı (132,915) binlik mi (132.915)? Doğru yazımı kitaba girin.']


def test_duplicate_sentences_keep_turkish_numbers_intact():
    assert unique_sentences(['Toplam 1.234,56. Yanlış satırı düzeltin.',
                             'Yanlış satırı düzeltin. Kaynağı kontrol edin.']) == (
        'Toplam 1.234,56. Yanlış satırı düzeltin. Kaynağı kontrol edin.')


def test_mixed_programme_message_is_split_and_counted_once():
    mixed = economic_finding(['inside_total_mismatch', 'program_group_unallocated'])
    pure = deepcopy(mixed)
    pure.update(error='Yalnız dağılım gerektiren başka hücre.', causes=[{'cause': 'program_group_unallocated', 'message': 'Dağıtılmalı.'}])
    pure['allocation_cell']['category'] = 'sgk'
    parsed = dict(departments=[dict(name='Test Müdürlüğü', blocks=[
        dict(program='Yönetim ve Destek Programı', subprogram='Üst Yönetim'),
        dict(program='Kent İçi Ulaşım', subprogram='Ulaşım')])])
    result = checklist(parsed, [], dict(findings=[mixed, pure], transfers=[]))
    assert result['book_messages'] == 1 and result['allocation_messages'] == 1
    assert result['mixed_messages'] == 1
    assert len(result['items']) == 1
    assert 'program' not in result['items'][0]['action'].lower()
    assert [c['group'] for c in result['allocations']['Test Müdürlüğü']['cards']] == ['Yönetim ve Destek', 'Hizmet']
    assert result['allocations']['Test Müdürlüğü']['messages'] == 2
    only = checklist(parsed, [], dict(findings=[pure], transfers=[]))
    assert not only['items'] and only['only_allocation'] == ['Test Müdürlüğü'] and only['clean']
    assert not checklist(dict(parsed, excluded_source_tables=[{'table_number': 195}]), [],
                         dict(findings=[pure], transfers=[]))['clean']


def test_cross_total_personnel_and_missing_explanation_actions():
    actions, _ = finding_actions(finding(group='cross_total', stored=[
        dict(activity_total='100', personnel='20', economic_total='125')]))
    assert '100,00 + ortak personel/SGK 20,00 = 120,00' in actions[0]
    assert 'ekonomik tablo toplamı 125,00 (fark 5,00)' in actions[0]
    actions, _ = finding_actions(finding(group='personnel', stored=[dict(economic_personnel='23', personnel='20')]))
    assert '23,00, ortak personel/SGK 20,00 (fark 3,00)' in actions[0]
    assert finding_actions(finding(group='explanation', stored=[]))[0] == [
        "Bu faaliyetin açıklama metnini 'Faaliyetlere İlişkin Açıklamalar' bölümüne ekleyin."]


def test_generic_action_names_exact_cell_and_rule_without_guessing_zero():
    action = finding_actions(finding(stored=finances(None, None, None)))[0][0]
    assert 's.128, tablo 49, satır 2, sütun 5' in action
    assert 'Toplam = Bütçe İçi + Bütçe Dışı olmalı' in action
    assert '0,00 yazın' not in action


def test_report_marks_directorate_waiting_only_for_allocation(monkeypatch):
    from pathlib import Path
    from scripts.first_load_dryrun import report
    pure = economic_finding(['program_group_unallocated'])
    pure['details'] = 'Program Grubu Belirlenmeli.'
    parsed = dict(departments=[dict(name='Test Müdürlüğü', blocks=[
        dict(program='Yönetim ve Destek Programı', subprogram='Üst Yönetim'),
        dict(program='Kent İçi Ulaşım', subprogram='Ulaşım')])])
    audit = dict(findings=[pure], transfers=[], counts=[])
    monkeypatch.setattr('scripts.first_load_audit.audit_results', lambda *_: audit)
    inspection = dict(results=[dict(name='Test Müdürlüğü', ready=False, warnings=[],
                                   stored={'economics': []})],
                      errors=[], plan={'conflicts': []}, unresolved=[], pending=[], applied=None)
    content = report(parsed, inspection, Path('test.idml'), 'test')
    assert 'Kitap temiz mi: **Evet**' in content
    assert 'Kitap kontrol maddesi: **0**' in content
    assert 'Yalnız program grubu dağılımı bekleyen müdürlük: **1**' in content
    assert 'Kitap açısından temiz; program grubu dağılımı bekliyor.' in content
    assert '0 kitap mesajı + 1 yalnız program grubu mesajı = 1' in content
