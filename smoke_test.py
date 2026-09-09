import http.cookiejar
import json
import os
import urllib.parse
import urllib.request

BASE = os.environ["TARGET"].rstrip("/")
PASSWORD = os.environ["PILOT_PASSWORD"]

health = json.loads(urllib.request.urlopen(BASE + "/health", timeout=30).read().decode())
assert health.get("status") == "ok", health
print("HEALTH_OK", health, flush=True)


def check(email: str, expected: str) -> None:
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    payload = urllib.parse.urlencode({"email": email, "password": PASSWORD}).encode()
    req = urllib.request.Request(BASE + "/login", data=payload, method="POST")
    response = opener.open(req, timeout=30)
    body = response.read().decode("utf-8", "replace")
    final_url = response.geturl()
    assert response.status == 200, (email, response.status, final_url)
    assert "/dashboard" in final_url, (email, final_url)
    assert expected.lower() in body.lower(), (email, expected)
    print("LOGIN_OK", email, final_url, expected, flush=True)


check("strateji@civensa.local", "Strateji")
check("saglik@civensa.local", "Sağlık")
print("ALL_SMOKE_OK", flush=True)
