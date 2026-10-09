"""Phase 5B1 Activity Report unchanged-value reference / resolution engine.

Pure, side-effect-free helpers. This module performs no database, ORM, HTTP,
clock or filesystem access and never searches for a value: every input is
passed in explicitly by the caller. A successor ReportIndicator's effective
realization is EXACTLY ONE of:

  A) newly materialized content (a new ActualRevision written by the caller), or
  B) an explicit immutable reference, flattened to the terminal materialized
     source ActualRevision and bound to the IMMEDIATE predecessor release.

There is no "latest ActualRevision" lookup, no global fallback, no name/code
identity matching and no automatic rebase. Anything incomplete, ambiguous or
inconsistent fails closed with ActivityReferenceError. See
docs/phase5b1-activity-reference-contract.md.
"""
import hashlib
import json
import re
from dataclasses import dataclass
from decimal import (Context, Decimal, DivisionByZero, InvalidOperation, Overflow, ROUND_HALF_EVEN,
                     localcontext)

CONTENT_SCHEMA = 'civensa.activity-realization-content/v1'
TARGET_SCHEMA = 'civensa.activity-target-semantics/v1'
REFERENCE_SCHEMA = 'civensa.activity-unchanged-value-reference/v2'
CALCULATION_RULE = 'difference-v1'
STATES = frozenset({'verified', 'needs_review', 'missing'})
CONTRACT_VERSIONS = frozenset({'1.0', '2.0', '3.0'})
EVIDENCE_KEYS = ('title', 'locator', 'source_revision')
MAX_EVIDENCE = 30
MAX_EVIDENCE_CHARS = 50000
MAX_EXPLANATION_CHARS = 10000
MAX_DEVIATION_CHARS = 10000
MODE_MATERIALIZED = 'materialized'
MODE_REFERENCE = 'reference'
ENTRY_MODES = frozenset({MODE_MATERIALIZED, MODE_REFERENCE})
CANDIDATE_SCHEMA_V1 = 'activity-candidate-1'
# PROPOSED payload form for successor candidates (not written anywhere yet).
CANDIDATE_SCHEMA_V2 = 'activity-candidate-2'
MANIFEST_VERSION = 'report-manifest-1'
ACTIVITY_SCOPE = 'activity_report'

# parse_actual's text form, restricted to ASCII digits (no Arabic-Indic / full-width lookalikes).
_DECIMAL_TEXT = re.compile(r'[+-]?[0-9]+(?:\.[0-9]{1,6})?', re.ASCII)
_SHA256 = re.compile(r'[0-9a-f]{64}', re.ASCII)
# Explicit arithmetic context: results never depend on the ambient decimal context.
# 50 digits covers |value| < 1e20 with 6 decimals and their differences exactly.
_DECIMAL_CONTEXT = Context(prec=50, rounding=ROUND_HALF_EVEN, Emin=-999999, Emax=999999, capitals=1, clamp=0,
                           flags=[], traps=[InvalidOperation, DivisionByZero, Overflow])
_QUANTUM = Decimal('0.000001')
_VALUE_LIMIT = Decimal('1e20')
# A difference of two in-range values may reach twice the value limit.
_DELTA_LIMIT = Decimal('2e20')


class ActivityReferenceError(ValueError):
    """Fail-closed error. `code` is stable for callers; `message` is user-facing Turkish."""

    def __init__(self, code, message, field=None, details=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.field = field
        self.details = tuple(details or ())


def _fail(code, message, field=None, details=None):
    raise ActivityReferenceError(code, message, field, details)


# ---------------------------------------------------------------- canonical JSON

def _json_safe(item, field):
    """Deep copy restricted to JSON types. Floats are never accepted or normalized."""
    if item is None or isinstance(item, (str, bool)):
        return item
    if isinstance(item, float):
        _fail('float_not_allowed', 'Sayısal alanları ondalık metin olarak gönderin; kayan noktalı sayı kabul edilmez.', field)
    if isinstance(item, int):
        return item
    if isinstance(item, Decimal):
        if not item.is_finite():
            _fail('invalid_decimal', 'Sonlu bir ondalık sayı girin.', field)
        # Same text form as app.serialization.json_dumps.
        return format(item, 'f')
    if isinstance(item, (list, tuple)):
        return [_json_safe(value, field) for value in item]
    if isinstance(item, dict):
        if any(not isinstance(key, str) for key in item):
            _fail('invalid_json_key', 'Kayıt alan adları metin olmalı.', field)
        return {key: _json_safe(value, field) for key, value in item.items()}
    _fail('unsupported_type', 'Kayıt desteklenmeyen bir veri türü içeriyor.', field)


def canonical_json(value):
    """Deterministic JSON: sorted keys, compact separators, UTF-8 text, list order kept.

    Byte-identical to activity_contract_service.canonical for float-free input.
    """
    return json.dumps(_json_safe(value, 'json'), ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)


def sha256_hex(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _loads(text, field):
    if not isinstance(text, str):
        _fail('invalid_json', 'Kayıtlı içerik metin olarak okunamadı.', field)
    try:
        return json.loads(text)
    except ValueError:
        _fail('invalid_json', 'Kayıtlı içerik çözümlenemedi. Kaydın bütünlüğünü kontrol edin.', field)


# ---------------------------------------------------------------- decimals

def canonical_decimal(value, *, field='value', allow_int=False, limit=_VALUE_LIMIT):
    """Exact canonical decimal text, or None for blank. Blank is never zero.

    Accepts the decimal text form of parse_actual ('' / None = blank) and Decimal
    (as read from Numeric(26, 6) columns). Trailing zeros are removed with Decimal
    arithmetic only, so '12.5', '12.500000' and Decimal('12.500000') share one form.
    Floats, booleans, exponents, Turkish display text and >6 decimals are rejected.
    """
    if value is None or (isinstance(value, str) and value == ''):
        return None
    if isinstance(value, bool) or isinstance(value, float):
        _fail('invalid_decimal', 'Sayısal değeri ondalık metin olarak gönderin.', field)
    if isinstance(value, str):
        if not _DECIMAL_TEXT.fullmatch(value):
            _fail('invalid_decimal', 'Sonlu bir sayı ve en fazla 6 ondalık basamak girin.', field)
        number = Decimal(value)
    elif isinstance(value, Decimal):
        number = value
    elif allow_int and isinstance(value, int):
        number = Decimal(value)
    else:
        _fail('invalid_decimal', 'Sayısal değeri ondalık metin olarak gönderin.', field)
    with localcontext(_DECIMAL_CONTEXT):
        try:
            if not number.is_finite() or abs(number) >= limit or number != number.quantize(_QUANTUM):
                raise InvalidOperation()
        except InvalidOperation:
            _fail('invalid_decimal', 'Sonlu bir sayı ve en fazla 6 ondalık basamak girin.', field)
        if number == 0:
            return '0'
        return format(number.normalize(), 'f')


def _subtract(left, right):
    with localcontext(_DECIMAL_CONTEXT):
        return left - right


def _positive_int(value, field):
    if type(value) is not int or value <= 0:
        _fail('incomplete_provenance', 'Referans kaynağı eksik veya geçersiz bir kimlik içeriyor. Kaynağı açıkça belirtin.', field)
    return value


def _sha(value, field):
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        _fail('incomplete_provenance', 'Referans kaynağının bütünlük özeti eksik veya geçersiz.', field)
    return value


def _identity(value, field):
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > 36:
        _fail('incomplete_provenance', 'Kalıcı gösterge kimliği eksik veya geçersiz. Göstergeyi açık kimliğiyle bağlayın.', field)
    return value


# ---------------------------------------------------------------- realization content

def _canonical_evidence(evidence, state):
    if not isinstance(evidence, (list, tuple)) or len(evidence) > MAX_EVIDENCE:
        _fail('invalid_evidence', 'Kanıtlar en fazla 30 kaynak kaydı içermeli.', 'evidence')
    items = _json_safe(list(evidence), 'evidence')
    for source in items:
        if not isinstance(source, dict) or not all(isinstance(source.get(key), str) and source[key].strip()
                                                   for key in EVIDENCE_KEYS):
            _fail('invalid_evidence', 'Eksik kaynak kaydı: kaynak adı, konumu ve sabit kaynak sürümünü doldurun.', 'evidence')
    if state == 'verified' and not items:
        _fail('verified_without_evidence', 'Doğrulanmış gerçekleşme için en az bir tam kaynak ekleyin veya veri durumunu İncelenmeli seçin.', 'evidence')
    text = canonical_json(items)
    if len(text) > MAX_EVIDENCE_CHARS:
        _fail('invalid_evidence', 'Kanıt kaydı çok uzun.', 'evidence')
    return text


def _canonical_deviation(deviation, state):
    if not isinstance(deviation, dict):
        _fail('invalid_deviation', 'Sapma kaydı bir nesne olmalı.', 'deviation')
    data = _json_safe(deviation, 'deviation')
    if data.get('calculation_rule_version') != CALCULATION_RULE:
        _fail('invalid_deviation', 'Sapma kaydı difference-v1 hesap kuralıyla oluşturulmamış. Gerçekleşmeyi yeniden kaydedip farkı hesaplatın.', 'deviation')
    if type(data.get('target_definition_revision_id')) is not int or data['target_definition_revision_id'] <= 0:
        _fail('invalid_deviation', 'Sapma kaydı sabit hedef tanımına bağlı değil.', 'deviation')
    if 'delta' not in data or 'achievement_percent' not in data or data['achievement_percent'] is not None:
        _fail('invalid_deviation', 'Sapma kaydının hesaplanmış alanları eksik veya geçersiz.', 'deviation')
    data['delta'] = canonical_decimal(data['delta'], field='deviation', limit=_DELTA_LIMIT)
    if state != 'verified' and data['delta'] is not None:
        _fail('invalid_deviation', 'Doğrulanmamış gerçekleşme için hedef farkı hesaplanamaz.', 'deviation')
    text = canonical_json(data)
    if len(text) > MAX_DEVIATION_CHARS:
        _fail('invalid_deviation', 'Sapma kaydı çok uzun.', 'deviation')
    return text


def _normalize_content(value, state, evidence, explanation, deviation):
    if state not in STATES:
        _fail('invalid_state', 'Veri durumu tanınmıyor. Doğrulanmış, İncelenmeli veya Eksik seçin.', 'state')
    number = canonical_decimal(value)
    if state == 'verified' and number is None:
        _fail('verified_without_value', 'Doğrulanmış gerçekleşme için sayı girin. Boş değer sıfır değildir.', 'value')
    if state == 'missing' and number is not None:
        _fail('missing_with_value', 'Veri yoksa Eksik seçip alanı boş bırakın. Boş değer sıfır değildir.', 'value')
    if not isinstance(explanation, str) or len(explanation) > MAX_EXPLANATION_CHARS:
        _fail('invalid_explanation', 'Açıklama en fazla 10.000 karakterlik metin olmalı.', 'explanation')
    return number, state, _canonical_evidence(evidence, state), explanation, _canonical_deviation(deviation, state)


@dataclass(frozen=True)
class RealizationContent:
    """Immutable canonical realization content. Raw display text is not part of it."""
    value: str | None
    state: str
    evidence_json: str
    explanation: str
    deviation_json: str

    def __post_init__(self):
        if not isinstance(self.evidence_json, str) or not isinstance(self.deviation_json, str):
            _fail('invalid_content', 'Gerçekleşme içeriği kanonik biçimde değil.')
        normalized = _normalize_content(self.value, self.state, _loads(self.evidence_json, 'evidence'),
                                        self.explanation, _loads(self.deviation_json, 'deviation'))
        if normalized != (self.value, self.state, self.evidence_json, self.explanation, self.deviation_json):
            _fail('invalid_content', 'Gerçekleşme içeriği kanonik biçimde değil. content_from_fields ile oluşturun.')

    @property
    def decimal_value(self):
        return None if self.value is None else Decimal(self.value)

    @property
    def evidence(self):
        return json.loads(self.evidence_json)

    @property
    def deviation(self):
        return json.loads(self.deviation_json)

    def canonical_payload(self):
        return {'schema': CONTENT_SCHEMA, 'value': self.value, 'state': self.state, 'evidence': self.evidence,
                'explanation': self.explanation, 'deviation': self.deviation}

    def canonical_json(self):
        return canonical_json(self.canonical_payload())

    @property
    def sha256(self):
        return sha256_hex(self.canonical_json())


def content_from_fields(*, value, state, evidence, explanation, deviation):
    """Validate and canonicalize content. Inputs are copied; later caller mutation has no effect."""
    return RealizationContent(*_normalize_content(value, state, evidence, explanation, deviation))


def content_from_actual_revision(actual):
    """Duck-typed reader for an ActualRevision row (value, state, evidence_json, explanation, deviation_json)."""
    return content_from_fields(value=actual.value, state=actual.state,
                               evidence=_loads(actual.evidence_json, 'evidence'), explanation=actual.explanation,
                               deviation=_loads(actual.deviation_json, 'deviation'))


def content_from_entry(entry):
    """Reader for a package / candidate entry dict with value, state, evidence, explanation, deviation."""
    if not isinstance(entry, dict):
        _fail('invalid_content', 'Gösterge kaydı okunamadı.')
    try:
        return content_from_fields(value=entry['value'], state=entry['state'], evidence=entry['evidence'],
                                   explanation=entry['explanation'], deviation=entry['deviation'])
    except KeyError as exc:
        _fail('invalid_content', 'Gösterge kaydında gerçekleşme alanları eksik.', str(exc.args[0]))


# ---------------------------------------------------------------- indicator context

@dataclass(frozen=True)
class IndicatorContext:
    """Immutable binding of one ReportIndicator to its report revision, definition and Program base.

    Built by the caller from immutable rows only: ActivityReport, ActivityReportRevision,
    ReportIndicator, PublicationIndicatorBinding, IndicatorDefinitionRevision, IndicatorIdentity
    (identity_organization_id = IndicatorIdentity.organization_id).
    """
    organization_id: int
    activity_report_id: int
    reporting_period_id: int
    report_revision_id: int
    report_revision_number: int
    report_indicator_id: int
    persistent_indicator_id: str
    identity_organization_id: int
    definition_revision_id: int
    definition_sha256: str
    definition_json: str
    publication_id: int
    publication_sha256: str
    contract_version: str

    def __post_init__(self):
        for name in ('organization_id', 'activity_report_id', 'reporting_period_id', 'report_revision_id', 'report_revision_number',
                     'report_indicator_id', 'identity_organization_id', 'definition_revision_id', 'publication_id'):
            _positive_int(getattr(self, name), name)
        _identity(self.persistent_indicator_id, 'persistent_indicator_id')
        if self.identity_organization_id != self.organization_id:
            _fail('identity_organization_mismatch', 'Kalıcı gösterge kimliği başka bir kuruma ait. Göstergeyi kendi kurumunun kimliğiyle bağlayın.', 'identity_organization_id')
        _sha(self.definition_sha256, 'definition_sha256')
        _sha(self.publication_sha256, 'publication_sha256')
        if self.contract_version not in CONTRACT_VERSIONS:
            _fail('unsupported_contract', 'Yayın veri sözleşmesinin sürümü desteklenmiyor.', 'contract_version')
        if not isinstance(self.definition_json, str) or sha256_hex(self.definition_json) != self.definition_sha256:
            _fail('definition_integrity', 'Gösterge tanımının bütünlüğü doğrulanamadı. Strateji birimine başvurun.', 'definition_sha256')
        definition = _loads(self.definition_json, 'definition_json')
        if not isinstance(definition, dict) or not isinstance(definition.get('targets'), list):
            _fail('definition_integrity', 'Gösterge tanımının hedef yapısı doğrulanamadı.', 'definition_json')
        if type(definition.get('year')) is not int or definition['year'] <= 0:
            _fail('definition_integrity', 'Gösterge tanımının raporlama yılı doğrulanamadı.', 'definition_json')
        # v1 definitions carry no marker; v2/v3 must carry their own contract version.
        marker = definition.get('definition_contract_version')
        if (self.contract_version == '1.0' and marker is not None) or (self.contract_version != '1.0' and marker != self.contract_version):
            _fail('definition_integrity', 'Gösterge tanımı yayın veri sözleşmesiyle uyuşmuyor.', 'definition_json')
        _target_semantics(definition['targets'])

    @property
    def targets(self):
        return json.loads(self.definition_json)['targets']

    @property
    def reporting_year(self):
        return json.loads(self.definition_json)['year']

    @property
    def effective_target(self):
        """difference-v1 target exactly as activity_contract_service.save_actual derives it."""
        effective = _target_semantics(self.targets)['effective_target']
        return None if effective is None else Decimal(effective)

    @property
    def target_semantics_sha256(self):
        return sha256_hex(canonical_json(_target_semantics(self.targets)))

    def binding(self):
        return {'organization_id': self.organization_id, 'activity_report_id': self.activity_report_id,
                'reporting_period_id': self.reporting_period_id, 'reporting_year': self.reporting_year,
                'persistent_indicator_id': self.persistent_indicator_id,
                'definition_revision_id': self.definition_revision_id, 'definition_sha256': self.definition_sha256,
                'target_semantics_sha256': self.target_semantics_sha256, 'publication_id': self.publication_id,
                'publication_sha256': self.publication_sha256, 'contract_version': self.contract_version}


def _target_semantics(targets):
    rows = []
    for target in targets:
        if not isinstance(target, dict) or target.get('state') not in STATES or not isinstance(target.get('value_kind'), str):
            _fail('definition_integrity', 'Gösterge tanımındaki hedef kaydı doğrulanamadı.', 'targets')
        year = target.get('year')
        if type(year) is not int:
            _fail('definition_integrity', 'Gösterge tanımındaki hedef yılı doğrulanamadı.', 'targets')
        rows.append({'year': year, 'value_kind': target['value_kind'], 'state': target['state'],
                     'value': canonical_decimal(target.get('value'), field='targets', allow_int=True)})
    effective = None
    if len(rows) == 1 and rows[0]['state'] == 'verified' and rows[0]['value'] is not None:
        effective = rows[0]['value']
    return {'schema': TARGET_SCHEMA, 'calculation_rule_version': CALCULATION_RULE, 'targets': rows,
            'effective_target': effective}


def verify_content_for_context(content, context):
    """difference-v1 must be bound to this definition revision and recomputable from its target."""
    if not isinstance(content, RealizationContent) or not isinstance(context, IndicatorContext):
        _fail('invalid_input', 'Gerçekleşme içeriği ve gösterge bağlamı açıkça verilmeli.')
    deviation = content.deviation
    if deviation['target_definition_revision_id'] != context.definition_revision_id:
        _fail('deviation_definition_mismatch', 'Hedef farkı başka bir gösterge tanımına göre hesaplanmış. Gerçekleşmeyi yeni kayıtla girip farkı yeniden hesaplatın.', 'deviation')
    target = context.effective_target
    expected = _subtract(content.decimal_value, target) if content.state == 'verified' and target is not None else None
    delta = deviation['delta']
    if (expected is None) != (delta is None) or (expected is not None and Decimal(delta) != expected):
        _fail('deviation_mismatch', 'Hedef farkı sabit tanıma göre uyuşmuyor. Gerçekleşmeyi yeni kayıtla girip farkı yeniden hesaplatın.', 'deviation')


# ---------------------------------------------------------------- released candidate / release provenance

def _release_fail(message, field=None):
    _fail('release_provenance_mismatch', message + ' Değişmeyen değer referansı kullanılamaz.', field)


@dataclass(frozen=True)
class ReleaseRecord:
    """Immutable ReportRelease facts plus the frozen ActivityReportApproval's report revision."""
    release_id: int
    organization_id: int
    resource_scope: str
    report_key: str
    release_major: int
    release_minor: int
    candidate_id: int
    activity_approval_id: int
    approval_report_revision_id: int

    def __post_init__(self):
        for name in ('release_id', 'organization_id', 'candidate_id', 'activity_approval_id', 'approval_report_revision_id'):
            _positive_int(getattr(self, name), name)
        if self.resource_scope != ACTIVITY_SCOPE:
            _release_fail('Kaynak yayın bir Faaliyet Raporu yayını değil.', 'resource_scope')
        if not isinstance(self.report_key, str) or not self.report_key or len(self.report_key) > 100:
            _fail('incomplete_provenance', 'Yayının rapor anahtarı eksik veya geçersiz.', 'report_key')
        if type(self.release_major) is not int or self.release_major < 1:
            _fail('incomplete_provenance', 'Yayın sürümü geçersiz.', 'release_major')
        if type(self.release_minor) is not int or self.release_minor < 0:
            _fail('incomplete_provenance', 'Yayın sürümü geçersiz.', 'release_minor')

    @property
    def version(self):
        return (self.release_major, self.release_minor)


@dataclass(frozen=True)
class CandidateSnapshot:
    """Immutable ReportCandidate row. Hashes are recomputed exactly as report_workflow_service does."""
    candidate_id: int
    organization_id: int
    period_id: int
    resource_scope: str
    report_key: str
    activity_revision_id: int
    payload_json: str
    payload_sha256: str
    manifest_json: str
    sha256: str

    def __post_init__(self):
        for name in ('candidate_id', 'organization_id', 'period_id', 'activity_revision_id'):
            _positive_int(getattr(self, name), name)
        _sha(self.payload_sha256, 'payload_sha256')
        _sha(self.sha256, 'sha256')
        if self.resource_scope != ACTIVITY_SCOPE or not isinstance(self.report_key, str) or not self.report_key:
            _release_fail('Rapor adayı bir Faaliyet Raporu adayı değil.', 'resource_scope')
        if not isinstance(self.payload_json, str) or sha256_hex(self.payload_json) != self.payload_sha256:
            _fail('candidate_integrity', 'Rapor adayının içerik bütünlüğü doğrulanamadı. Referans kullanılamaz.', 'payload_sha256')
        payload = _loads(self.payload_json, 'payload_json')
        manifest = _loads(self.manifest_json, 'manifest_json')
        # report_workflow_service.hash_content: digest(canonical({'manifest': ..., 'payload': ...})).
        if sha256_hex(canonical_json({'manifest': manifest, 'payload': payload})) != self.sha256:
            _fail('candidate_integrity', 'Rapor adayının bütünlük özeti doğrulanamadı. Referans kullanılamaz.', 'sha256')
        if (not isinstance(manifest, dict) or manifest.get('version') != MANIFEST_VERSION
                or manifest.get('resource_scope') != ACTIVITY_SCOPE or manifest.get('organization_id') != self.organization_id
                or manifest.get('period_id') != self.period_id):
            _release_fail('Rapor adayının bildirim kaydı kurum, dönem veya rapor türüyle uyuşmuyor.', 'manifest_json')
        if (not isinstance(payload, dict) or payload.get('schema_version') not in {CANDIDATE_SCHEMA_V1, CANDIDATE_SCHEMA_V2}
                or payload.get('report_revision_id') != self.activity_revision_id or not isinstance(payload.get('entries'), list)):
            _release_fail('Rapor adayı içeriği desteklenmiyor veya rapor revizyonuyla uyuşmuyor.', 'payload_json')
        if payload['schema_version'] == CANDIDATE_SCHEMA_V2:
            keys = ('predecessor_release_id', 'predecessor_candidate_id', 'predecessor_candidate_sha256')
            values = [payload.get(key, 'absent') for key in keys]
            if 'absent' in values or (any(v is None for v in values) and any(v is not None for v in values)):
                _release_fail('Ardıl rapor adayının önceki yayın bağlantısı eksik.', 'payload_json')
            if values[0] is not None:
                _positive_int(values[0], 'predecessor_release_id')
                _positive_int(values[1], 'predecessor_candidate_id')
                _sha(values[2], 'predecessor_candidate_sha256')

    @property
    def payload(self):
        return json.loads(self.payload_json)

    def entry_for(self, report_indicator_id):
        """Explicit key lookup of one materialized indicator; never 'latest', never by name/code."""
        payload = self.payload
        key = ('materialized_report_indicator_id' if payload['schema_version'] == CANDIDATE_SCHEMA_V1
               else 'successor_report_indicator_id')
        found = [e for e in payload['entries'] if isinstance(e, dict) and e.get(key) == report_indicator_id]
        if len(found) != 1:
            _release_fail('Gösterge yayımlanan rapor adayında tam olarak bir kez bulunmuyor.', key)
        return found[0]


_MATERIALIZED_KEYS = frozenset({'mode', 'actual_revision_id', 'content_sha256'})
_REFERENCE_REALIZATION_KEYS = frozenset({'mode', 'reference_sha256', 'source_release_id', 'source_actual_revision_id',
                                         'predecessor_release_id', 'content_sha256'})


def _entry_realization(schema_version, entry):
    if schema_version == CANDIDATE_SCHEMA_V1:
        return {'mode': MODE_MATERIALIZED,
                'actual_revision_id': _positive_int(entry.get('materialized_actual_revision_id'), 'materialized_actual_revision_id')}
    realization = entry.get('realization')
    if not isinstance(realization, dict) or realization.get('mode') not in ENTRY_MODES:
        _release_fail('Rapor adayı kaydının gerçekleşme türü belirtilmemiş.', 'realization')
    keys = _MATERIALIZED_KEYS if realization['mode'] == MODE_MATERIALIZED else _REFERENCE_REALIZATION_KEYS
    if set(realization) != keys:
        _release_fail('Rapor adayı kaydının gerçekleşme bilgisi eksik veya fazla alan içeriyor.', 'realization')
    for key, value in realization.items():
        if key.endswith('_sha256'):
            _sha(value, f'realization.{key}')
        elif key != 'mode':
            _positive_int(value, f'realization.{key}')
    return realization


@dataclass(frozen=True)
class ReleasedIndicator:
    """One indicator exactly as a published release holds it.

    The entry mode and the materialized ActualRevision ID come from the hash-verified
    candidate payload, never from the caller. A reference entry must supply its
    UnchangedValueReference; a materialized entry must not.
    """
    context: IndicatorContext
    release: ReleaseRecord
    candidate: CandidateSnapshot
    content: RealizationContent
    reference: 'UnchangedValueReference | None' = None

    def __post_init__(self):
        if (not isinstance(self.context, IndicatorContext) or not isinstance(self.release, ReleaseRecord)
                or not isinstance(self.candidate, CandidateSnapshot) or not isinstance(self.content, RealizationContent)):
            _fail('incomplete_provenance', 'Yayımlanmış gösterge için bağlam, yayın, rapor adayı ve içerik açıkça verilmeli.')
        context, release, candidate = self.context, self.release, self.candidate
        verify_content_for_context(self.content, context)
        if release.candidate_id != candidate.candidate_id:
            _release_fail('Yayın başka bir rapor adayına ait.', 'candidate_id')
        if not release.organization_id == candidate.organization_id == context.organization_id:
            _release_fail('Yayın, rapor adayı ve gösterge aynı kuruma ait değil.', 'organization_id')
        if release.report_key != candidate.report_key:
            _release_fail('Yayın ve rapor adayının rapor anahtarı uyuşmuyor.', 'report_key')
        if candidate.period_id != context.reporting_period_id:
            _release_fail('Rapor adayı başka bir raporlama dönemine ait.', 'period_id')
        if not candidate.activity_revision_id == release.approval_report_revision_id == context.report_revision_id:
            _release_fail('Yayının onaylı rapor revizyonu göstergenin revizyonuyla uyuşmuyor.', 'report_revision_id')
        payload = candidate.payload
        if (payload.get('publication_id') != context.publication_id or payload.get('publication_sha256') != context.publication_sha256
                or payload.get('contract_version') != context.contract_version):
            _release_fail('Rapor adayının Performans Programı yayını göstergenin bazıyla uyuşmuyor.', 'publication_id')
        entry = candidate.entry_for(context.report_indicator_id)
        if entry.get('definition_revision_id') != context.definition_revision_id:
            _release_fail('Rapor adayındaki gösterge tanım sürümü uyuşmuyor.', 'definition_revision_id')
        if content_from_entry(entry).sha256 != self.content.sha256:
            _fail('source_content_mismatch', 'Gerçekleşme içeriği yayımlanan rapor adayıyla uyuşmuyor. Değişmeyen değer referansı kullanılamaz.')
        realization = _entry_realization(payload['schema_version'], entry)
        if 'content_sha256' in realization and realization['content_sha256'] != self.content.sha256:
            _fail('source_content_mismatch', 'Rapor adayındaki içerik özeti gerçekleşmeyle uyuşmuyor.')
        if realization['mode'] == MODE_MATERIALIZED:
            if self.reference is not None:
                _fail('ambiguous_realization', 'Yayında yeni girilmiş bir gerçekleşme için ayrıca referans verilmiş.')
            return
        reference = self.reference
        if not isinstance(reference, UnchangedValueReference):
            _fail('reference_missing', 'Yayındaki değer önceki sürüme referans; bu referans açıkça verilmeli.')
        UnchangedValueReference(reference.provenance_json, reference.reference_sha256)
        stored = reference.payload
        if (reference.reference_sha256 != realization['reference_sha256']
                or stored['successor'] != _successor_section(context) or stored['binding'] != context.binding()
                or stored['content_sha256'] != self.content.sha256
                or stored['source']['release_id'] != realization['source_release_id']
                or stored['source']['actual_revision_id'] != realization['source_actual_revision_id']
                or stored['predecessor']['release_id'] != realization['predecessor_release_id']
                or stored['predecessor']['release_id'] != payload.get('predecessor_release_id')
                or stored['predecessor']['candidate_id'] != payload.get('predecessor_candidate_id')
                or stored['predecessor']['candidate_sha256'] != payload.get('predecessor_candidate_sha256')
                or (stored['predecessor']['release_major'], stored['predecessor']['release_minor']) >= release.version):
            _fail('predecessor_reference_mismatch', 'Yayındaki referans kaydı rapor adayıyla uyuşmuyor. Referans kullanılamaz.')

    @property
    def mode(self):
        return MODE_MATERIALIZED if self.reference is None else MODE_REFERENCE

    def flattened_source(self):
        """Terminal materialized ActualRevision provenance this indicator's content comes from."""
        if self.reference is not None:
            return self.reference.payload['source']
        entry = self.candidate.entry_for(self.context.report_indicator_id)
        actual_id = _entry_realization(self.candidate.payload['schema_version'], entry)['actual_revision_id']
        return {'release_id': self.release.release_id, 'release_major': self.release.release_major,
                'release_minor': self.release.release_minor, 'candidate_id': self.candidate.candidate_id,
                'candidate_sha256': self.candidate.sha256, 'activity_approval_id': self.release.activity_approval_id,
                'report_revision_id': self.context.report_revision_id,
                'report_revision_number': self.context.report_revision_number,
                'report_indicator_id': self.context.report_indicator_id, 'actual_revision_id': actual_id}

    def predecessor_section(self):
        return {'release_id': self.release.release_id, 'release_major': self.release.release_major,
                'release_minor': self.release.release_minor, 'candidate_id': self.candidate.candidate_id,
                'candidate_sha256': self.candidate.sha256, 'activity_approval_id': self.release.activity_approval_id,
                'report_revision_id': self.context.report_revision_id,
                'report_revision_number': self.context.report_revision_number,
                'report_indicator_id': self.context.report_indicator_id, 'entry_mode': self.mode,
                'materialized_actual_revision_id': (None if self.reference else self.flattened_source()['actual_revision_id']),
                'predecessor_reference_sha256': self.reference.reference_sha256 if self.reference else None,
                'content_sha256': self.content.sha256}


@dataclass(frozen=True)
class SuccessorTarget:
    """A successor ReportIndicator plus the immediate predecessor release its lineage declares.

    The predecessor fields come from the host's succession lineage (successor candidate's
    predecessor). All three are None for a first release, which can only materialize.
    """
    context: IndicatorContext
    predecessor_release_id: int | None = None
    predecessor_candidate_id: int | None = None
    predecessor_candidate_sha256: str | None = None

    def __post_init__(self):
        if not isinstance(self.context, IndicatorContext):
            _fail('invalid_input', 'Ardıl gösterge bağlamı açıkça verilmeli.')
        values = (self.predecessor_release_id, self.predecessor_candidate_id, self.predecessor_candidate_sha256)
        if all(value is None for value in values):
            return
        _positive_int(self.predecessor_release_id, 'predecessor_release_id')
        _positive_int(self.predecessor_candidate_id, 'predecessor_candidate_id')
        _sha(self.predecessor_candidate_sha256, 'predecessor_candidate_sha256')

    @property
    def has_predecessor(self):
        return self.predecessor_release_id is not None


# ---------------------------------------------------------------- eligibility

@dataclass(frozen=True)
class Mismatch:
    code: str
    message: str


@dataclass(frozen=True)
class Eligibility:
    eligible: bool
    mismatches: tuple


_NEW_RECORD = ' Değişmeyen değer referansı kullanılamaz; yeni gerçekleşme kaydı oluşturun.'
_CONTEXT_CHECKS = (
    ('organization_id', 'organization_mismatch', 'Önceki sürümdeki gösterge başka bir kuruma ait.'),
    ('activity_report_id', 'report_mismatch', 'Önceki sürümdeki gösterge başka bir Faaliyet Raporuna ait.'),
    ('reporting_period_id', 'reporting_period_mismatch', 'Önceki sürümdeki gösterge başka bir raporlama dönemine ait.'),
    ('reporting_year', 'reporting_period_mismatch', 'Gösterge tanımının raporlama yılı önceki sürümden farklı.'),
    ('persistent_indicator_id', 'identity_mismatch', 'Kalıcı gösterge kimliği önceki sürümle aynı değil.'),
    ('definition_revision_id', 'definition_revision_mismatch', 'Gösterge tanım sürümü değişmiş.'),
    ('definition_sha256', 'definition_hash_mismatch', 'Gösterge tanımının içeriği değişmiş.'),
    ('target_semantics_sha256', 'target_mismatch', 'Göstergenin hedefi değişmiş.'),
    ('publication_id', 'program_base_mismatch', 'Rapor farklı bir Performans Programı yayınına bağlı.'),
    ('publication_sha256', 'program_base_mismatch', 'Performans Programı yayınının içeriği farklı.'),
    ('contract_version', 'program_base_mismatch', 'Yayın veri sözleşmesi sürümü farklı.'),
)
_CONTENT_CHECKS = (
    ('value', 'value_changed', 'Gerçekleşme değeri önceki sürümden farklı.'),
    ('state', 'state_changed', 'Veri durumu önceki sürümden farklı.'),
    ('evidence_json', 'evidence_changed', 'Kanıt kayıtları veya sıraları önceki sürümden farklı.'),
    ('explanation', 'explanation_changed', 'Açıklama önceki sürümden farklı.'),
    ('deviation_json', 'deviation_changed', 'Sapma kaydı önceki sürümden farklı.'),
)


def _context_mismatches(older, newer):
    found = []
    for name, code, message in _CONTEXT_CHECKS:
        if getattr(older, name) != getattr(newer, name):
            found.append(Mismatch(code, message + _NEW_RECORD))
    if (newer.report_revision_number <= older.report_revision_number or newer.report_revision_id == older.report_revision_id
            or newer.report_indicator_id == older.report_indicator_id):
        found.append(Mismatch('not_a_successor', 'Referans yalnız daha yeni bir rapor revizyonundaki göstergeden önceki sürüme verilebilir.'))
    return found


def _dedupe(found):
    seen, result = set(), []
    for mismatch in found:
        if mismatch not in seen:
            seen.add(mismatch); result.append(mismatch)
    return result


def _lineage_mismatches(successor, predecessor, source):
    found = []
    if not successor.has_predecessor:
        return [Mismatch('predecessor_missing', 'Ardıl revizyonun önceki yayını belirtilmemiş; ilk yayında yalnız yeni gerçekleşme girilebilir.')]
    if (predecessor.release.release_id != successor.predecessor_release_id
            or predecessor.candidate.candidate_id != successor.predecessor_candidate_id
            or predecessor.candidate.sha256 != successor.predecessor_candidate_sha256):
        found.append(Mismatch('predecessor_mismatch', 'Referans yalnız hemen önceki yayına verilebilir; verilen yayın ardıl revizyonun önceki yayını değil.'))
    if source.mode != MODE_MATERIALIZED:
        found.append(Mismatch('source_not_materialized', 'Kaynak, gerçekleşmenin ilk girildiği yayın olmalı (zincirin ucundaki gerçek kayıt).'))
    elif predecessor.flattened_source() != source.flattened_source():
        found.append(Mismatch('lineage_mismatch', 'Önceki yayındaki değer bu kaynaktan gelmiyor. Değişmeyen değer yalnız hemen önceki yayındaki değere bağlanabilir.'))
    if predecessor.content.sha256 != source.content.sha256:
        found.append(Mismatch('lineage_mismatch', 'Önceki yayındaki değer kaynak gerçekleşmeyle aynı değil.'))
    same_release = predecessor.release.release_id == source.release.release_id
    if (predecessor.release.report_key != source.release.report_key
            or (not same_release and predecessor.release.version <= source.release.version)):
        found.append(Mismatch('release_order_invalid', 'Önceki yayın ile kaynak yayının sürüm sırası geçersiz.'))
    return found


def _check_types(successor, predecessor, source):
    if not isinstance(successor, SuccessorTarget):
        _fail('invalid_input', 'Ardıl gösterge ve önceki yayın bağlantısı açıkça verilmeli.')
    if not isinstance(predecessor, ReleasedIndicator) or not isinstance(source, ReleasedIndicator):
        _fail('reference_source_missing', 'Hemen önceki yayın ve kaynak gerçekleşme açıkça verilmeli; sistem başka bir değer aramaz.')


def check_reference_eligibility(successor, predecessor, source, proposed):
    """May `proposed` successor content be represented by a reference?

    Content must equal the IMMEDIATE predecessor's effective content; the reference is
    flattened to the predecessor's terminal materialized source. Every mismatch is reported.
    """
    _check_types(successor, predecessor, source)
    if not isinstance(proposed, RealizationContent):
        _fail('invalid_input', 'Önerilen gerçekleşme içeriği kanonik biçimde verilmeli.')
    found = _lineage_mismatches(successor, predecessor, source)
    found += _context_mismatches(predecessor.context, successor.context)
    found += _context_mismatches(source.context, successor.context)
    for name, code, message in _CONTENT_CHECKS:
        if getattr(predecessor.content, name) != getattr(proposed, name):
            found.append(Mismatch(code, message + _NEW_RECORD))
    try:
        verify_content_for_context(proposed, successor.context)
    except ActivityReferenceError as exc:
        found.append(Mismatch(exc.code, exc.message))
    found = _dedupe(found)
    return Eligibility(not found, tuple(found))


def require_reference_eligibility(successor, predecessor, source, proposed):
    result = check_reference_eligibility(successor, predecessor, source, proposed)
    if not result.eligible:
        first = result.mismatches[0]
        _fail(first.code, first.message, details=result.mismatches)
    return result


# ---------------------------------------------------------------- reference provenance

_SUCCESSOR_KEYS = frozenset({'organization_id', 'activity_report_id', 'reporting_period_id', 'report_revision_id',
                             'report_revision_number', 'report_indicator_id'})
_RELEASE_KEYS = frozenset({'release_id', 'release_major', 'release_minor', 'candidate_id', 'candidate_sha256',
                           'activity_approval_id', 'report_revision_id', 'report_revision_number', 'report_indicator_id'})
_SOURCE_KEYS = _RELEASE_KEYS | {'actual_revision_id'}
_PREDECESSOR_KEYS = _RELEASE_KEYS | {'entry_mode', 'materialized_actual_revision_id', 'predecessor_reference_sha256',
                                     'content_sha256'}
_BINDING_KEYS = frozenset({'organization_id', 'activity_report_id', 'reporting_period_id', 'reporting_year',
                           'persistent_indicator_id', 'definition_revision_id', 'definition_sha256',
                           'target_semantics_sha256', 'publication_id', 'publication_sha256', 'contract_version'})
_TOP_KEYS = frozenset({'schema', 'calculation_rule_version', 'successor', 'predecessor', 'source', 'binding',
                       'content_sha256'})
_SHARED_RELEASE_KEYS = sorted(_RELEASE_KEYS)


def _successor_section(context):
    return {'organization_id': context.organization_id, 'activity_report_id': context.activity_report_id,
            'reporting_period_id': context.reporting_period_id, 'report_revision_id': context.report_revision_id,
            'report_revision_number': context.report_revision_number, 'report_indicator_id': context.report_indicator_id}


def _reference_payload(successor, predecessor, source):
    return {'schema': REFERENCE_SCHEMA, 'calculation_rule_version': CALCULATION_RULE,
            'successor': _successor_section(successor.context), 'predecessor': predecessor.predecessor_section(),
            'source': source.flattened_source(), 'binding': successor.context.binding(),
            'content_sha256': source.content.sha256}


def _structure_fail(message, field=None):
    _fail('incomplete_provenance', message, field)


def _check_structure(payload):
    if not isinstance(payload, dict) or set(payload) != _TOP_KEYS:
        _structure_fail('Değişmeyen değer referansı eksik veya fazla alan içeriyor.')
    if payload['schema'] != REFERENCE_SCHEMA or payload['calculation_rule_version'] != CALCULATION_RULE:
        _fail('unsupported_reference', 'Değişmeyen değer referansının sürümü desteklenmiyor.')
    for name, keys in (('successor', _SUCCESSOR_KEYS), ('predecessor', _PREDECESSOR_KEYS), ('source', _SOURCE_KEYS),
                       ('binding', _BINDING_KEYS)):
        if not isinstance(payload[name], dict) or set(payload[name]) != keys:
            _structure_fail('Değişmeyen değer referansının kaynak bilgisi eksik.', name)
        for key, value in payload[name].items():
            field = f'{name}.{key}'
            if key == 'predecessor_reference_sha256':
                if value is not None:
                    _sha(value, field)
            elif key == 'materialized_actual_revision_id':
                if value is not None:
                    _positive_int(value, field)
            elif key.endswith('_sha256'):
                _sha(value, field)
            elif key == 'persistent_indicator_id':
                _identity(value, field)
            elif key == 'contract_version':
                if value not in CONTRACT_VERSIONS:
                    _structure_fail('Referansın veri sözleşmesi sürümü geçersiz.', field)
            elif key == 'entry_mode':
                if value not in ENTRY_MODES:
                    _structure_fail('Önceki yayın kaydının gerçekleşme türü geçersiz.', field)
            elif key == 'release_minor':
                if type(value) is not int or value < 0:
                    _structure_fail('Referanstaki yayın sürümü geçersiz.', field)
            else:
                _positive_int(value, field)
    _sha(payload['content_sha256'], 'content_sha256')
    # Internal relationships that hold without any database access.
    successor, predecessor, source, binding = (payload[k] for k in ('successor', 'predecessor', 'source', 'binding'))
    if any(successor[k] != binding[k] for k in ('organization_id', 'activity_report_id', 'reporting_period_id')):
        _structure_fail('Referansın ardıl gösterge ve bağlama bilgileri uyuşmuyor.', 'binding')
    if predecessor['content_sha256'] != payload['content_sha256']:
        _structure_fail('Önceki yayındaki içerik referans alınan içerikle aynı değil.', 'predecessor.content_sha256')
    if not successor['report_revision_number'] > predecessor['report_revision_number'] >= source['report_revision_number']:
        _structure_fail('Referanstaki revizyon sırası geçersiz.', 'report_revision_number')
    shared_equal = all(predecessor[k] == source[k] for k in _SHARED_RELEASE_KEYS)
    if predecessor['entry_mode'] == MODE_MATERIALIZED:
        if (predecessor['predecessor_reference_sha256'] is not None or not shared_equal
                or predecessor['materialized_actual_revision_id'] != source['actual_revision_id']):
            _structure_fail('Önceki yayındaki değer yeni girilmişse kaynak o yayının kendisi olmalı.', 'predecessor')
    else:
        if (predecessor['predecessor_reference_sha256'] is None or predecessor['materialized_actual_revision_id'] is not None
                or predecessor['release_id'] == source['release_id']
                or (predecessor['release_major'], predecessor['release_minor']) <= (source['release_major'], source['release_minor'])
                or predecessor['report_revision_number'] <= source['report_revision_number']):
            _structure_fail('Önceki yayındaki referans zinciri geçersiz.', 'predecessor')


@dataclass(frozen=True)
class UnchangedValueReference:
    """Immutable reference: canonical provenance JSON plus its SHA-256.

    Suitable for a later append-only reference row storing exactly these two columns
    (plus indexed copies of the IDs, which must equal the JSON).
    """
    provenance_json: str
    reference_sha256: str

    def __post_init__(self):
        if not isinstance(self.reference_sha256, str) or not _SHA256.fullmatch(self.reference_sha256):
            _fail('reference_hash_invalid', 'Değişmeyen değer referansının bütünlük özeti geçersiz.')
        payload = _loads(self.provenance_json, 'provenance_json')
        _check_structure(payload)
        if canonical_json(payload) != self.provenance_json:
            _fail('reference_not_canonical', 'Değişmeyen değer referansı kanonik biçimde değil.')
        if sha256_hex(self.provenance_json) != self.reference_sha256:
            _fail('reference_hash_invalid', 'Değişmeyen değer referansının bütünlüğü doğrulanamadı. Referans kullanılamaz.')

    @property
    def payload(self):
        return json.loads(self.provenance_json)


def build_reference(successor, predecessor, source, proposed):
    """Construct a reference only for content unchanged against the immediate predecessor."""
    require_reference_eligibility(successor, predecessor, source, proposed)
    text = canonical_json(_reference_payload(successor, predecessor, source))
    return UnchangedValueReference(text, sha256_hex(text))


def verify_reference(reference, *, successor, predecessor, source):
    """Fail closed unless the reference binds exactly this successor, immediate predecessor and source."""
    if not isinstance(reference, UnchangedValueReference):
        _fail('incomplete_provenance', 'Değişmeyen değer referansı açıkça verilmeli.')
    _check_types(successor, predecessor, source)
    # Re-check hash/structure even if the instance was altered after construction.
    UnchangedValueReference(reference.provenance_json, reference.reference_sha256)
    found = _dedupe(_lineage_mismatches(successor, predecessor, source)
                    + _context_mismatches(predecessor.context, successor.context)
                    + _context_mismatches(source.context, successor.context))
    if found:
        _fail(found[0].code, found[0].message, details=found)
    payload = reference.payload
    expected = _reference_payload(successor, predecessor, source)
    for name, code, message in (
            ('successor', 'successor_mismatch', 'Referans başka bir ardıl rapor göstergesine ait.'),
            ('predecessor', 'predecessor_mismatch', 'Referans başka bir önceki yayına bağlı; yalnız hemen önceki yayın geçerlidir.'),
            ('binding', 'binding_mismatch', 'Referansın gösterge kimliği, tanımı, hedefi, dönemi veya Program yayını uyuşmuyor.'),
            ('source', 'source_provenance_mismatch', 'Referansın kaynak yayını veya gerçekleşme kaydı uyuşmuyor.'),
            ('content_sha256', 'source_content_mismatch', 'Kaynak gerçekleşme içeriği referans alınan içerikle uyuşmuyor. Referans kullanılamaz.')):
        if payload[name] != expected[name]:
            _fail(code, message, name)


# ---------------------------------------------------------------- resolution

@dataclass(frozen=True)
class MaterializedRealization:
    """New successor content; actual_revision_id is None before persistence."""
    report_indicator_id: int
    content: RealizationContent
    actual_revision_id: int | None = None

    def __post_init__(self):
        _positive_int(self.report_indicator_id, 'report_indicator_id')
        if self.actual_revision_id is not None:
            _positive_int(self.actual_revision_id, 'actual_revision_id')
        if not isinstance(self.content, RealizationContent):
            _fail('invalid_content', 'Yeni gerçekleşme içeriği kanonik biçimde verilmeli.')


@dataclass(frozen=True)
class EffectiveRealization:
    mode: str
    successor_report_indicator_id: int
    content: RealizationContent
    content_sha256: str
    actual_revision_id: int | None
    reference_sha256: str | None = None
    source_report_indicator_id: int | None = None
    source_release_id: int | None = None
    predecessor_release_id: int | None = None

    @property
    def value(self):
        return self.content.decimal_value

    @property
    def state(self):
        return self.content.state

    @property
    def evidence(self):
        return self.content.evidence

    @property
    def explanation(self):
        return self.content.explanation

    @property
    def deviation(self):
        return self.content.deviation


def resolve_effective_realization(successor, *, materialized=None, reference=None, predecessor=None, source=None):
    """Resolve from exactly one explicit input; never looks anything up."""
    if not isinstance(successor, SuccessorTarget):
        _fail('invalid_input', 'Ardıl gösterge ve önceki yayın bağlantısı açıkça verilmeli.')
    if materialized is not None and (reference is not None or predecessor is not None or source is not None):
        _fail('ambiguous_realization', 'Gösterge için hem yeni gerçekleşme hem önceki sürüme referans verilmiş. Yalnız birini seçin.')
    if materialized is None and reference is None:
        if predecessor is not None or source is not None:
            _fail('reference_missing', 'Önceki yayın referanssız kullanılamaz. Değişmeyen değer referansı oluşturun veya yeni kayıt girin.')
        _fail('missing_realization', 'Göstergenin gerçekleşmesi yok. Yeni gerçekleşme girin veya değişmeyen değeri hemen önceki yayına açıkça bağlayın.')
    context = successor.context
    if materialized is not None:
        if not isinstance(materialized, MaterializedRealization):
            _fail('invalid_content', 'Yeni gerçekleşme içeriği kanonik biçimde verilmeli.')
        if materialized.report_indicator_id != context.report_indicator_id:
            _fail('successor_mismatch', 'Yeni gerçekleşme başka bir rapor göstergesine ait.')
        verify_content_for_context(materialized.content, context)
        return EffectiveRealization(MODE_MATERIALIZED, context.report_indicator_id, materialized.content,
                                    materialized.content.sha256, materialized.actual_revision_id)
    verify_reference(reference, successor=successor, predecessor=predecessor, source=source)
    origin = source.flattened_source()
    return EffectiveRealization(MODE_REFERENCE, context.report_indicator_id, source.content, source.content.sha256,
                                origin['actual_revision_id'], reference.reference_sha256,
                                origin['report_indicator_id'], origin['release_id'], predecessor.release.release_id)


def resolve_successor_realizations(successors, *, materialized=None, references=None):
    """Resolve every required successor indicator exactly once.

    successors:   iterable of SuccessorTarget
    materialized: {successor report_indicator_id: MaterializedRealization}
    references:   {successor report_indicator_id: (UnchangedValueReference, predecessor ReleasedIndicator, source ReleasedIndicator)}
    Unknown keys, duplicates, overlaps and gaps fail closed.
    """
    materialized = dict(materialized or {})
    references = dict(references or {})
    targets = list(successors)
    ids = [target.context.report_indicator_id if isinstance(target, SuccessorTarget) else None for target in targets]
    if None in ids or len(ids) != len(set(ids)):
        _fail('invalid_input', 'Ardıl rapor göstergeleri yinelenmiş veya geçersiz.')
    unknown = (set(materialized) | set(references)) - set(ids)
    if unknown:
        _fail('unknown_indicator', 'Raporda bulunmayan bir gösterge için gerçekleşme verilmiş.', details=sorted(unknown, key=str))
    result = {}
    for target in targets:
        key = target.context.report_indicator_id
        triple = references.get(key)
        if triple is not None and (not isinstance(triple, tuple) or len(triple) != 3):
            _fail('incomplete_provenance', 'Referans, hemen önceki yayın ve kaynak gerçekleşme birlikte verilmeli.')
        reference, predecessor, source = triple if triple is not None else (None, None, None)
        result[key] = resolve_effective_realization(target, materialized=materialized.get(key), reference=reference,
                                                    predecessor=predecessor, source=source)
    return result
