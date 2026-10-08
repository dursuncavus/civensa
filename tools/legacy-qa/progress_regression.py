"""Regression test for department progress classification and role gates."""
import http.cookiejar
import json
import os
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ["TARGET"].rstrip("/")
PASSWORD = os.environ["PILOT_PASSWORD"]
VALID_STATES = {"not_started", "in_progress", "needs_attention", "ready", "submitted", "returned", "approved"}


def login(email):
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    data = urllib.parse.urlencode({"email": email, "password": PASSWORD}).encode()
    response = opener.open(urllib.request.Request(BASE + "/login", data=data), timeout=30)
    assert "/dashboard" in response.geturl()
    return opener, response.read().decode("utf-8", "replace")


strategy, dashboard = login("strateji@civensa.local")
payload = json.loads(strategy.open(BASE + "/api/progress", timeout=30).read())
assert payload["status"] == "ok", payload
assert payload["version"] == "3.0.0", payload
assert payload["total"] == len(payload["rows"]) >= 1, payload
assert sum(value for key, value in payload["summary"].items() if key != "missing_accounts") == payload["total"], payload
assert payload["summary"]["missing_accounts"] >= 0, payload
assert all(isinstance(row["has_department_user"], bool) for row in payload["rows"]), payload
assert all(row["state"] in VALID_STATES for row in payload["rows"]), payload
assert all(0 <= row["progress_percent"] <= 100 for row in payload["rows"]), payload
assert "Müdürlük İlerleme Panosu" in dashboard, dashboard[:500]
print("PROGRESS_OVERVIEW_OK", payload["summary"], flush=True)

department, _ = login("saglik@civensa.local")
try:
    department.open(BASE + "/api/progress", timeout=30)
    raise AssertionError("department user unexpectedly accessed progress API")
except urllib.error.HTTPError as exc:
    assert exc.code == 403, exc.code
print("PROGRESS_ROLE_GATE_OK", flush=True)
