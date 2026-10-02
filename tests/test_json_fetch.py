"""Run the actual browser helpers in Node without a browser or new packages."""
import os
from pathlib import Path
import shutil
import subprocess

import pytest

APP_JS = Path(__file__).resolve().parents[1] / "app/static/app.js"
NODE = os.environ.get("CIVENSA_TEST_NODE") or shutil.which("node")

SCENARIOS = {
    "text": """reply(422, 'Tutar negatif olamaz.'); await check('Tutar negatif olamaz.');""",
    "list": """reply(409, {detail:['2027 toplamı farklı.', 'Finansman eksik.']}); await check('2027 toplamı farklı. · Finansman eksik.');""",
    "nested_object": """reply(422, {detail:{message:'CSV uygulanamadı.', errors:['Satır 2 geçersiz.']}}); await check('CSV uygulanamadı. · Satır 2 geçersiz.');""",
    "top_level_errors": """reply(422, {message:'Kontrolleri tamamlayın.',errors:['Kart eksik.']}); const result=await check('Kontrolleri tamamlayın. · Kart eksik.'); assert.deepEqual(result.j.errors,['Kart eksik.']);""",
    "validation_object": """reply(422, {detail:[{loc:['body','amount'],type:'missing',msg:'Field required',input:{secret:'private'}}]}); await check('Girilen bilgiler geçersiz veya eksik. Alanları kontrol edip tekrar deneyin.');""",
    "unknown_object": """reply(422, {internal:'private'}); await check('Girilen bilgileri kontrol edip tekrar deneyin.');""",
    "network": """context.fetch=async()=>{calls++;throw Error('private network detail')}; const result=await run(); assert.equal(result.r.status,0); assert.match(result.j.detail,/Sunucuya ulaşılamadı/); assert.match(result.j.detail,/kayıt durumunu kontrol edin/); assert.equal(calls,1);""",
    "non_json_error": """reply(502, null, {broken:true}); const result=await run(); assert.equal(result.r.ok,false); assert.match(result.j.detail,/Sunucu isteği tamamlayamadı/); assert.doesNotMatch(result.j.detail,/private/);""",
    "non_json_success": """reply(200, null, {broken:true}); const result=await run(); assert.equal(result.r.ok,false); assert.match(result.j.detail,/beklenen yanıt alınamadı/);""",
    "invalid_success_shape": """reply(200, 'unexpected'); assert.equal((await run()).r.ok,false);""",
    "session_expired": """reply(401, {detail:'Unauthorized'}); const result=await run(); assert.equal(result.r.ok,false); assert.match(result.j.detail,/Oturumunuz/); assert.equal(jsonCalls,0);""",
    "login_redirect": """reply(200, null, {redirected:true,url:'https://civensa.invalid/login',broken:true}); const result=await run(); assert.equal(result.r.ok,false); assert.match(result.j.detail,/Yeniden giriş yapın/); assert.equal(jsonCalls,0);""",
    "csrf": """reply(403, {detail:'Güvenlik doğrulaması başarısız. Sayfayı yenileyip tekrar deneyin.'}); await check('Güvenlik doğrulaması başarısız. Sayfayı yenileyip tekrar deneyin.'); assert.equal(sent.options.headers.get('X-CSRF-Token'),'test-token'); assert.equal(sent.options.headers.get('Content-Type'),'application/json'); assert.equal(sent.options.body,'original-input');""",
    "success": """const payload={ok:true,issues:[],updated:2}; reply(200,payload); const result=await run(); assert.equal(result.r.ok,true); assert.equal(result.j,payload);""",
    "toast_safe_text": """vm.runInContext(`toast({detail:['<img src=x onerror=alert(1)>','Alanı kontrol edin.']})`,context); assert.equal(toastElement.textContent,'<img src=x onerror=alert(1)> · Alanı kontrol edin.'); assert.equal(toastElement.innerHTML,undefined);""",
}

HARNESS = r"""
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
let calls=0,jsonCalls=0,sent;
const toastElement={textContent:'',classList:{add(){},remove(){}}};
const context=vm.createContext({
  Headers,URL,
  location:{origin:'https://civensa.invalid'},window:{},
  setTimeout(){},clearTimeout(){},
  document:{
    querySelector(selector){return selector.startsWith('meta')?{content:'test-token'}:null},
    querySelectorAll(){return []},
    getElementById(id){return id==='toast'?toastElement:null},
    addEventListener(){},
  },
});
vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),context);
function reply(status,payload,extra={}){
  context.fetch=async(url,options)=>{
    calls++;sent={url,options};
    return {ok:status>=200&&status<300,status,redirected:false,url:'https://civensa.invalid/api/test',...extra,
      async json(){jsonCalls++;if(extra.broken)throw Error('<html>private server detail</html>');return payload},
    };
  };
}
async function run(){
  const result=await vm.runInContext(`jsonFetch('/api/test',{method:'POST',headers:{'Content-Type':'application/json'},body:'original-input'})`,context);
  if(!result.r.ok){
    assert.equal(typeof result.j.detail,'string');assert.equal(typeof result.j.message,'string');
    assert.doesNotMatch(result.j.detail,/\[object Object\]|private|Unauthorized/);
  }
  return result;
}
async function check(message){const result=await run();assert.equal(result.r.ok,false);assert.equal(result.j.detail,message);assert.equal(result.j.message,message);return result}
(async()=>{SCENARIO})().catch(error=>{console.error(error);process.exitCode=1});
"""


@pytest.mark.skipif(not NODE, reason="Node.js is required for browser helper regression tests")
@pytest.mark.parametrize("scenario", SCENARIOS)
def test_json_fetch(scenario):
    script = HARNESS.replace("SCENARIO", SCENARIOS[scenario])
    result = subprocess.run(
        [NODE, "-e", script, str(APP_JS)], capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0, result.stderr
