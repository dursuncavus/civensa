import http.cookiejar,json,os,re,urllib.error,urllib.parse,urllib.request
BASE=os.environ["TARGET"].rstrip("/");OLD=os.environ["PILOT_PASSWORD"];NEW="QA-Rotated-2026!"
def login(email,password):
 jar=http.cookiejar.CookieJar();o=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar));data=urllib.parse.urlencode({"email":email,"password":password}).encode()
 r=o.open(urllib.request.Request(BASE+"/login",data=data),timeout=90);assert "/dashboard" in r.geturl();return o,r.read().decode()
department_session,_=login("saglik@civensa.local",OLD)
strategy,html=login("strateji@civensa.local",OLD);token=re.search(r'<meta name="csrf-token" content="([^"]+)"',html).group(1)
users=strategy.open(BASE+"/users",timeout=90).read().decode();row=re.search(r'<tr data-user="(\d+)">.*?saglik@civensa.local.*?</tr>',users,re.S);assert row
uid=row.group(1)
def post(path,payload):
 req=urllib.request.Request(BASE+path,data=json.dumps(payload).encode(),method="POST",headers={"Content-Type":"application/json","X-CSRF-Token":token})
 return json.loads(strategy.open(req,timeout=120).read())
assert post(f"/api/users/{uid}/active",{"active":False})["active"] is False
try:department_session.open(BASE+"/dashboard",timeout=90);raise AssertionError("disabled existing session remained active")
except urllib.error.HTTPError as exc:assert exc.code==401,exc.code
try:login("saglik@civensa.local",OLD);raise AssertionError("disabled user logged in")
except urllib.error.HTTPError as exc:assert exc.code==400,exc.code
assert post(f"/api/users/{uid}/active",{"active":True})["active"] is True
assert post(f"/api/users/{uid}/reset-password",{"password":NEW})["ok"]
login("saglik@civensa.local",NEW)
assert post(f"/api/users/{uid}/reset-password",{"password":OLD})["ok"]
login("saglik@civensa.local",OLD)
print("USER_LIFECYCLE_OK",uid)
