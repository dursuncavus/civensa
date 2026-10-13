import io
import re
import unicodedata
from collections import OrderedDict
from docx import Document
from docx.table import Table
from docx.oxml.ns import qn
from .numbers import source_cell


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").replace("|", " ").replace("\xa0", " ")).strip()


def _key(text: str) -> str:
    text=_clean(text).lower().replace("ı","i")
    return "".join(c for c in unicodedata.normalize("NFKD",text) if not unicodedata.combining(c))


def _label_key(text: str) -> str:
    """Compare Turkish labels independently of punctuation and spacing."""
    return _clean(re.sub(r"[^\w\s]", " ", _key(text)))


def _number(text: str):
    cell = source_cell(text)
    if cell['state'] == 'needs_review':
        raise ValueError(cell['issue'])
    return cell['number']


def _source_value(raw, field):
    cell = source_cell(raw, money=field == 'amount')
    return {field: cell['number'], 'raw_text': cell['raw_text'], 'state': cell['state']}


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


def _parse_indicator_table(table):
    rows=table.rows
    header_idx = next((idx for idx, row in enumerate(rows)
                       if _label_key(row.cells[0].text).startswith(
                           ("performans gostergesi", "performans gostergeleri"))
                       and any(_value_kind(cell.text) for cell in row.cells[1:])), None)
    if header_idx is None:
        return None

    def label_value(label):
        return next((_field_value(row) for row in rows[:header_idx]
                     if _label_key(row.cells[0].text).startswith(label)), "")

    budget_year_text = label_value("butce yili")
    budget_years = {int(year) for year in re.findall(r"(?<!\d)20\d{2}(?!\d)", budget_year_text)}
    budget_year = next(iter(budget_years)) if len(budget_years) == 1 else None
    program = label_value("program adi")
    administration = label_value("idare birim adi")
    department = _department_name(administration)
    subprogram = label_value("alt program adi")
    rationale = label_value("gerekce ve aciklamalar")
    goal = label_value("alt programin hedefi")
    headers=[_clean(c.text) for c in rows[header_idx].cells]
    value_columns=[]
    for col,h in enumerate(headers):
        spec=_value_kind(h)
        if spec: value_columns.append((col,*spec))
    indicators=[]
    metadata={"explanation":"","calculation_method":"","data_source":"","responsible":""}
    stop_idx=len(rows)
    for idx in range(header_idx+1,len(rows)):
        first=_clean(rows[idx].cells[0].text)
        lower=_label_key(first)
        if lower.startswith(("gostergeye", "gostergelere")):
            stop_idx=idx; metadata["explanation"]=_field_value(rows[idx],1); break
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
            values.append({"year":year,"kind":kind,**_source_value(cells[col] if col<len(cells) else "", "value")})
        indicators.append({"name":first,"unit":unit,"values":values})
    for row in rows[stop_idx+1:]:
        first=_label_key(row.cells[0].text)
        val=_field_value(row,1)
        if first.startswith("hesaplama yontemi"):
            metadata["calculation_method"]=val
        elif first.startswith("verinin kaynagi"):
            metadata["data_source"]=val
        elif first.startswith("sorumlu idare"):
            metadata["responsible"]=val
    for ind in indicators:
        ind.update(metadata)
    return {"department":department,"budget_year":budget_year,"program":program,"subprogram":subprogram,"rationale":rationale,"goal":goal,"source_title":budget_year_text,"administration":administration,"metadata":metadata,"indicators":indicators}


def _parse_activity_table(table):
    rows=table.rows
    if not rows or _label_key(rows[0].cells[0].text)!="faaliyetler":
        return None
    headers=[_clean(c.text) for c in rows[0].cells]
    value_columns=[]
    for col,h in enumerate(headers):
        spec=_value_kind(h)
        if spec: value_columns.append((col,*spec))
    activities=[]; explanation_start=None; personnel=[]
    i=1
    while i<len(rows):
        cells=[_clean(c.text) for c in rows[i].cells]
        first=cells[0] if cells else ""; lower=_label_key(first)
        if lower.startswith("faaliyetlere iliskin aciklamalar"):
            explanation_start=i+1; break
        if lower.startswith("toplam") or lower.startswith("genel toplam") or lower.startswith("genel butce"):
            i+=1; continue
        if lower.startswith("personel ve sgk"):
            for col,year,kind in value_columns:
                personnel.append({"year":year,"kind":kind,**_source_value(cells[col] if col<len(cells) else "", "amount")})
            i+=1; continue
        if not first or lower in {"butce ici","butce disi"}:
            i+=1; continue
        # A real activity budget row is followed by its Bütçe İçi / Bütçe Dışı detail rows.
        # Do not assume every row comes in triples; otherwise the explanation section can be
        # accidentally consumed as activity data when a total row shifts the index.
        next_inside = i+1 < len(rows) and _label_key(rows[i+1].cells[0].text) == "butce ici"
        next_outside = i+2 < len(rows) and _label_key(rows[i+2].cells[0].text) == "butce disi"
        if not (next_inside and next_outside):
            i += 1
            continue
        total=[]
        for col,year,kind in value_columns:
            total.append({"year":year,"kind":kind,"funding_type":"total",**_source_value(cells[col] if col<len(cells) else "", "amount")})
        inside=[]; outside=[]
        icells=[_clean(c.text) for c in rows[i+1].cells]
        for col,year,kind in value_columns:
            inside.append({"year":year,"kind":kind,"funding_type":"inside",**_source_value(icells[col] if col<len(icells) else "", "amount")})
        ocells=[_clean(c.text) for c in rows[i+2].cells]
        for col,year,kind in value_columns:
            outside.append({"year":year,"kind":kind,"funding_type":"outside",**_source_value(ocells[col] if col<len(ocells) else "", "amount")})
        activities.append({"name":first,"explanation":"","official_name":"","costs":total+inside+outside})
        i+=3
    if explanation_start is not None:
        pairs=[]; j=explanation_start
        while j<len(rows):
            title=_clean(rows[j].cells[0].text)
            if _label_key(title).startswith("faaliyet adi"):
                official=title.split(":",1)[1].strip() if ":" in title else title
                desc=_clean(rows[j+1].cells[0].text) if j+1<len(rows) else ""
                pairs.append((official,desc)); j+=2
            else:
                j+=1
        for idx,(official,desc) in enumerate(pairs):
            if idx<len(activities):
                activities[idx]["official_name"]=official
                activities[idx]["explanation"]=desc
    return {"activities":activities,"personnel":personnel,"columns":[{"column":c,"year":y,"kind":k,"label":headers[c]} for c,y,k in value_columns]}


def parse_performance_docx(data: bytes):
    doc=Document(io.BytesIO(data))
    departments=OrderedDict(); current_department=None; errors=[]; coverage_items=[]
    indicator_table_count=0; activity_table_count=0
    tables = list(iter_document_tables(doc))
    for index,table in enumerate(tables):
        perf=_parse_indicator_table(table)
        if perf and perf["indicators"]:
            indicator_table_count+=1; current_department=perf["department"]
            if perf["budget_year"] is None:
                errors.append(f"Tablo {index+1}: Bütçe Yılı alanında tek bir yıl bulunamadı (alan eksik, boş veya birden fazla farklı yıl içeriyor). Bütçe Yılı alanına tek bir dört haneli yıl yazıp dosyayı yeniden yükleyin.")
            if not current_department:
                errors.append(f"Tablo {index+1}: İdare Birim Adı alanında müdürlük adı bulunamadı. Müdürlük adını yazıp dosyayı yeniden yükleyin."); continue
            dept=departments.setdefault(current_department,{"name":current_department,"blocks":[],"activities":[],"personnel":[]})
            dept["blocks"].append({k:perf[k] for k in ("budget_year","program","subprogram","rationale","goal","source_title","administration","metadata","indicators")})
            continue
        cost=_parse_activity_table(table)
        if cost and cost["columns"] and cost["activities"]:
            activity_table_count+=1
            if not current_department:
                errors.append(f"Tablo {index+1}: faaliyet tablosu bir müdürlükle eşleştirilemedi. Önüne İdare Birim Adı içeren gösterge tablosunu ekleyip dosyayı yeniden yükleyin."); continue
            dept=departments.setdefault(current_department,{"name":current_department,"blocks":[],"activities":[],"personnel":[]})
            dept["activities"].extend(cost["activities"]); dept["personnel"].extend(cost["personnel"])
            continue
        # Empty wrapper tables are visited separately from their nested tables.
        texts = [_clean(cell.text) for row in table.rows for cell in row.cells]
        if any(texts):
            labels = [_label_key(text) for text in texts]
            carries_data = any(
                label.startswith(("butce yili", "program adi", "performans gostergesi",
                                  "performans gostergeleri"))
                or label in {"faaliyetler", "faaliyet maliyeti", "faaliyet maliyetleri"}
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
    indicator_count=sum(len(b["indicators"]) for d in result for b in d["blocks"])
    activity_count=sum(len(d["activities"]) for d in result)
    source_years=sorted({b.get("budget_year") for d in result for b in d["blocks"] if b.get("budget_year")})
    return {
        "departments":result,
        "summary":{"department_count":len(result),"indicator_table_count":indicator_table_count,"indicator_count":indicator_count,"activity_table_count":activity_table_count,"activity_count":activity_count,"table_count":len(tables),"source_years":source_years},
        "warnings":list(errors),
        "errors":errors,
        "coverage_items":coverage_items,
    }
