import csv,http.cookiejar,io,os,urllib.error,urllib.parse,urllib.request
BASE=os.environ["TARGET"].rstrip("/");PASSWORD=os.environ["PILOT_PASSWORD"]
def login(email):
 jar=http.cookiejar.CookieJar();o=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar));data=urllib.parse.urlencode({"email":email,"password":PASSWORD}).encode();r=o.open(urllib.request.Request(BASE+"/login",data=data),timeout=90);assert "/dashboard" in r.geturl();return o
s=login("strateji@civensa.local");html=s.open(BASE+"/audit?action=login&user=strateji",timeout=90).read().decode()
assert "Denetim Geçmişi" in html and "strateji@civensa.local" in html and "login" in html
raw=s.open(BASE+"/api/audit/export.csv?action=login&user=strateji",timeout=90).read().decode("utf-8-sig");rows=list(csv.reader(io.StringIO(raw)))
assert rows[0]==["Tarih","Kullanıcı","İşlem","Varlık","Varlık ID","Ayrıntı"] and len(rows)>=2,rows
d=login("saglik@civensa.local")
for path in ("/audit","/api/audit/export.csv"):
 try:d.open(BASE+path,timeout=90);raise AssertionError("department accessed audit")
 except urllib.error.HTTPError as exc:assert exc.code==403,exc.code
print("AUDIT_VISIBILITY_OK",len(rows)-1)
