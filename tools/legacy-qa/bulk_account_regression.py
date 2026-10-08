import csv, http.cookiejar, io, json, os, re, urllib.error, urllib.parse, urllib.request, uuid
BASE=os.environ["TARGET"].rstrip("/"); PASSWORD=os.environ["PILOT_PASSWORD"]; APPLY=os.getenv("APPLY_BULK_USERS")=="1"
jar=http.cookiejar.CookieJar(); opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
data=urllib.parse.urlencode({"email":"strateji@civensa.local","password":PASSWORD}).encode()
response=opener.open(urllib.request.Request(BASE+"/login",data=data),timeout=90)
assert "/dashboard" in response.geturl()
html=opener.open(BASE+"/users",timeout=90).read().decode()
token=re.search(r'<meta name="csrf-token" content="([^"]+)"',html).group(1)
assert "Eksik hesap şablonunu indir" in html
template=opener.open(BASE+"/api/users/missing-departments.csv",timeout=90).read().decode("utf-8-sig")
rows=list(csv.reader(io.StringIO(template))); assert len(rows)>=2
before=len(rows)-1
suffix=uuid.uuid4().hex[:10]
rows[1][2]="QA Toplu Hesap"; rows[1][3]=f"qa-bulk-{suffix}@civensa.local"; rows[1][4]="QA-Strong-2026!"
out=io.StringIO(); csv.writer(out).writerows(rows)
payload=("\ufeff"+out.getvalue()).encode()
def multipart(url, content):
    boundary="----CivensaBoundary"+uuid.uuid4().hex
    body=(f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"accounts.csv\"\r\nContent-Type: text/csv\r\n\r\n").encode()+content+f"\r\n--{boundary}--\r\n".encode()
    req=urllib.request.Request(BASE+url,data=body,method="POST",headers={"Content-Type":f"multipart/form-data; boundary={boundary}","X-CSRF-Token":token})
    return opener.open(req,timeout=120)
preview=json.loads(multipart("/api/users/bulk-preview",payload).read())
assert preview["ok"] and preview["count"]==1,preview
assert "QA-Strong-2026!" not in json.dumps(preview),preview
bad=payload.replace(rows[1][3].encode(),b"invalid-address")
bad_preview=json.loads(multipart("/api/users/bulk-preview",bad).read())
assert not bad_preview["ok"] and bad_preview["errors"],bad_preview
if APPLY:
    applied=json.loads(multipart("/api/users/bulk-import",payload).read())
    assert applied["ok"] and applied["created"]==1 and applied["batch_id"],applied
    after=list(csv.reader(io.StringIO(opener.open(BASE+"/api/users/missing-departments.csv",timeout=90).read().decode("utf-8-sig"))))
    assert len(after)-1==before-1,(before,len(after)-1)
    try:
        multipart("/api/users/bulk-import",payload)
        raise AssertionError("duplicate import unexpectedly succeeded")
    except urllib.error.HTTPError as exc:
        assert exc.code in (409,422),exc.code
    req=urllib.request.Request(BASE+"/api/users/batches/"+applied["batch_id"]+"/revert",data=b"",method="POST",headers={"X-CSRF-Token":token})
    reverted=json.loads(opener.open(req,timeout=120).read()); assert reverted=={"ok":True,"reverted":1},reverted
    restored=list(csv.reader(io.StringIO(opener.open(BASE+"/api/users/missing-departments.csv",timeout=90).read().decode("utf-8-sig"))))
    assert len(restored)-1==before,(before,len(restored)-1)
print("BULK_ACCOUNT_CSV_OK",before,"apply",APPLY)
