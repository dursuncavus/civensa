import http.cookiejar,json,os,urllib.error,urllib.parse,urllib.request
BASE=os.environ["TARGET"].rstrip("/");PASSWORD=os.environ["PILOT_PASSWORD"]
def login(email):
 jar=http.cookiejar.CookieJar();o=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar));data=urllib.parse.urlencode({"email":email,"password":PASSWORD}).encode();r=o.open(urllib.request.Request(BASE+"/login",data=data),timeout=90);assert "/dashboard" in r.geturl();return o
s=login("strateji@civensa.local");p=json.loads(s.open(BASE+"/api/release/readiness",timeout=90).read())
assert p["status"]=="ready",p
assert p["migration"]=="8c4f72a10b31",p
assert all(p["checks"].values()),p
assert isinstance(p["warnings"],list),p
html=s.open(BASE+"/operations",timeout=90).read().decode();assert "Yayın Uygunluk Kapısı" in html and "READY" in html
d=login("saglik@civensa.local")
try:d.open(BASE+"/api/release/readiness",timeout=90);raise AssertionError("department accessed readiness")
except urllib.error.HTTPError as exc:assert exc.code==403,exc.code
print("RELEASE_READINESS_OK",p["warnings"])
