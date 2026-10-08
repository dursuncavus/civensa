import csv, html, http.cookiejar, io, json, os, re, urllib.error, urllib.parse, urllib.request, uuid
BASE=os.environ["TARGET"].rstrip("/"); PASSWORD=os.environ["PILOT_PASSWORD"]; APPLY=os.getenv("APPLY_MAPPING_CSV")=="1"; DOCX=os.getenv("IMPORT_DOCX")
jar=http.cookiejar.CookieJar(); opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
login=urllib.parse.urlencode({"email":"strateji@civensa.local","password":PASSWORD}).encode()
response=opener.open(urllib.request.Request(BASE+"/login",data=login),timeout=120); assert "/dashboard" in response.geturl()
page=opener.open(BASE+"/activity-mapping",timeout=120).read().decode(); token=re.search(r'<meta name="csrf-token" content="([^"]+)"',page).group(1)
def multipart(path, content, filename="mapping.csv", content_type="text/csv"):
    boundary="----Civensa"+uuid.uuid4().hex
    body=(f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\nContent-Type: {content_type}\r\n\r\n").encode()+content+f"\r\n--{boundary}--\r\n".encode()
    return opener.open(urllib.request.Request(BASE+path,data=body,method="POST",headers={"Content-Type":f"multipart/form-data; boundary={boundary}","X-CSRF-Token":token}),timeout=180)
def export_rows():
    raw=opener.open(BASE+"/api/activity-mappings/export.csv",timeout=120).read().decode("utf-8-sig")
    return list(csv.reader(io.StringIO(raw)))
rows=export_rows()
if len(rows)==1 and DOCX:
    with open(DOCX,"rb") as source: preview=json.loads(multipart("/api/periods/1/data-import-preview",source.read(),os.path.basename(DOCX),"application/vnd.openxmlformats-officedocument.wordprocessingml.document").read())
    assert preview["can_apply"],preview
    req=urllib.request.Request(BASE+f"/api/import-batches/{preview['batch_id']}/apply",data=b"",method="POST",headers={"X-CSRF-Token":token})
    applied=json.loads(opener.open(req,timeout=240).read()); assert applied["ok"],applied
    rows=export_rows(); page=opener.open(BASE+"/activity-mapping",timeout=120).read().decode()
assert len(rows)>=2,rows
activity_id=rows[1][1]
block=re.search(rf'<article class="mapping-row" data-activity="{activity_id}".*?</article>',page,re.S); assert block,activity_id
options=re.findall(r'<option value="\d+">([^<]+)</option>',block.group(0)); assert options,block.group(0)[:500]
selection=html.unescape(options[0]).strip(); rows[1][6]=selection
out=io.StringIO(); csv.writer(out).writerows(rows); payload=("\ufeff"+out.getvalue()).encode()
preview=json.loads(multipart("/api/activity-mappings/import-preview",payload).read())
assert preview["ok"] and preview["count"]==1,preview
bad_rows=[row[:] for row in rows]; bad_rows[1][6]="INVALID PROGRAM / SUBPROGRAM"
bad_out=io.StringIO(); csv.writer(bad_out).writerows(bad_rows); bad=("\ufeff"+bad_out.getvalue()).encode()
bad_preview=json.loads(multipart("/api/activity-mappings/import-preview",bad).read())
assert not bad_preview["ok"] and bad_preview["errors"],bad_preview
before=len(rows)-1
if APPLY:
    applied=json.loads(multipart("/api/activity-mappings/import-apply",payload).read())
    assert applied["ok"] and applied["updated"]==1 and applied["batch_id"],applied
    after=len(export_rows())-1; assert after==before-1,(before,after)
    try:
        multipart("/api/activity-mappings/import-apply",payload)
        raise AssertionError("stale mapping CSV unexpectedly applied twice")
    except urllib.error.HTTPError as exc:
        assert exc.code==422,exc.code
    req=urllib.request.Request(BASE+"/api/activity-mappings/batches/"+applied["batch_id"]+"/revert",data=b"",method="POST",headers={"X-CSRF-Token":token})
    reverted=json.loads(opener.open(req,timeout=120).read()); assert reverted=={"ok":True,"reverted":1},reverted
    restored=len(export_rows())-1; assert restored==before,(before,restored)
    try:
        opener.open(req,timeout=120)
        raise AssertionError("mapping batch reverted twice")
    except urllib.error.HTTPError as exc:
        assert exc.code==409,exc.code
print("MAPPING_CSV_ROLLBACK_OK",before,"apply",APPLY)
