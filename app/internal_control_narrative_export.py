"""Narrative insertion only for the CIV-084 official Word report."""
import json
from . import internal_control_narrative_service as n
from . import internal_control_monitoring_service as m


def narrative_for_word(db, period, *, draft):
    current = n.latest(db, period.id)
    if current and not draft and current.to_status != 'approved':
        m.fail('Rapor anlatı bölümleri onaylanmadı. Strateji Müdürü onayını tamamlayın veya TASLAK indirin.', status=409)
    return current


def insert_narrative(doc, db, period, revision):
    values = json.loads(revision.snapshot_json)
    suffix = ' (taslak metin)' if revision.to_status != 'approved' else ''

    def section(label, key, level=1):
        doc.add_heading(label + suffix, level)
        for line in (values.get(key, '').splitlines() or ['']):
            doc.add_paragraph(line)

    section('Misyon', 'mission')
    section('Vizyon', 'vision')
    doc.add_heading('Bileşen değerlendirmeleri' + suffix, 1)
    for code, label in n.components(db, period):
        section(label, 'component_' + code, 2)
    section('Puan aralığı', 'band_label')
    for line in (values.get('band_explanation', '').splitlines() or ['']):
        doc.add_paragraph(line)
    section('Güçlü yönler', 'strengths')
    section('Gelişim alanları', 'improvements')
    section('Öneriler', 'recommendations')
