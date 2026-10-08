"""Phase 5B1 Activity Report unchanged-value reference / resolution engine.

Pure, side-effect-free helpers. This module performs no database, ORM, HTTP,
clock or filesystem access and never searches for a value: every input is
passed in explicitly by the caller. A successor ReportIndicator's effective
realization is EXACTLY ONE of:

  A) newly materialized content (a new ActualRevision written by the caller), or
  B) an explicit immutable reference to one historical source ActualRevision.

There is no "latest ActualRevision" lookup, no global fallback, no name/code
identity matching and no automatic rebase. Anything incomplete, ambiguous or
inconsistent fails closed with ActivityReferenceError. See
docs/phase5b1-activity-reference-contract.md.
"""
import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

CONTENT_SCHEMA = 'civensa.activity-realization-content/v1'
TARGET_SCHEMA = 'civensa.activity-target-semantics/v1'
REFERENCE_SCHEMA = 'civensa.activity-unchanged-value-reference/v1'
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

# Same accepted text form as activity_contract_service.parse_actual.
_DECIMAL_TEXT = re.compile(r'[+-]?\d+(?:\.\d{1,6})?')
_SHA256 = re.compile(r'[0-9a-f]{64}')
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
    try:
        if not number.is_finite() or abs(number) >= limit or number != number.quantize(_QUANTUM):
            raise InvalidOperation()
    except InvalidOperation:
        _fail('invalid_decimal', 'Sonlu bir sayı ve en fazla 6 ondalık basamak girin.', field)
    if number == 0:
        return '0'
    return format(number.normalize(), 'f')


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
    ReportIndicator, PublicationIndicatorBinding, IndicatorDefinitionRevision, IndicatorIdentity.
    """
    organization_id: int
    activity_report_id: int
    report_revision_id: int
    report_revision_number: int
    report_indicator_id: int
    persistent_indicator_id: str
    definition_revision_id: int
    definition_sha256: str
    definition_json: str
    publication_id: int
    publication_sha256: str
    contract_version: str

    def __post_init__(self):
        for name in ('organization_id', 'activity_report_id', 'report_revision_id', 'report_revision_number',
                     'report_indicator_id', 'definition_revision_id', 'publication_id'):
            _positive_int(getattr(self, name), name)
        _identity(self.persistent_indicator_id, 'persistent_indicator_id')
        _sha(self.definition_sha256, 'definition_sha256')
        _sha(self.publication_sha256, 'publication_sha256')
        if self.contract_version not in CONTRACT_VERSIONS:
            _fail('unsupported_contract', 'Yayın veri sözleşmesinin sürümü desteklenmiyor.', 'contract_version')
        if not isinstance(self.definition_json, str) or sha256_hex(self.definition_json) != self.definition_sha256:
            _fail('definition_integrity', 'Gösterge tanımının bütünlüğü doğrulanamadı. Strateji birimine başvurun.', 'definition_sha256')
        definition = _loads(self.definition_json, 'definition_json')
        if not isinstance(definition, dict) or not isinstance(definition.get('targets'), list):
            _fail('definition_integrity', 'Gösterge tanımının hedef yapısı doğrulanamadı.', 'definition_json')
        # v1 definitions carry no marker; v2/v3 must carry their own contract version.
        marker = definition.get('definition_contract_version')
        if (self.contract_version == '1.0' and marker is not None) or (self.contract_version != '1.0' and marker != self.contract_version):
            _fail('definition_integrity', 'Gösterge tanımı yayın veri sözleşmesiyle uyuşmuyor.', 'definition_json')
        _target_semantics(definition['targets'])

    @property
    def targets(self):
        return json.loads(self.definition_json)['targets']

    @property
    def effective_target(self):
        """difference-v1 target exactly as activity_contract_service.save_actual derives it."""
        effective = _target_semantics(self.targets)['effective_target']
        return None if effective is None else Decimal(effective)

    @property
    def target_semantics_sha256(self):
        return sha256_hex(canonical_json(_target_semantics(self.targets)))

    def binding(self):
        return {'organization_id': self.organization_id, 'persistent_indicator_id': self.persistent_indicator_id,
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
    expected = content.decimal_value - target if content.state == 'verified' and target is not None else None
    delta = deviation['delta']
    if (expected is None) != (delta is None) or (expected is not None and Decimal(delta) != expected):
        _fail('deviation_mismatch', 'Hedef farkı sabit tanıma göre uyuşmuyor. Gerçekleşmeyi yeni kayıtla girip farkı yeniden hesaplatın.', 'deviation')


# ---------------------------------------------------------------- source realization

@dataclass(frozen=True)
class SourceProvenance:
    """Immutable release-side provenance of one historical source ActualRevision."""
    release_id: int
    release_major: int
    release_minor: int
    candidate_id: int
    candidate_sha256: str
    activity_approval_id: int
    actual_revision_id: int

    def __post_init__(self):
        for name in ('release_id', 'candidate_id', 'activity_approval_id', 'actual_revision_id'):
            _positive_int(getattr(self, name), name)
        if type(self.release_major) is not int or self.release_major < 1:
            _fail('incomplete_provenance', 'Kaynak rapor sürümü geçersiz.', 'release_major')
        if type(self.release_minor) is not int or self.release_minor < 0:
            _fail('incomplete_provenance', 'Kaynak rapor sürümü geçersiz.', 'release_minor')
        _sha(self.candidate_sha256, 'candidate_sha256')


@dataclass(frozen=True)
class SourceRealization:
    """One explicit historical realization: its context, provenance and exact content."""
    context: IndicatorContext
    provenance: SourceProvenance
    content: RealizationContent

    def __post_init__(self):
        if (not isinstance(self.context, IndicatorContext) or not isinstance(self.provenance, SourceProvenance)
                or not isinstance(self.content, RealizationContent)):
            _fail('incomplete_provenance', 'Referans kaynağı eksik. Kaynak gösterge, sürüm ve içerik açıkça verilmeli.')
        verify_content_for_context(self.content, self.context)

    def section(self):
        return {'activity_report_id': self.context.activity_report_id,
                'report_revision_id': self.context.report_revision_id,
                'report_revision_number': self.context.report_revision_number,
                'report_indicator_id': self.context.report_indicator_id,
                'actual_revision_id': self.provenance.actual_revision_id,
                'release_id': self.provenance.release_id, 'release_major': self.provenance.release_major,
                'release_minor': self.provenance.release_minor, 'candidate_id': self.provenance.candidate_id,
                'candidate_sha256': self.provenance.candidate_sha256,
                'activity_approval_id': self.provenance.activity_approval_id}


def verify_source_against_candidate_entry(source, entry):
    """Check that the source is exactly what the released candidate materialized for this indicator."""
    if not isinstance(source, SourceRealization) or not isinstance(entry, dict):
        _fail('incomplete_provenance', 'Referans kaynağı ve yayımlanan aday kaydı açıkça verilmeli.')
    if (entry.get('materialized_report_indicator_id') != source.context.report_indicator_id
            or entry.get('materialized_actual_revision_id') != source.provenance.actual_revision_id
            or entry.get('definition_revision_id') != source.context.definition_revision_id):
        _fail('source_provenance_mismatch', 'Kaynak gerçekleşme yayımlanan rapor sürümündeki kayıtla uyuşmuyor. Değişmeyen değer referansı kullanılamaz.')
    if content_from_entry(entry).sha256 != source.content.sha256:
        _fail('source_content_mismatch', 'Kaynak gerçekleşme içeriği yayımlanan rapor sürümüyle uyuşmuyor. Değişmeyen değer referansı kullanılamaz.')


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
    ('organization_id', 'organization_mismatch', 'Kaynak gösterge başka bir kuruma ait.'),
    ('activity_report_id', 'report_mismatch', 'Kaynak gösterge başka bir Faaliyet Raporuna ait.'),
    ('persistent_indicator_id', 'identity_mismatch', 'Kalıcı gösterge kimliği kaynakla aynı değil.'),
    ('definition_revision_id', 'definition_revision_mismatch', 'Gösterge tanım sürümü değişmiş.'),
    ('definition_sha256', 'definition_hash_mismatch', 'Gösterge tanımının içeriği değişmiş.'),
    ('target_semantics_sha256', 'target_mismatch', 'Göstergenin hedefi değişmiş.'),
    ('publication_id', 'program_base_mismatch', 'Rapor farklı bir Performans Programı yayınına bağlı.'),
    ('publication_sha256', 'program_base_mismatch', 'Performans Programı yayınının içeriği farklı.'),
    ('contract_version', 'program_base_mismatch', 'Yayın veri sözleşmesi sürümü farklı.'),
)
_CONTENT_CHECKS = (
    ('value', 'value_changed', 'Gerçekleşme değeri kaynaktan farklı.'),
    ('state', 'state_changed', 'Veri durumu kaynaktan farklı.'),
    ('evidence_json', 'evidence_changed', 'Kanıt kayıtları veya sıraları kaynaktan farklı.'),
    ('explanation', 'explanation_changed', 'Açıklama kaynaktan farklı.'),
    ('deviation_json', 'deviation_changed', 'Sapma kaydı kaynaktan farklı.'),
)


def _context_mismatches(source, successor):
    found = []
    for name, code, message in _CONTEXT_CHECKS:
        if getattr(source.context, name) != getattr(successor, name):
            found.append(Mismatch(code, message + _NEW_RECORD))
    if (successor.report_revision_number <= source.context.report_revision_number
            or successor.report_revision_id == source.context.report_revision_id
            or successor.report_indicator_id == source.context.report_indicator_id):
        found.append(Mismatch('not_a_successor', 'Referans yalnız daha yeni bir rapor revizyonundaki göstergeden önceki sürüme verilebilir.'))
    return found


def check_reference_eligibility(source, successor, proposed):
    """Decide whether `proposed` successor content may be represented by a reference to `source`.

    Every mismatch is reported, not only the first. Equality is exact on canonical
    content: Decimal value equality, blank != zero, evidence order significant.
    """
    if not isinstance(source, SourceRealization) or not isinstance(successor, IndicatorContext) \
            or not isinstance(proposed, RealizationContent):
        _fail('invalid_input', 'Kaynak gerçekleşme, ardıl gösterge bağlamı ve önerilen içerik açıkça verilmeli.')
    found = _context_mismatches(source, successor)
    for name, code, message in _CONTENT_CHECKS:
        if getattr(source.content, name) != getattr(proposed, name):
            found.append(Mismatch(code, message + _NEW_RECORD))
    try:
        verify_content_for_context(proposed, successor)
    except ActivityReferenceError as exc:
        found.append(Mismatch(exc.code, exc.message))
    return Eligibility(not found, tuple(found))


def require_reference_eligibility(source, successor, proposed):
    result = check_reference_eligibility(source, successor, proposed)
    if not result.eligible:
        first = result.mismatches[0]
        _fail(first.code, first.message, details=result.mismatches)
    return result


# ---------------------------------------------------------------- reference provenance

_SUCCESSOR_KEYS = frozenset({'organization_id', 'activity_report_id', 'report_revision_id', 'report_revision_number',
                             'report_indicator_id'})
_SOURCE_KEYS = frozenset({'activity_report_id', 'report_revision_id', 'report_revision_number', 'report_indicator_id',
                          'actual_revision_id', 'release_id', 'release_major', 'release_minor', 'candidate_id',
                          'candidate_sha256', 'activity_approval_id'})
_BINDING_KEYS = frozenset({'organization_id', 'persistent_indicator_id', 'definition_revision_id', 'definition_sha256',
                           'target_semantics_sha256', 'publication_id', 'publication_sha256', 'contract_version'})
_TOP_KEYS = frozenset({'schema', 'calculation_rule_version', 'successor', 'source', 'binding', 'content_sha256'})


def _successor_section(successor):
    return {'organization_id': successor.organization_id, 'activity_report_id': successor.activity_report_id,
            'report_revision_id': successor.report_revision_id,
            'report_revision_number': successor.report_revision_number,
            'report_indicator_id': successor.report_indicator_id}


def _reference_payload(source, successor):
    return {'schema': REFERENCE_SCHEMA, 'calculation_rule_version': CALCULATION_RULE,
            'successor': _successor_section(successor), 'source': source.section(),
            'binding': successor.binding(), 'content_sha256': source.content.sha256}


def _check_structure(payload):
    if not isinstance(payload, dict) or set(payload) != _TOP_KEYS:
        _fail('incomplete_provenance', 'Değişmeyen değer referansı eksik veya fazla alan içeriyor.')
    if payload['schema'] != REFERENCE_SCHEMA or payload['calculation_rule_version'] != CALCULATION_RULE:
        _fail('unsupported_reference', 'Değişmeyen değer referansının sürümü desteklenmiyor.')
    for name, keys in (('successor', _SUCCESSOR_KEYS), ('source', _SOURCE_KEYS), ('binding', _BINDING_KEYS)):
        if not isinstance(payload[name], dict) or set(payload[name]) != keys:
            _fail('incomplete_provenance', 'Değişmeyen değer referansının kaynak bilgisi eksik.', name)
    for name in ('successor', 'source', 'binding'):
        for key, value in payload[name].items():
            if key.endswith('_sha256'):
                _sha(value, f'{name}.{key}')
            elif key == 'persistent_indicator_id':
                _identity(value, f'{name}.{key}')
            elif key == 'contract_version':
                if value not in CONTRACT_VERSIONS:
                    _fail('incomplete_provenance', 'Referansın veri sözleşmesi sürümü geçersiz.', f'{name}.{key}')
            elif key == 'release_minor':
                if type(value) is not int or value < 0:
                    _fail('incomplete_provenance', 'Referansın kaynak rapor sürümü geçersiz.', f'{name}.{key}')
            else:
                _positive_int(value, f'{name}.{key}')
    _sha(payload['content_sha256'], 'content_sha256')


@dataclass(frozen=True)
class UnchangedValueReference:
    """Immutable reference: canonical provenance JSON plus its SHA-256.

    Suitable for a later append-only RevisionValueReference row storing exactly
    these two columns (plus indexed copies of the IDs, which must equal the JSON).
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


def build_reference(source, successor, proposed):
    """Construct a reference only for exactly unchanged, fully bound content."""
    require_reference_eligibility(source, successor, proposed)
    text = canonical_json(_reference_payload(source, successor))
    return UnchangedValueReference(text, sha256_hex(text))


def verify_reference(reference, *, source, successor):
    """Fail closed unless the reference binds exactly this source and this successor."""
    if not isinstance(reference, UnchangedValueReference):
        _fail('incomplete_provenance', 'Değişmeyen değer referansı açıkça verilmeli.')
    if not isinstance(source, SourceRealization):
        _fail('reference_source_missing', 'Referansın kaynak gerçekleşmesi açıkça verilmeli; sistem başka bir değer aramaz.')
    if not isinstance(successor, IndicatorContext):
        _fail('invalid_input', 'Ardıl gösterge bağlamı açıkça verilmeli.')
    # Re-check hash/structure even if the instance was altered after construction.
    UnchangedValueReference(reference.provenance_json, reference.reference_sha256)
    found = _context_mismatches(source, successor)
    if found:
        _fail(found[0].code, found[0].message, details=found)
    payload = reference.payload
    expected = _reference_payload(source, successor)
    if payload['successor'] != expected['successor']:
        _fail('successor_mismatch', 'Referans başka bir ardıl rapor göstergesine ait.', 'successor')
    if payload['binding'] != expected['binding']:
        _fail('binding_mismatch', 'Referansın gösterge kimliği, tanımı, hedefi veya Program yayını uyuşmuyor.', 'binding')
    if payload['source'] != expected['source']:
        _fail('source_provenance_mismatch', 'Referansın kaynak rapor sürümü veya gerçekleşme kaydı uyuşmuyor.', 'source')
    if payload['content_sha256'] != expected['content_sha256']:
        _fail('source_content_mismatch', 'Kaynak gerçekleşme içeriği referans alınan içerikle uyuşmuyor. Referans kullanılamaz.', 'content_sha256')


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


def resolve_effective_realization(successor, *, materialized=None, reference=None, source=None):
    """Resolve from exactly one explicit input; never looks anything up."""
    if not isinstance(successor, IndicatorContext):
        _fail('invalid_input', 'Ardıl gösterge bağlamı açıkça verilmeli.')
    if materialized is not None and (reference is not None or source is not None):
        _fail('ambiguous_realization', 'Gösterge için hem yeni gerçekleşme hem önceki sürüme referans verilmiş. Yalnız birini seçin.')
    if materialized is None and reference is None:
        if source is not None:
            _fail('reference_missing', 'Kaynak gerçekleşme referanssız kullanılamaz. Değişmeyen değer referansı oluşturun veya yeni kayıt girin.')
        _fail('missing_realization', 'Göstergenin gerçekleşmesi yok. Yeni gerçekleşme girin veya değişmeyen değeri önceki sürüme açıkça bağlayın.')
    if materialized is not None:
        if not isinstance(materialized, MaterializedRealization):
            _fail('invalid_content', 'Yeni gerçekleşme içeriği kanonik biçimde verilmeli.')
        if materialized.report_indicator_id != successor.report_indicator_id:
            _fail('successor_mismatch', 'Yeni gerçekleşme başka bir rapor göstergesine ait.')
        verify_content_for_context(materialized.content, successor)
        return EffectiveRealization(MODE_MATERIALIZED, successor.report_indicator_id, materialized.content,
                                    materialized.content.sha256, materialized.actual_revision_id)
    verify_reference(reference, source=source, successor=successor)
    return EffectiveRealization(MODE_REFERENCE, successor.report_indicator_id, source.content, source.content.sha256,
                                source.provenance.actual_revision_id, reference.reference_sha256,
                                source.context.report_indicator_id, source.provenance.release_id)


def resolve_successor_realizations(successors, *, materialized=None, references=None):
    """Resolve every required successor indicator exactly once.

    materialized: {successor report_indicator_id: MaterializedRealization}
    references:   {successor report_indicator_id: (UnchangedValueReference, SourceRealization)}
    Unknown keys, duplicates, overlaps and gaps fail closed.
    """
    materialized = dict(materialized or {})
    references = dict(references or {})
    contexts = list(successors)
    ids = [context.report_indicator_id if isinstance(context, IndicatorContext) else None for context in contexts]
    if None in ids or len(ids) != len(set(ids)):
        _fail('invalid_input', 'Ardıl rapor göstergeleri yinelenmiş veya geçersiz.')
    unknown = (set(materialized) | set(references)) - set(ids)
    if unknown:
        _fail('unknown_indicator', 'Raporda bulunmayan bir gösterge için gerçekleşme verilmiş.', details=sorted(unknown, key=str))
    result = {}
    for context in contexts:
        pair = references.get(context.report_indicator_id)
        if pair is not None and (not isinstance(pair, tuple) or len(pair) != 2):
            _fail('incomplete_provenance', 'Referans ve kaynak gerçekleşme birlikte verilmeli.')
        reference, source = pair if pair is not None else (None, None)
        result[context.report_indicator_id] = resolve_effective_realization(
            context, materialized=materialized.get(context.report_indicator_id), reference=reference, source=source)
    return result
