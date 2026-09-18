"""Regression test for the strategy-only operations status endpoint."""
import http.cookiejar
import json
import os
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ["TARGET"].rstrip("/")
PASSWORD = os.environ["PILOT_PASSWORD"]


def login(email):
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    data = urllib.parse.urlencode({"email": email, "password": PASSWORD}).encode()
    response = opener.open(urllib.request.Request(BASE + "/login", data=data), timeout=30)
    assert "/dashboard" in response.geturl()
    return opener


strategy = login("strateji@civensa.local")
payload = json.loads(strategy.open(BASE + "/api/operations/status", timeout=30).read())
assert payload["status"] == "ok", payload
assert payload["version"] == "2.0.1", payload
assert payload["database"]["status"] == "ok", payload
assert payload["records"]["departments"] >= 1, payload
assert payload["records"]["indicators"] >= 1, payload
assert payload["records"]["activities"] >= 1, payload
assert payload["records"]["unresolved_activities"] >= 0, payload
assert isinstance(payload["submissions"], dict), payload
print("OPERATIONS_STATUS_OK", payload, flush=True)

department = login("saglik@civensa.local")
try:
    department.open(BASE + "/api/operations/status", timeout=30)
    raise AssertionError("department user unexpectedly accessed operations status")
except urllib.error.HTTPError as exc:
    assert exc.code == 403, exc.code
print("OPERATIONS_ROLE_GATE_OK", flush=True)
