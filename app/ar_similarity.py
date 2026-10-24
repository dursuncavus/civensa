"""Read-only AR-16 advice for HTML views; never enrich report/export payloads."""
import json
import re
import unicodedata
from difflib import SequenceMatcher

from sqlalchemy import select

from . import activity_sections_service as sections
from .activity_contract_service import digest
from .models import ARDocument, ARDocumentFreeze, ARUnitWorkflowEvent, ReportingPeriod

# Strateji policy defaults live here, independently of copy/review provenance.
SIMILARITY_THRESHOLD = 85
MINIMUM_WORDS = 30
PREVIOUS_YEAR_OFFSET = 1
NUMBER_TOKEN = '#'
NUMBER_PATTERN = re.compile(r'\d+(?:[.,]\d+)*')
EXCLUDED_CODES = frozenset({sections.CORE, 'EKLER'})
EXCLUDED_CONTENT_KINDS = frozenset({'assurance'})
TURKISH_LOWERCASE = str.maketrans({'İ': 'i', 'I': 'ı'})


def normalized_words(blocks):
    """Only paragraphs and list items are narrative; table figures are excluded."""
    parts = []
    for block in blocks:
        if block.get('type') == 'paragraph':
            parts.append(block['text'])
        elif block.get('type') == 'bullets':
            parts.extend(block['items'])
    text = unicodedata.normalize('NFC', ' '.join(parts)).translate(TURKISH_LOWERCASE).lower()
    text = NUMBER_PATTERN.sub(f' {NUMBER_TOKEN} ', text)
    text = ''.join(c for c in text if c == NUMBER_TOKEN or not unicodedata.category(c).startswith('P'))
    return text.split()


def eligible(section):
    return (section['code'] not in EXCLUDED_CODES
            and section.get('content_kind') not in EXCLUDED_CONTENT_KINDS)


def load_baseline(db, doc, year):
    """Resolve exactly year-1 / organization / scope once, never a draft."""
    missing = f'Karşılaştırma yapılamadı: {year} yılı için onaylı rapor bulunamadı.'
    prior = db.scalar(select(ARDocument).join(ReportingPeriod, ReportingPeriod.id == ARDocument.period_id)
        .where(ReportingPeriod.year == year, ARDocument.organization_id == doc.organization_id,
               ARDocument.scope == doc.scope, ARDocument.department_id == doc.department_id))
    if not prior:
        return {'year': year, 'sections': {}, 'message': missing}
    if doc.department_id:
        record = db.scalar(select(ARUnitWorkflowEvent).where(ARUnitWorkflowEvent.document_id == prior.id,
            ARUnitWorkflowEvent.action == 'approve', ARUnitWorkflowEvent.to_status == 'approved')
            .order_by(ARUnitWorkflowEvent.id.desc()).limit(1))
    else:
        record = sections.latest_release(db, prior)
    if not record:
        return {'year': year, 'sections': {}, 'message': missing}
    error = (f'Karşılaştırma yapılamadı: {year} yılı onaylı rapor kopyası doğrulanamadı. '
             'Strateji veya sistem sorumlusuyla rapor sürümünü kontrol edin.')
    if not record.payload_json or digest(record.payload_json) != record.sha256:
        return {'year': year, 'sections': {}, 'message': error}
    try:
        payload = json.loads(record.payload_json)
        baseline_sections = {s['code']: s for s in payload['sections']}
        # Validate the compared blocks before using a historical stored payload.
        for section in baseline_sections.values():
            if eligible(section):
                normalized_words(section['blocks'])
    except (ValueError, KeyError, TypeError, AttributeError):
        return {'year': year, 'sections': {}, 'message': error}
    if isinstance(record, ARDocumentFreeze):
        url = f'/activity-sections/reports/{prior.id}/export.json?version={record.version}'
        label = f'{year} yılı onaylı idare raporu · Sürüm {record.version} (JSON)'
    else:
        url = f'/activity-sections/reports/{prior.id}/approvals/{record.id}.json'
        label = f'{year} yılı onaylı birim raporu · Revizyon {record.revision} (JSON)'
    return {'year': year, 'sections': baseline_sections, 'message': '',
            'source_url': url, 'source_label': label}


def compare_section(section, baseline):
    """Threshold uses the unrounded ratio; the display uses a whole percent."""
    if not eligible(section):
        return None
    current = normalized_words(section['blocks'])
    if len(current) < MINIMUM_WORDS:
        return None
    year = baseline['year']
    old = baseline['sections'].get(section['code'])
    if baseline['message'] or old is None or not eligible(old):
        return {'percent': None, 'message': baseline['message'] or
                f'Karşılaştırma yapılamadı: {year} yılı için onaylı rapor bulunamadı.'}
    ratio = SequenceMatcher(None, normalized_words(old['blocks']), current, autojunk=False).ratio() * 100
    percent = round(ratio)
    message = (f'Bu bölüm {year} yılı onaylı raporundaki aynı bölümle %{percent} benzer. '
               'Metni bu yılın gelişmelerine göre güncelleyin.') if ratio > SIMILARITY_THRESHOLD else ''
    return {'percent': percent, 'message': message,
            'source_url': baseline['source_url'], 'source_label': baseline['source_label']}


def for_report(db, user, report):
    """Separate view context: cannot become completeness blockers or frozen facts."""
    doc = sections.document(db, user, report['id'])
    # Department accounts may read some idare sections, but compare only their unit.
    if user.role != 'strategy' and doc.department_id != user.department_id:
        return {}
    candidates = [s for s in report['sections'] if eligible(s)
                  and len(normalized_words(s['blocks'])) >= MINIMUM_WORDS]
    if not candidates:
        return {}
    baseline = load_baseline(db, doc, report['year'] - PREVIOUS_YEAR_OFFSET)
    return {s['code']: compare_section(s, baseline) for s in candidates}
