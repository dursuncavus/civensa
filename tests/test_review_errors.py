"""D2: approval failures remain readable in the relevant review row."""
import subprocess

import pytest
from sqlalchemy import select

from app.models import Submission
from test_json_fetch import APP_JS, HARNESS, NODE

DOM = r"""
function element(tag){return {tag,children:[],hidden:true,textContent:'',
  append(child){this.children.push(child)},
  replaceChildren(...children){this.children=children},
  focus(){this.focused=true},scrollIntoView(){this.scrolled=true},
}}
const boxes={'reviewErrors-1':element('div'),'reviewErrors-2':element('div')};
context.document.createElement=element;
context.document.getElementById=id=>boxes[id]||(id==='toast'?toastElement:null);
const timers=[];context.setTimeout=fn=>timers.push(fn);
context.location.reload=()=>{context.reloaded=true};
const decide=(id='1',decision='approve')=>vm.runInContext(`decide('${id}','${decision}','İade gerekçesi')`,context);
const messages=(id='1')=>boxes['reviewErrors-'+id].children[1].children.map(item=>item.textContent);
"""

SCENARIOS = {
    "separate_persistent_items": """reply(409,{detail:['2027 toplamı uyuşmuyor.','Kart bağlantısı eksik.']});await decide();assert.deepEqual(messages(),['2027 toplamı uyuşmuyor.','Kart bağlantısı eksik.']);assert.equal(boxes['reviewErrors-1'].hidden,false);assert.equal(boxes['reviewErrors-1'].focused,true);assert.equal(timers.length,0);assert.equal(toastElement.textContent,'');assert.equal(boxes['reviewErrors-2'].hidden,true);""",
    "repeat_failure_replaces_list": """reply(409,{detail:['İlk hata.']});await decide();reply(409,{detail:['Kalan hata.']});await decide();assert.deepEqual(messages(),['Kalan hata.']);assert.equal(boxes['reviewErrors-1'].children.length,2);assert.equal(boxes['reviewErrors-1'].hidden,false);""",
    "structured_errors_and_safe_text": """reply(409,{detail:{message:'Kontroller başarısız.',errors:['<img src=x onerror=alert(1)>',{message:'Kaynak değeri doğrulanmalı.'}]}});await decide();assert.deepEqual(messages(),['<img src=x onerror=alert(1)>','Kaynak değeri doğrulanmalı.']);assert.equal(boxes['reviewErrors-1'].children[1].children[0].innerHTML,undefined);""",
    "network_error_is_persistent": """context.fetch=async()=>{throw Error('network')};await decide();assert.match(messages()[0],/Sunucuya ulaşılamadı/);assert.equal(boxes['reviewErrors-1'].hidden,false);assert.equal(timers.length,0);""",
    "session_error_is_persistent": """reply(401,{detail:'Unauthorized'});await decide();assert.match(messages()[0],/Oturumunuz/);assert.equal(boxes['reviewErrors-1'].hidden,false);""",
    "success_clears_only_own_errors": """reply(409,{detail:['Hata.']});await decide();await decide('2');reply(200,{ok:true,status:'approved'});await decide();assert.equal(boxes['reviewErrors-1'].hidden,true);assert.equal(boxes['reviewErrors-1'].children.length,0);assert.equal(boxes['reviewErrors-2'].hidden,false);assert.equal(toastElement.textContent,'Müdürlük paketi onaylandı.');assert.equal(timers.length,2);assert.equal(context.reloaded,undefined);timers.at(-1)();assert.equal(context.reloaded,true);""",
    "return_failure_keeps_approval_errors": """reply(409,{detail:['Mali fark.']});await decide();reply(422,{detail:'İade açıklaması zorunlu.'});await decide('1','return');assert.deepEqual(messages(),['Mali fark.']);assert.equal(boxes['reviewErrors-1'].hidden,false);assert.equal(toastElement.textContent,'İade açıklaması zorunlu.');""",
    "return_success_clears_approval_errors": """reply(409,{detail:['Mali fark.']});await decide();reply(200,{ok:true,status:'returned'});await decide('1','return');assert.equal(boxes['reviewErrors-1'].hidden,true);assert.equal(toastElement.textContent,'Paket müdürlüğe iade edildi.');""",
}


@pytest.mark.skipif(not NODE, reason="Node.js is required for review regression tests")
@pytest.mark.parametrize("scenario", SCENARIOS)
def test_review_errors(scenario):
    script = HARNESS.replace("SCENARIO", DOM + SCENARIOS[scenario])
    result = subprocess.run([NODE, "-e", script, str(APP_JS)], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr


def test_review_template_has_error_region_for_submitted_package(client, db, sample):
    from app.main import app, require_user
    app.dependency_overrides[require_user] = lambda: sample["strategy"]
    submission = db.scalar(select(Submission))
    submission.status = "submitted"
    db.commit()
    response = client.get("/review")
    assert response.status_code == 200
    region = f'id="reviewErrors-{submission.id}" class="return-note" role="alert" tabindex="-1" hidden'
    assert region in response.text
    submission.status = "approved"
    db.commit()
    assert region not in client.get("/review").text
