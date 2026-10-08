"""QA-only regression for missing indicator values."""
import http.cookiejar
import json
import os
import re
import urllib.parse
import urllib.request

BASE = os.environ["TARGET"].rstrip("/")
PASSWORD = os.environ["PILOT_PASSWORD"]
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
login_data = urllib.parse.urlencode({"email": "saglik@civensa.local", "password": PASSWORD}).encode()
dashboard = opener.open(urllib.request.Request(BASE + "/login", data=login_data, method="POST"), timeout=60).read().decode()
department_id = int(re.search(r'href="/department/(\d+)"', dashboard).group(1))
department_html = opener.open(BASE + f"/department/{department_id}", timeout=60).read().decode()
csrf = re.search(r'<meta name="csrf-token" content="([^"]+)"', department_html).group(1)
indicator_id = int(re.search(r'<article class="record [^"]*" data-id="(\d+)"', department_html).group(1))

def save(value):
    body = json.dumps({"value_2025_planned": value}).encode()
    response = opener.open(urllib.request.Request(
        BASE + f"/api/indicators/{indicator_id}/save",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "X-CSRF-Token": csrf},
    ), timeout=60)
    assert response.status == 200

def indicator_card():
    html = opener.open(BASE + f"/department/{department_id}", timeout=60).read().decode()
    match = re.search(rf'<article class="record [^"]*" data-id="{indicator_id}">.*?</article>', html, re.S)
    assert match
    return match.group(0)

try:
    save("")
    card = indicator_card()
    assert 'data-field="value_2025_planned" value=""' in card
    assert 'data-field="value_2025_planned" value="0"' not in card
    print("CLEARED_INDICATOR_REMOVED_OK", indicator_id)
finally:
    save("12.500")
    assert 'data-field="value_2025_planned" value="12.500"' in indicator_card()
    print("INDICATOR_VALUE_RESTORED_OK", indicator_id)
