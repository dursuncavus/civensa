import io
import hashlib
import json
import re
import unicodedata
from collections import OrderedDict
from decimal import Decimal
from .value_labels import value_kind_label, funding_label
from docx import Document
from docx.table import Table
from docx.oxml.ns import qn
from .numbers import source_cell, format_number


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").replace("|", " ").replace("\xa0", " ")).strip()


def _key(text: str) -> str:
    text=_clean(text).lower().replace("ı","i")
    return "".join(c for c in unicodedata.normalize("NFKD",text) if not unicodedata.combining(c))


def _label_key(text: str) -> str:
    """Compare Turkish labels independently of punctuation and all whitespace."""
    return re.sub(r"[^\w]", "", _key(text))


def _number(text: str):
    cell = source_cell(text)
    if cell['state'] == 'needs_review':
        raise ValueError(cell['issue'])
    return cell['number']


def _source_value(raw, field, *, activity_cost=False):
    cell = source_cell(raw, money=field == 'amount')
    if str(raw).strip() in {'-', '–', '—'}:
        cell['state'] = 'not_applicable' if activity_cost else 'needs_review'
    return {field: cell['number'], 'raw_text': cell['raw_text'], 'state': cell['state']}


def _cost_source_value(cells, column, year, kind, budget_year):
    historical = budget_year is not None and year == budget_year - 1
    allow_dash = historical and kind in {'budget', 'midyear_spend', 'year_end_estimate'}
    raw = cells[column] if column < len(cells) else ''
    return _source_value(raw, 'amount', activity_cost=allow_dash)


def _field_value(row, label_cols=2):
    values=[_clean(c.text) for c in row.cells]
    for value in values[label_cols:]:
        if value:
            return value
    return ""


def _department_name(raw: str) -> str:
    raw=_clean(raw)
    if "/" in raw:
        raw=raw.split("/")[-1]
    return raw.strip()


def _value_kind(header: str):
    h=_clean(header).lower()
    match=re.search(r"(20\d{2})", h)
    if not match:
        return None
    year=int(match.group(1))
    if "haziran" in h:
        kind="midyear_spend"
    elif "yıl sonu" in h or "yil sonu" in h:
        kind="year_end_estimate"
    elif "gerçekleşme" in h or "gerceklesme" in h:
        kind="actual"
    elif "planlanan" in h:
        kind="planned"
    elif "hedef" in h:
        kind="target"
    elif "bütçe" in h or "butce" in h:
        kind="budget"
    elif "tahmin" in h:
        kind="forecast"
    else:
        kind="value"
    return year,kind


def iter_document_tables(doc):
    """Visit each table once in document order, including nested tables."""
    for element in doc.element.body.iter():
        if element.tag == qn("w:tbl"):
            yield Table(element, doc)


def _use_accepted_view(doc):
    """Project visible OOXML into the structure python-docx reads.

    Work only on the in-memory import document. Unwrap inserted/moved-to text
    and displayed content controls, including block controls around paragraphs
    or tables; discard deleted/moved-from subtrees altogether.
    """
    hidden = {qn('w:del'), qn('w:moveFrom')}
    wrappers = {qn('w:ins'), qn('w:moveTo'), qn('w:sdt')}
    for element in reversed(list(doc.element.iter())):
        parent = element.getparent()
        if element.tag in hidden:
            parent.remove(element)
        elif element.tag in wrappers:
            content = element.find(qn('w:sdtContent')) if element.tag == qn('w:sdt') else element
            index = parent.index(element)
            for child in list(content) if content is not None else []:
                parent.insert(index, child)
                index += 1
            parent.remove(element)


def _indicator_header_spec(header):
    """Require an explicit, unique year AND kind, never infer from position."""
    years = set(re.findall(r'(?<!\d)20\d{2}(?!\d)', header))
    key = _key(header)
    markers = {'actual': 'gerceklesme', 'target': 'hedef', 'forecast': 'tahmin',
               'planned': 'planlanan', 'budget': 'butce',
               'midyear_spend': 'haziran', 'year_end_estimate': 'yil sonu'}
    kinds = {kind for kind, marker in markers.items() if marker in key}
    # “Değer” qualifies explicit kinds (“Hedef Değeri”); only use the generic
    # kind on its own. Preserve the legacy kind of the “Gerçekleşen” label.
    if not kinds and ('deger' in key or 'gerceklesen' in key):
        kinds.add('value')
    # “Yıl Sonu Gerçekleşme Tahmini” is one Ministry kind, not three kinds.
    if 'year_end_estimate' in kinds:
        kinds.difference_update({'actual', 'forecast'})
    if 'midyear_spend' in kinds:
        kinds.discard('actual')
    if len(years) != 1 or len(kinds) != 1:
        return None
    return int(next(iter(years))), next(iter(kinds))


def _parse_indicator_table(table):
    rows=table.rows
    header_idx = next((idx for idx, row in enumerate(rows)
                       if _label_key(row.cells[0].text).startswith(
                           ("performansgostergesi", "performansgostergeleri"))
                       and any(_label_key(cell.text) == 'olcubirimi' or _value_kind(cell.text)
                               for cell in row.cells[1:])), None)
    if header_idx is None:
        return None

    def label_value(label):
        return next((_field_value(row) for row in rows[:header_idx]
                     if _label_key(row.cells[0].text).startswith(label)), "")

    budget_year_text = label_value("butceyili")
    budget_years = {int(year) for year in re.findall(r"(?<!\d)20\d{2}(?!\d)", budget_year_text)}
    budget_year = next(iter(budget_years)) if len(budget_years) == 1 else None
    program = label_value("programadi")
    administration = label_value("idarebirimadi")
    department = _department_name(administration)
    subprogram = label_value("altprogramadi")
    rationale = label_value("gerekceveaciklamalar")
    goal = label_value("altprograminhedefi")
    headers=[_clean(c.text) for c in rows[header_idx].cells]
    header_cells = rows[header_idx].cells
    data_start = header_idx + 1
    unit_column = max((col for col, text in enumerate(headers)
                       if _label_key(text) == 'olcubirimi'), default=1)
    if data_start < len(rows):
        continuation = [_clean(c.text) for c in rows[data_start].cells]
        # Blank or vertically merged label cells distinguish the second header
        # row from an indicator. Join by grid column, preserving year and kind.
        if all(not text or text == headers[col]
               for col, text in enumerate(continuation[:unit_column + 1])):
            header_cells = rows[data_start].cells
            headers = [' '.join(dict.fromkeys((text, continuation[col]))).strip()
                       if col < len(continuation) else text for col, text in enumerate(headers)]
            data_start += 1
    value_columns=[]
    header_errors=[]
    for col in range(unit_column + 1, len(headers)):
        spec = _indicator_header_spec(headers[col])
        if spec:
            value_columns.append((col, *spec))
        else:
            header_errors.append(col + 1)
    for col, year, kind in value_columns:
        # Word repeats a horizontally merged header cell in the grid. Preserve
        # that established source representation; independent duplicate headers
        # cannot identify distinct values and must be refused.
        if any((other_year, other_kind) == (year, kind)
               and header_cells[other_col]._tc is not header_cells[col]._tc
               for other_col, other_year, other_kind in value_columns):
            header_errors.append(col + 1)
    indicators=[]
    metadata={"explanation":"","calculation_method":"","data_source":"","responsible":""}
    stop_idx=len(rows)
    for idx in range(data_start,len(rows)):
        first=_clean(rows[idx].cells[0].text)
        lower=_label_key(first)
        if lower.startswith(("gostergeye", "gostergelere")):
            stop_idx=idx; metadata["explanation"]=_field_value(rows[idx],1); break
        if lower.startswith(('performansgostergesi', 'performansgostergeleri')) or lower == 'olcubirimi':
            continue
        if lower == 'faaliyetler':
            break
        if not first:
            continue
        cells=[_clean(c.text) for c in rows[idx].cells]
        unit=""
        for candidate in cells[1:3]:
            candidate=_clean(candidate)
            if candidate:
                unit=candidate; break
        values=[]
        for col,year,kind in value_columns:
            values.append({"year":year,"kind":kind,"row_number":idx+1,"column_number":col+1,**_source_value(cells[col] if col<len(cells) else "", "value")})
        indicators.append({"name":first,"unit":unit,"values":values})
    for row in rows[stop_idx+1:]:
        first=_label_key(row.cells[0].text)
        val=_field_value(row,1)
        if first.startswith(("hesaplamayontemi", "hesaplamayonetemi")):
            metadata["calculation_method"]=val
        elif first.startswith("verininkaynagi"):
            metadata["data_source"]=val
        elif first.startswith("sorumluidare"):
            metadata["responsible"]=val
    for ind in indicators:
        ind.update(metadata)
    return {"department":department,"budget_year":budget_year,"program":program,"subprogram":subprogram,"rationale":rationale,"goal":goal,"source_title":budget_year_text,"administration":administration,"metadata":metadata,"indicators":indicators,"header_errors":header_errors}


def _parse_activity_table(table, table_number=None, budget_year=None):
    rows=table.rows
    if not rows or _label_key(rows[0].cells[0].text)!="faaliyetler":
        return None
    headers=[_clean(c.text) for c in rows[0].cells]
    value_columns=[]
    for col,h in enumerate(headers):
        spec=_value_kind(h)
        if spec: value_columns.append((col,*spec))
    activities=[]; explanation_start=None; personnel=[]; assertions=[]
    i=1
    while i<len(rows):
        cells=[_clean(c.text) for c in rows[i].cells]
        first=cells[0] if cells else ""; lower=_label_key(re.sub(r"^\d+[.\s)]*", "", first))
        if lower.startswith("faaliyetlereiliskinaciklamalar"):
            explanation_start=i+1; break
        if lower.startswith("toplam") or lower.startswith("geneltoplam") or lower.startswith("genelbutce"):
            for col,year,kind in value_columns:
                assertions.append({"label":first,"year":year,"kind":kind,
                    "table_number":table_number,"row_number":i+1,"column_number":col+1,
                    **_cost_source_value(cells, col, year, kind, budget_year)})
            i+=1; continue
        if lower.startswith("personelvesgk"):
            for col,year,kind in value_columns:
                personnel.append({"year":year,"kind":kind,"table_number":table_number,"row_number":i+1,"column_number":col+1,**_cost_source_value(cells, col, year, kind, budget_year)})
            i+=1; continue
        if not first or lower in {"butceici","butcedisi"}:
            i+=1; continue
        # A real activity budget row is followed by its Bütçe İçi / Bütçe Dışı detail rows.
        # Do not assume every row comes in triples; otherwise the explanation section can be
        # accidentally consumed as activity data when a total row shifts the index.
        next_inside = i+1 < len(rows) and _label_key(rows[i+1].cells[0].text) == "butceici"
        next_outside = i+2 < len(rows) and _label_key(rows[i+2].cells[0].text) == "butcedisi"
        if not (next_inside and next_outside):
            i += 1
            continue
        total=[]
        for col,year,kind in value_columns:
            total.append({"year":year,"kind":kind,"funding_type":"total","table_number":table_number,"row_number":i+1,"column_number":col+1,**_cost_source_value(cells, col, year, kind, budget_year)})
        inside=[]; outside=[]
        icells=[_clean(c.text) for c in rows[i+1].cells]
        for col,year,kind in value_columns:
            inside.append({"year":year,"kind":kind,"funding_type":"inside","table_number":table_number,"row_number":i+2,"column_number":col+1,**_cost_source_value(icells, col, year, kind, budget_year)})
        ocells=[_clean(c.text) for c in rows[i+2].cells]
        for col,year,kind in value_columns:
            outside.append({"year":year,"kind":kind,"funding_type":"outside","table_number":table_number,"row_number":i+3,"column_number":col+1,**_cost_source_value(ocells, col, year, kind, budget_year)})
        activities.append({"name":first,"explanation":"","official_name":"","costs":total+inside+outside})
        i+=3
    if explanation_start is not None:
        pairs=[]; j=explanation_start
        while j<len(rows):
            title=_clean(rows[j].cells[0].text)
            code = re.match(r'^\s*(\d+)[.\s)]', title)
            body = re.sub(r'^\d+[.\s)]*', '', title)
            labelled = _label_key(body).startswith('faaliyetadi')
            # Some book headings omit “Faaliyet Adı:”. Accept only an exact,
            # coded activity title, never arbitrary prose resembling a heading.
            known_title = code and any(_label_key(body) == _label_key(
                re.sub(r'^\d+[.\s)]*', '', a['name'])) for a in activities)
            if labelled or known_title:
                official=body.split(":",1)[1].strip() if labelled and ":" in body else body
                desc=_clean(rows[j+1].cells[0].text) if j+1<len(rows) else ""
                pairs.append(dict(official=official, description=desc, code=code.group(1) if code else None,
                                  table_number=table_number, title_row=j+1, row_number=j+2)); j+=2
            else:
                j+=1
        for idx, activity in enumerate(activities):
            code = re.match(r'^\s*(\d+)[.\s)]', activity['name'])
            if code:
                candidates = [p for p in pairs if p['code'] == code.group(1)]
                exact = [p for p in candidates if _label_key(p['official']) == _label_key(
                    re.sub(r'^\d+[.\s)]*', '', activity['name']))]
                candidates = exact or candidates
            else:
                candidates = pairs[idx:idx+1]  # Existing uncoded Ministry format.
            if len(candidates) == 1:
                pair = candidates[0]
                activity.update(official_name=pair['official'], explanation=pair['description'],
                                explanation_source={k: pair[k] for k in ('table_number', 'title_row', 'row_number')})
    return {"activities":activities,"personnel":personnel,"total_assertions":assertions,"columns":[{"column":c,"year":y,"kind":k,"label":headers[c]} for c,y,k in value_columns]}


def parse_performance_docx(data: bytes):
    doc=Document(io.BytesIO(data))
    _use_accepted_view(doc)
    departments=OrderedDict(); current_department=None; errors=[]; coverage_items=[]
    indicator_table_count=0; activity_table_count=0; economic_table_count=0
    pending_blocks=[]; rejected_economic_tables=[]
    tables = list(iter_document_tables(doc))
    for index,table in enumerate(tables):
        perf=_parse_indicator_table(table)
        if perf and perf["indicators"]:
            indicator_table_count+=1; current_department=None
            for column in perf['header_errors']:
                errors.append(f"Tablo {index+1}, sütun {column}: gösterge başlık bilgisinde tek bir yıl ve değer türü belirlenemedi. Başlığı yıl ve Gerçekleşme/Hedef/Tahmin gibi tek bir tür içerecek şekilde düzeltip dosyayı yeniden yükleyin.")
            if perf["budget_year"] is None:
                errors.append(f"Tablo {index+1}: Bütçe Yılı alanında tek bir yıl bulunamadı (alan eksik, boş veya birden fazla farklı yıl içeriyor). Bütçe Yılı alanına tek bir dört haneli yıl yazıp dosyayı yeniden yükleyin.")
            required_fields = (
                ("Program Adı", perf["program"]),
                ("İdare/Birim Adı", perf["department"]),
                ("Alt Program Adı", perf["subprogram"]),
            )
            missing_fields = [label for label, value in required_fields if not value]
            for label in missing_fields:
                errors.append(f"Tablo {index+1}: {label} alanı eksik veya boş. {label} alanını doldurup dosyayı yeniden yükleyin.")
            if missing_fields:
                continue
            current_department=perf["department"]
            dept=departments.setdefault(current_department,{"name":current_department,"blocks":[],"activities":[],"personnel":[]})
            pending_blocks.append({"table_number":index+1,"program":perf["program"],"budget_year":perf["budget_year"]})
            dept["blocks"].append({"table_number":index+1, **{k:perf[k] for k in ("budget_year","program","subprogram","rationale","goal","source_title","administration","metadata","indicators")}})
            continue
        # The print book lists membership separately from department-level costs.
        # These amounts must never become duplicate ActivityCostValue sources.
        if table.rows and _label_key(table.rows[0].cells[0].text).startswith('altprogramkapsaminda'):
            if not current_department:
                errors.append(f'Tablo {index+1}: faaliyet üyeliğinin kartı bulunamadı. Önüne ilgili performans kartını ekleyin.')
                continue
            block = departments[current_department]['blocks'][-1]
            members = block.setdefault('activity_memberships', [])
            for row_number, row in enumerate(table.rows[2:], 3):
                title = _clean(row.cells[0].text)
                if title:
                    members.append({'name': title, 'table_number': index+1, 'row_number': row_number})
            continue
        budget_year = departments[current_department]['blocks'][-1]['budget_year'] if current_department else None
        cost=_parse_activity_table(table, table_number=index+1, budget_year=budget_year)
        if cost and cost["columns"] and (cost["activities"] or cost['total_assertions']):
            activity_table_count+=1
            if not current_department:
                errors.append(f"Tablo {index+1}: faaliyet tablosu bir müdürlükle eşleştirilemedi. Önüne İdare Birim Adı içeren gösterge tablosunu ekleyip dosyayı yeniden yükleyin."); continue
            dept=departments.setdefault(current_department,{"name":current_department,"blocks":[],"activities":[],"personnel":[]})
            dept["activities"].extend(cost["activities"]); dept["personnel"].extend(cost["personnel"])
            dept.setdefault('total_assertions', []).extend(cost['total_assertions'])
            continue
        economic = _parse_economic_table(table, index+1, pending_blocks if current_department else [])
        if economic is not None:
            economic_table_count += 1
            if economic.get('error'):
                rejected_economic_tables.append(economic)
                errors.append(economic['error'])
            else:
                departments[current_department].setdefault('economic_assertions', []).extend(
                    economic.pop('source_assertions'))
                departments[current_department].setdefault('economic_tables', []).append(economic)
            pending_blocks=[]
            continue
        # Empty wrapper tables are visited separately from their nested tables.
        texts = [_clean(cell.text) for row in table.rows for cell in row.cells]
        if any(texts):
            labels = [_label_key(text) for text in texts]
            carries_data = any(
                label.startswith(("butceyili", "programadi", "performansgostergesi",
                                  "performansgostergeleri"))
                or label in {"faaliyetler", "faaliyetmaliyeti", "faaliyetmaliyetleri"}
                for label in labels
            )
            if carries_data:
                errors.append(f"Tablo {index+1}: gösterge veya faaliyet tablosu okunamadı. Başlık, yıl/değer sütunları ve veri satırlarını Bakanlık şablonuna uygun düzenleyip dosyayı yeniden yükleyin.")
            else:
                first_cell = texts[0] if texts else ""
                coverage_items.append({"table_number": index+1, "first_cell_text": first_cell,
                    "message": f"Tablo {index+1}: {first_cell} — gösterge/faaliyet verisi içermeyen tablo bilgi amaçlı listelendi; içe aktarmaya dahil edilmedi."})
    if not indicator_table_count:
        errors.append("Dosyada tanınan performans göstergesi tablosu bulunamadı. Bakanlık gösterge şablonunu ve Performans Göstergeleri başlığını kontrol edip dosyayı yeniden yükleyin.")
    result=list(departments.values())
    membership_issues = []
    _attach_activity_memberships(result, membership_issues)
    indicator_count=sum(len(b["indicators"]) for d in result for b in d["blocks"])
    activity_count=sum(len(d["activities"]) for d in result)
    source_years=sorted({b.get("budget_year") for d in result for b in d["blocks"] if b.get("budget_year")})
    _check_economic_personnel(result)
    review_items = _review_items(result)
    economic_count = sum(len(t['values']) for d in result for t in d.get('economic_tables', []))
    # Informational/unclassified tables remain outside the financial importer,
    # but their numeric cells still need visible source comparison evidence.
    unmapped_cells = []
    for item in coverage_items:
        number = item['table_number']
        for row_number, row in enumerate(tables[number-1].rows, 1):
            for column_number, cell in enumerate(row.cells, 1):
                value = source_cell(_clean(cell.text))
                if value['number'] is not None:
                    unmapped_cells.append({'value': value['number'], 'raw_text': value['raw_text'],
                        'state': value['state'], 'label': item['first_cell_text'],
                        'table_number': number, 'row_number': row_number, 'column_number': column_number})
    return {
        "document_sha256": hashlib.sha256(data).hexdigest(),
        "source_assertion_version": 1,
        "unmapped_source_cells": unmapped_cells,
        "departments":result,
        "summary":{"department_count":len(result),"indicator_table_count":indicator_table_count,"indicator_count":indicator_count,"activity_table_count":activity_table_count,"activity_count":activity_count,"table_count":len(tables),"source_years":source_years,"economic_table_count":economic_table_count,"economic_value_count":economic_count,"needs_review_count":len(review_items)},
        "warnings":list(errors) + membership_issues,
        "errors":errors,
        "coverage_items":coverage_items,
        "review_items":review_items,
        "rejected_economic_tables":rejected_economic_tables,
        "source_tables": _source_table_pages(tables),
        "membership_issues": membership_issues,
    }


def _activity_identity(name):
    code = re.match(r'^\s*(\d+)[.\s)]', name)
    return ('code', code.group(1)) if code else ('name', _label_key(name))


def _attach_activity_memberships(departments, issues):
    for department in departments:
        blocks = department['blocks']
        if not any('activity_memberships' in block for block in blocks):
            continue  # Preserve the old Word format's single-subprogramme fallback.
        by_identity = {}
        for activity in department['activities']:
            activity['source_memberships'] = []
            by_identity.setdefault(_activity_identity(activity['name']), []).append(activity)
        for block in blocks:
            for member in block.get('activity_memberships', []):
                matches = by_identity.get(_activity_identity(member['name']), [])
                if len(matches) != 1:
                    issues.append(f"Tablo {member['table_number']}, satır {member['row_number']}: "
                                  f"{department['name']} / {member['name']}: faaliyet maliyet kaydı tekil eşleşmedi. "
                                  'Kart üyeliği ile müdürlük maliyet tablosundaki faaliyet kod/adını kontrol edin.')
                    continue
                matches[0]['source_memberships'].append({**member, 'block_table_number': block['table_number']})


def _source_table_pages(tables):
    sources = {}
    for index, table in enumerate(tables, 1):
        caption = table._tbl.tblPr.find(qn('w:tblCaption'))
        if caption is not None:
            try:
                value = json.loads(caption.get(qn('w:val')))
                if isinstance(value, dict) and value.get('page'):
                    sources[str(index)] = value
            except (ValueError, TypeError):
                pass
    return sources


def _economic_cell(row, column):
    """A merged cell cannot supply several independently asserted year values."""
    cells = row.cells
    offset = row.grid_cols_before
    index = column - offset
    if index < 0 or index >= len(cells):
        return {'amount': None, 'raw_text': '', 'state': 'needs_review', 'issue': 'Kaynak hücre eksik.'}
    cell = cells[index]
    merged = sum(other._tc is cell._tc for other in cells) > 1 or cell._tc.find('.//' + qn('w:vMerge')) is not None
    value = _source_value(_clean(cell.text), 'amount')
    if merged or value['amount'] is None:
        value['amount'] = None
        value['state'] = 'needs_review'
        value['issue'] = 'Birleştirilmiş, boş veya belirsiz kaynak hücre; kaynağa göre doğrulayın.'
    return value


def _parse_economic_table(table, table_number, blocks):
    from .program_service import ECONOMIC_CATEGORIES, economic_columns
    if not table.rows or not any(_label_key(cell.text) == 'ekonomikad'
                                 for cell in table.rows[0].cells[:2]):
        return None
    headers = [_clean(cell.text) for cell in table.rows[0].cells]
    categories = {_label_key(label): key for key, label in ECONOMIC_CATEGORIES.items()}
    # Ministry sources use both singular and plural expense names.
    categories.update({_label_key(label[:-4] + 'i'): key
                       for key, label in ECONOMIC_CATEGORIES.items() if label.endswith('leri')})
    categories['sosyalguvenlikkurumunadevletprimigiderler'] = 'sgk'
    codes = {'01': 'personnel', '02': 'sgk', '03': 'goods_services',
             '04': 'interest', '05': 'current_transfers', '06': 'capital',
             '07': 'capital_transfers', '08': 'lending', '09': 'reserve'}
    columns = {}
    for col, cell in enumerate(table.rows[0].cells):
        spec = _value_kind(cell.text)
        if spec:
            columns[spec] = -1 if spec in columns else col
    year = blocks[-1]['budget_year'] if blocks else None
    # A department left over from a completed card is not source provenance.
    # Reject before making values or placeholders when the card/year is absent.
    if not blocks or year is None or (year, 'budget') not in columns:
        detail = ''
        if blocks:
            detail = (f' Kartın yılına uygun {year} Bütçe sütunu bulunamadı.' if year
                      else ' Önceki kartta Bütçe Yılı belirlenemedi.')
        message = (f'Kart tablosuna bağlı olmayan ekonomik tablo (tablo {table_number}): '
                   + ' | '.join(headers) + '.' + detail
                   + ' Bu tabloyu ilgili müdürlüğün kartından hemen sonra yerleştirin veya kaynaktan çıkarın.')
        return {'table_number': table_number, 'header_row': headers, 'error': message}
    expected = economic_columns(year)
    source_rows = {}; totals = {}; assertions = []
    for row_number, row in enumerate(table.rows[1:], 2):
        label = _label_key(row.cells[0].text)
        category = codes.get(_clean(row.cells[0].text)) or next(
            (categories[_label_key(cell.text)] for cell in row.cells[:2]
             if _label_key(cell.text) in categories), None)
        total = next((key for prefix, key in [('butceicitoplam', 'inside'),
                     ('butcedisitoplam', 'outside'), ('faaliyetmaliyet', 'total')]
                     if label.startswith(prefix)), None)
        if not category and not total:
            continue
        values = [{'year': y, 'kind': k, **_economic_cell(row, columns.get((y, k), -1))}
                  for y, k in expected]
        assertions.extend({**v, 'category': category, 'funding_type': 'inside' if category else total,
                           'label': _clean(row.cells[0].text), 'table_number': table_number,
                           'row_number': row_number,
                           'column_number': columns[(v['year'], v['kind'])] + 1
                               if (v['year'], v['kind']) in columns else None} for v in values)
        if category:
            if category in source_rows:
                for previous, value in zip(source_rows[category], values):
                    value['raw_text'] = previous['raw_text'] + ' / ' + value['raw_text']
                    value.update(amount=None, state='needs_review', issue='Aynı ekonomik gider satırı birden fazla kez bulunuyor.')
            source_rows[category] = values
        else:
            if total in totals:
                for previous, value in zip(totals[total], values):
                    value.update(amount=None, state='needs_review', raw_text=previous['raw_text'] + ' / ' + value['raw_text'])
            totals[total] = values
    # These rows are indispensable even in the Ministry's compact table.
    for category in ('personnel', 'sgk', 'goods_services'):
        source_rows.setdefault(category, [{'year': y, 'kind': k, 'amount': None, 'raw_text': '',
            'state': 'needs_review', 'issue': 'Ekonomik gider satırı kaynakta eksik.'} for y, k in expected])
    groups = {'management' if _label_key(b['program']).startswith('yonetimvedestekprogram') else 'service' for b in blocks}
    group = next(iter(groups)) if len(groups) == 1 else 'unallocated'
    values = []
    for index, (y, k) in enumerate(expected):
        checks = {f: (totals.get(f) or [{}] * len(expected))[index] for f in ('inside', 'outside', 'total')}
        outside_zero = checks['outside'].get('state') == 'verified' and Decimal(checks['outside']['amount']) == 0
        reasons = []
        prefix = f'Tablo {table_number}, {y} {value_kind_label(k)}: '
        def reason(cause, message):
            reasons.append({'cause': cause, 'message': prefix + message + ' Kaynak tabloyu kontrol edin.'})
        def money(amount):
            return format_number(amount, money=True) + ' TL'
        total_labels = {'inside': 'Bütçe İçi Toplam', 'outside': 'Bütçe Dışı Toplam', 'total': 'Faaliyet Maliyeti Toplamı'}
        parts = {category: rows[index] for category, rows in source_rows.items()}
        for label, cell in [*((ECONOMIC_CATEGORIES[c], v) for c, v in parts.items()),
                            *((total_labels[f], v) for f, v in checks.items())]:
            if cell.get('state') != 'verified':
                raw = cell.get('raw_text', '')
                observed = f'«{raw}»' if raw else 'boş/eksik hücre'
                detail = cell.get('issue', 'Kaynak hücre doğrulanamadı.')
                reason('source_cell_unverified', f'{label} için beklenen doğrulanmış bir tutar; gözlenen {observed}. {detail}')
        if checks['outside'].get('state') == 'verified' and not outside_zero:
            reason('outside_funding_unsplit', f"Bütçe Dışı Toplam {money(checks['outside']['amount'])}; "
                   'kategori bazında bütçe içi/dışı dağılım kaynakta ayrılmamış. Kategori tutarlarını ve finansman dağılımını kaynaktan doğrulayın.')
        if checks['inside'].get('state') == 'verified' and all(v['state'] == 'verified' for v in parts.values()):
            observed = Decimal(checks['inside']['amount'])
            expected_total = sum(Decimal(v['amount']) for v in parts.values())
            if observed != expected_total:
                reason('inside_total_mismatch', f'Bütçe İçi Toplam {money(observed)}, kategori satırlarının toplamı {money(expected_total)}; fark {money(observed - expected_total)}.')
        if all(v.get('state') == 'verified' for v in checks.values()):
            observed = Decimal(checks['total']['amount'])
            inside = Decimal(checks['inside']['amount']); outside = Decimal(checks['outside']['amount'])
            if observed != inside + outside:
                reason('funding_total_mismatch', f'Faaliyet Maliyeti Toplamı {money(observed)}, Bütçe İçi Toplam {money(inside)} + '
                       f'Bütçe Dışı Toplam {money(outside)} = {money(inside + outside)}; fark {money(observed - inside - outside)}.')
        if group == 'unallocated':
            programmes = '; '.join(dict.fromkeys(b['program'] for b in blocks)) or 'Program bilgisi eksik'
            reason('program_group_unallocated', f'Program grubu dağılımı kaynakta ayrılmamış. Programlar: {programmes}. Tutarları program gruplarına göre doğrulayın.')
        for category, rows in source_rows.items():
            for fund in ('inside', 'outside'):
                value = dict(rows[index]) if fund == 'inside' else {
                    'year': y, 'kind': k, 'amount': '0' if outside_zero else None,
                    'raw_text': checks['outside'].get('raw_text', ''),
                    'state': 'verified' if outside_zero else 'needs_review'}
                value.update(category=category, funding_type=fund, program_group=group)
                if reasons:
                    value['state'] = 'needs_review'
                    value['review_causes'] = list(reasons)
                    value['issue'] = ' '.join(r['message'] for r in reasons)
                    if not outside_zero:
                        value['amount'] = None  # No category-level financing split is given.
                values.append(value)
    return {'table_number': table_number, 'block_table_numbers': [b['table_number'] for b in blocks],
            'categories': list(source_rows), 'totals': totals, 'values': values, 'source_assertions': assertions}


def _review_items(departments):
    items = []
    for department in departments:
        items.extend(_duplicate_block_reviews(department))
        def add(value, record, table_number=None):
            if value.get('state') != 'needs_review':
                return
            items.append({'department': department['name'], 'record': record, 'table_number': table_number,
                'year': value['year'], 'kind': value['kind'], 'raw_text': value.get('raw_text', ''),
                'message': f"{department['name']} / {record} / {value['year']} {value_kind_label(value['kind'])}: "
                    + value.get('issue', 'Kaynak değeri müdürlükçe kontrol edilmeli.')})
        for block in department['blocks']:
            for indicator in block['indicators']:
                for value in indicator['values']: add(value, indicator['name'], block.get('table_number'))
        for activity in department['activities']:
            for value in activity['costs']: add(value, activity['name'] + ' / ' + funding_label(value['funding_type']))
        for value in department['personnel']: add(value, 'Personel ve SGK')
        for table in department.get('economic_tables', []):
            for value in table['values']:
                from .program_service import ECONOMIC_CATEGORIES
                add(value, ECONOMIC_CATEGORIES[value['category']] + ' / ' + funding_label(value['funding_type']), table['table_number'])
    return items


def _duplicate_block_reviews(department):
    """Flag source repetitions once per repeated group, keeping every block intact."""
    programmes = OrderedDict(); indicators = OrderedDict()
    for block in department['blocks']:
        key = (_key(block['program']), _key(block['subprogram']))
        programmes.setdefault(key, []).append(block)
        for indicator in block['indicators']:
            # Compare parsed numbers: 2467 and 2.467 assert the same value. Unknown
            # text stays distinct, and blank/dash/zero must never compare equal.
            values = tuple(sorted((v['year'], v['kind'], v['state'],
                                   Decimal(v['value']) if v.get('value') is not None else v.get('raw_text', ''))
                                  for v in indicator['values']))
            key = (_key(indicator['name']), values)
            matches = indicators.setdefault(key, [])
            if not any(b is block for b, _ in matches):
                matches.append((block, indicator))
    items = []
    def add(cause, record, blocks, description):
        numbers = [b.get('table_number') for b in blocks]
        tables = ', '.join(str(n) for n in numbers)
        items.append({'department': department['name'], 'record': record, 'table_number': numbers[0],
                      'table_numbers': numbers, 'year': None, 'kind': '', 'raw_text': '',
                      'state': 'needs_review', 'cause': cause,
                      'message': f"{department['name']} / Tablolar {tables}: {description} Kaynak blokları kontrol edin; tekrarların kasıtlı olup olmadığını doğrulayın."})
    for blocks in programmes.values():
        if len(blocks) > 1:
            record = blocks[0]['program'] + ' / ' + blocks[0]['subprogram']
            add('duplicate_programme_block', record, blocks, f'Aynı program ve alt program birden fazla blokta bulunuyor: {record}.')
    for matches in indicators.values():
        if len(matches) > 1:
            record = matches[0][1]['name']
            add('duplicate_indicator', record, [b for b, _ in matches], f'Aynı kod/ad ve aynı değerlere sahip gösterge birden fazla blokta bulunuyor: {record}.')
    return items


def _check_economic_personnel(departments):
    """Keep both source assertions when a shared personnel total disagrees."""
    for department in departments:
        shared = {(v['year'], v['kind']): v for v in department['personnel']}
        for table in department.get('economic_tables', []):
            for key, common in shared.items():
                if common['state'] != 'verified':
                    continue
                values = [v for v in table['values'] if (v['year'], v['kind']) == key and v['category'] in {'personnel', 'sgk'}]
                if values and all(v['amount'] is not None for v in values) and sum(Decimal(v['amount']) for v in values) != Decimal(common['amount']):
                    economic_total = sum(Decimal(v['amount']) for v in values)
                    shared_total = Decimal(common['amount'])
                    message = (f"Tablo {table['table_number']}, {key[0]} {value_kind_label(key[1])}: "
                               f"Personel ve SGK satırları ortak personel tablosundan farklı; ekonomik toplam "
                               f"{format_number(economic_total, money=True)} TL, ortak personel toplamı "
                               f"{format_number(shared_total, money=True)} TL; fark "
                               f"{format_number(economic_total - shared_total, money=True)} TL. İki kaynağı karşılaştırın.")
                    for value in values:
                        value['state'] = 'needs_review'
                        value['review_causes'] = [*value.get('review_causes', []),
                                                  {'cause': 'personnel_total_mismatch', 'message': message}]
                        value['issue'] = ' '.join(r['message'] for r in value['review_causes'])
