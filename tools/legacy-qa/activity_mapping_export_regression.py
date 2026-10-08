import csv,http.cookiejar,io,os,urllib.error,urllib.parse,urllib.request
BASE=os.environ["TARGET"].rstrip("/");PASSWORD=os.environ["PILOT_PASSWORD"]
def login(email):
 jar=http.cookiejar.CookieJar();o=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
 r=o.open(urllib.request.Request(BASE+"/login",data=urllib.parse.urlencode({"email":email,"password":PASSWORD}).encode()),timeout=60)
 assert "/dashboard" in r.geturl();return o
s=login("strateji@civensa.local");r=s.open(BASE+"/api/activity-mappings/export.csv",timeout=60)
assert r.headers.get_content_type()=="text/csv";rows=list(csv.reader(io.StringIO(r.read().decode("utf-8-sig"))))
assert rows[0]==["Müdürlük","Faaliyet ID","Faaliyet","Civensa Önerisi","Güven (%)","Öneri Düzeyi","Seçilecek Program / Alt Program"],rows[0]
assert all(len(row)==7 for row in rows)
d=login("saglik@civensa.local")
try:d.open(BASE+"/api/activity-mappings/export.csv",timeout=60);raise AssertionError("department accessed export")
except urllib.error.HTTPError as e:assert e.code==403,e.code
print("MAPPING_EXPORT_OK",len(rows)-1)
