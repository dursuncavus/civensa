import http.cookiejar
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ["TARGET"].rstrip("/")
PASSWORD = os.environ["PILOT_PASSWORD"]
ACTION = os.environ.get("PERSISTENCE_ACTION", "check").strip().lower()
MARKER = "__CIVENSA_PERSISTENCE_PROBE__"


def open_with_retry(opener, request, attempts=8, delay=8):
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            return opener.open(request, timeout=30)
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in {502, 503, 504} or attempt == attempts:
                raise
            print("PILOT_WAKE_RETRY", attempt, exc.code, flush=True)
            time.sleep(delay)
        except urllib.error.URLError as exc:
            last_error = exc
            if attempt == attempts:
                raise
            print("PILOT_WAKE_RETRY", attempt, str(exc.reason), flush=True)
            time.sleep(delay)
    raise last_error


def fetch(opener, path: str) -> tuple[str, str, int]:
    response = open_with_retry(opener, BASE + path)
    return response.read().decode("utf-8", "replace"), response.geturl(), response.status


def login(email: str, expected: str):
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    payload = urllib.parse.urlencode({"email": email, "password": PASSWORD}).encode()
    req = urllib.request.Request(BASE + "/login", data=payload, method="POST")
    response = open_with_retry(opener, req)
    body = response.read().decode("utf-8", "replace")
    final_url = response.geturl()
    assert response.status == 200, (email, response.status, final_url)
    assert "/dashboard" in final_url, (email, final_url)
    assert expected.lower() in body.lower(), (email, expected)
    print("LOGIN_OK", email, final_url, expected, flush=True)
    return opener, body


def csrf_from(html: str) -> str:
    match = re.search(r'<meta name="csrf-token" content="([^"]+)"', html)
    assert match, "CSRF token not found"
    return match.group(1)


def health_check():
    response = open_with_retry(urllib.request.build_opener(), BASE + "/health")
    health = json.loads(response.read().decode())
    assert health.get("status") == "ok", health
    assert health.get("version") == "1.8.2", health
    assert health.get("database", {}).get("status") == "ok", health
    assert health.get("database", {}).get("backend") in {"sqlite", "postgresql"}, health
    print("HEALTH_OK", health, flush=True)


def department_context(opener, dashboard_html: str):
    dept_match = re.search(r'href="/department/(\d+)"', dashboard_html)
    assert dept_match, "department link not found"
    department_id = int(dept_match.group(1))
    dept_html, _, status = fetch(opener, f"/department/{department_id}")
    assert status == 200
    csrf = csrf_from(dept_html)
    sp_match = re.search(r'id="subprogramPrototype".*?<option value="(\d+)"', dept_html, re.S)
    assert sp_match, "subprogram option not found"
    return department_id, int(sp_match.group(1)), csrf, dept_html


def marker_ids(html: str) -> list[int]:
    ids = []
    for match in re.finditer(r'<tr data-activity="(\d+)".*?</tr>', html, re.S):
        if MARKER in match.group(0):
            ids.append(int(match.group(1)))
    return ids


def create_probe(opener, dashboard_html: str):
    department_id, subprogram_id, csrf, dept_html = department_context(opener, dashboard_html)
    existing = marker_ids(dept_html)
    if existing:
        print("PERSISTENCE_PROBE_ALREADY_EXISTS", existing, flush=True)
        return
    data = json.dumps({
        "name": MARKER,
        "explanation": "Civensa otomatik kalıcılık testi; kullanıcı verisi değildir.",
        "subprogram_id": subprogram_id,
    }).encode()
    req = urllib.request.Request(
        BASE + "/api/activities",
        data=data,
        method="POST",
        headers={"Content-Type": "application/json", "X-CSRF-Token": csrf},
    )
    response = open_with_retry(opener, req)
    payload = json.loads(response.read().decode())
    assert response.status == 200 and payload.get("ok"), payload
    print("PERSISTENCE_PROBE_CREATED", payload.get("id"), "department", department_id, flush=True)


def verify_probe(opener, dashboard_html: str):
    _, _, _, dept_html = department_context(opener, dashboard_html)
    ids = marker_ids(dept_html)
    assert ids, "persistence probe missing after pilot redeploy"
    print("PERSISTENCE_PROBE_SURVIVED_REDEPLOY", ids, flush=True)


def delete_probe(opener, dashboard_html: str):
    _, _, csrf, dept_html = department_context(opener, dashboard_html)
    ids = marker_ids(dept_html)
    for activity_id in ids:
        req = urllib.request.Request(
            BASE + f"/api/activities/{activity_id}",
            method="DELETE",
            headers={"X-CSRF-Token": csrf},
        )
        response = open_with_retry(opener, req)
        payload = json.loads(response.read().decode())
        assert response.status == 200 and payload.get("ok"), payload
    print("PERSISTENCE_PROBE_DELETED", ids, flush=True)


health_check()
login("strateji@civensa.local", "Strateji")
health_opener, health_dashboard = login("saglik@civensa.local", "Sağlık")

if ACTION == "create":
    create_probe(health_opener, health_dashboard)
elif ACTION == "verify":
    verify_probe(health_opener, health_dashboard)
elif ACTION == "delete":
    delete_probe(health_opener, health_dashboard)
elif ACTION != "check":
    raise RuntimeError(f"Unknown PERSISTENCE_ACTION: {ACTION}")

print("ALL_SMOKE_OK", ACTION, flush=True)
