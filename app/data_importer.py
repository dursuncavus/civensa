import io
import re
import unicodedata
from collections import OrderedDict
from docx import Document


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").replace("|", " ").replace("\xa0", " ")).strip()


def _key(text: str) -> str:
    text=_clean(text).lower().replace("ı","i")
    return "".join(c for c in unicodedata.normalize("NFKD",text) if not unicodedata.combining(c))


def _number(text: str):
    raw=_clean(text).replace("*", "").replace("₺", "").replace("TL", "").strip()
    if not raw or raw in {"-", "–", "—"}:
        return None
    raw=re.sub(r"[^0-9,.-]", "", raw)
    if not raw or raw in {"-", ".", ","}:
        return None
    # Turkish source: 1.234.567,89. Some source cells contain 30.970.987.00.
    if "," in raw:
        raw=raw.replace(".", "").replace(",", ".")
    elif raw.count(".") > 1:
        parts=raw.split(".")
        if len(parts[-1])==2:
            raw="".join(parts[:-1])+"."+parts[-1]
        else:
            raw="".join(parts)
    try:
        return float(raw)
    except ValueError:
        return None


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


def _parse_indicator_table(table):
    rows=table.rows
    if len(rows)<10 or not _key(rows[0].cells[0].text).startswith("butce yili"):
        return None
    budget_year_text=_field_value(rows[0])
    year_match=re.search(r"20\d{2}", budget_year_text)
    budget_year=int(year_match.group(0)) if year_match else None
    program=_field_value(rows[1])
    department=_department_name(_field_value(rows[2]))
    subprogram=_field_value(rows[3])
    rationale=_field_value(rows[4])
    goal=_field_value(rows[6]) if len(rows)>6 else ""
    header_idx=None
    for idx,row in enumerate(rows):
        if _key(row.cells[0].text).startswith("performans gostergesi"):
            header_idx=idx; break
    if header_idx is None:
        return None
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
        lower=_key(first)
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
            values.append({"year":year,"kind":kind,"value":_number(cells[col]) if col<len(cells) else None})
        indicators.append({"name":first,"unit":unit,"values":values})
    for row in rows[stop_idx+1:]:
        first=_key(row.cells[0].text)
        val=_field_value(row,1)
        if first.startswith("hesaplama yontemi"):
            metadata["calculation_method"]=val
        elif first.startswith("verinin kaynagi"):
            metadata["data_source"]=val
        elif first.startswith("sorumlu idare"):
            metadata["responsible"]=val
    for ind in indicators:
        ind.update(metadata)
    return {"department":department,"budget_year":budget_year,"program":program,"subprogram":subprogram,"rationale":rationale,"goal":goal,"indicators":indicators}


def _parse_activity_table(table):
    rows=table.rows
    if not rows or _key(rows[0].cells[0].text)!="faaliyetler":
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
        first=cells[0] if cells else ""; lower=_key(first)
        if lower.startswith("faaliyetlere iliskin aciklamalar"):
            explanation_start=i+1; break
        if lower.startswith("toplam") or lower.startswith("genel toplam") or lower.startswith("genel butce"):
            i+=1; continue
        if lower.startswith("personel ve sgk"):
            for col,year,kind in value_columns:
                personnel.append({"year":year,"kind":kind,"amount":_number(cells[col]) if col<len(cells) else None})
            i+=1; continue
        if not first or lower in {"butce ici","butce disi"}:
            i+=1; continue
        # A real activity budget row is followed by its Bütçe İçi / Bütçe Dışı detail rows.
        # Do not assume every row comes in triples; otherwise the explanation section can be
        # accidentally consumed as activity data when a total row shifts the index.
        next_inside = i+1 < len(rows) and _key(rows[i+1].cells[0].text) == "butce ici"
        next_outside = i+2 < len(rows) and _key(rows[i+2].cells[0].text) == "butce disi"
        if not (next_inside and next_outside):
            i += 1
            continue
        total=[]
        for col,year,kind in value_columns:
            total.append({"year":year,"kind":kind,"funding_type":"total","amount":_number(cells[col]) if col<len(cells) else None})
        inside=[]; outside=[]
        icells=[_clean(c.text) for c in rows[i+1].cells]
        for col,year,kind in value_columns:
            inside.append({"year":year,"kind":kind,"funding_type":"inside","amount":_number(icells[col]) if col<len(icells) else None})
        ocells=[_clean(c.text) for c in rows[i+2].cells]
        for col,year,kind in value_columns:
            outside.append({"year":year,"kind":kind,"funding_type":"outside","amount":_number(ocells[col]) if col<len(ocells) else None})
        activities.append({"name":first,"explanation":"","official_name":"","costs":total+inside+outside})
        i+=3
    if explanation_start is not None:
        pairs=[]; j=explanation_start
        while j<len(rows):
            title=_clean(rows[j].cells[0].text)
            if _key(title).startswith("faaliyet adi"):
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
    departments=OrderedDict(); current_department=None; warnings=[]
    indicator_table_count=0; activity_table_count=0
    for index,table in enumerate(doc.tables):
        perf=_parse_indicator_table(table)
        if perf:
            indicator_table_count+=1; current_department=perf["department"] or current_department
            if not current_department:
                warnings.append(f"Tablo {index+1}: müdürlük adı bulunamadı."); continue
            dept=departments.setdefault(current_department,{"name":current_department,"blocks":[],"activities":[],"personnel":[]})
            dept["blocks"].append({k:perf[k] for k in ("budget_year","program","subprogram","rationale","goal","indicators")})
            continue
        cost=_parse_activity_table(table)
        if cost:
            activity_table_count+=1
            if not current_department:
                warnings.append(f"Tablo {index+1}: faaliyet tablosu bir müdürlükle eşleştirilemedi."); continue
            dept=departments.setdefault(current_department,{"name":current_department,"blocks":[],"activities":[],"personnel":[]})
            dept["activities"].extend(cost["activities"]); dept["personnel"].extend(cost["personnel"])
    result=list(departments.values())
    indicator_count=sum(len(b["indicators"]) for d in result for b in d["blocks"])
    activity_count=sum(len(d["activities"]) for d in result)
    source_years=sorted({b.get("budget_year") for d in result for b in d["blocks"] if b.get("budget_year")})
    return {
        "departments":result,
        "summary":{"department_count":len(result),"indicator_table_count":indicator_table_count,"indicator_count":indicator_count,"activity_table_count":activity_table_count,"activity_count":activity_count,"table_count":len(doc.tables),"source_years":source_years},
        "warnings":warnings,
    }
