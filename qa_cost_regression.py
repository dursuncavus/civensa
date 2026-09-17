"""Destructive QA-only regression for blank activity cost semantics."""
import http.cookiejar
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ["TARGET"].rstrip("/")
PASSWORD = os.environ["PILOT_PASSWORD"]
MARKER = "__CIVENSA_EMPTY_COST_REGRESSION__"

jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
login_data = urllib.parse.urlencode({
    "email": "saglik@civensa.local",
    "password": PASSWORD,
}).encode()
dashboard = opener.open(
    urllib.request.Request(BASE + "/login", data=login_data, method="POST"), timeout=60
).read().decode()
department_id = int(re.search(r'href="/department/(\d+)"', dashboard).group(1))
department_html = opener.open(BASE + f"/department/{department_id}", timeout=60).read().decode()
csrf = re.search(r'<meta name="csrf-token" content="([^"]+)"', department_html).group(1)
subprogram_id = int(
    re.search(r'id="subprogramPrototype".*?<option value="(\d+)"', department_html, re.S).group(1)
)

def call(path, method, payload=None):
    body = json.dumps(payload).encode() if payload is not None else None
    response = opener.open(
        urllib.request.Request(
            BASE + path,
            data=body,
            method=method,
            headers={"Content-Type": "application/json", "X-CSRF-Token": csrf},
        ),
        timeout=60,
    )
    return json.loads(response.read().decode())

def activity_row(activity_id):
    html = opener.open(BASE + f"/department/{department_id}", timeout=60).read().decode()
    match = re.search(rf'<tr data-activity="{activity_id}"[^>]*>.*?</tr>', html, re.S)
    assert match, "activity row missing"
    return match.group(0)

activity_id = None
try:
    activity_id = int(call("/api/activities", "POST", {
        "name": MARKER,
        "explanation": "Automated QA probe; not user data.",
        "subprogram_id": subprogram_id,
    })["id"])
    row = activity_row(activity_id)
    assert 'value="0,00"' not in row and 'value=""' in row
    print("CREATE_EMPTY_MISSING_OK", activity_id)

    call(f"/api/activities/{activity_id}", "PUT", {"cost_2026_budget": "123,45"})
    assert "123,45" in activity_row(activity_id)
    print("NONZERO_COST_OK")

    call(f"/api/activities/{activity_id}", "PUT", {"cost_2026_budget": ""})
    row = activity_row(activity_id)
    assert "123,45" not in row and 'value="0,00"' not in row
    print("CLEARED_COST_REMOVED_OK")

    try:
        call(f"/api/activities/{activity_id}", "PUT", {"cost_2026_budget": "-1"})
        raise AssertionError("negative cost accepted")
    except urllib.error.HTTPError as exc:
        assert exc.code == 422
    print("NEGATIVE_COST_REJECTED_OK")
finally:
    if activity_id:
        call(f"/api/activities/{activity_id}", "DELETE")
        print("QA_ACTIVITY_CLEANED", activity_id)
