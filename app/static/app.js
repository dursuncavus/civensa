// Pin an automatically selected PP period in this tab before any reload or write.
const displayedPpPeriod=document.querySelector('meta[name="pp-period-id"]')?.content;
if(displayedPpPeriod){
  const current=new URL(location.href);
  if(!current.searchParams.has('period_id')){
    current.searchParams.set('period_id',displayedPpPeriod);
    history.replaceState(history.state,'',current.pathname+current.search+current.hash);
  }
}
const toast=(msg)=>{const el=document.getElementById('toast');if(!el)return;el.textContent=errorMessage(msg);el.classList.add('show');clearTimeout(window.__toastTimer);window.__toastTimer=setTimeout(()=>el.classList.remove('show'),2800)};
const trNumber=(raw,money=false)=>String(raw??'').trim();
const requestFailure='İşlem sonucu doğrulanamadı. Yeniden denemeden önce kayıt durumunu kontrol edin.';
const errorMessage=(value)=>{
  if(typeof value==='string')return value.trim();
  if(Array.isArray(value))return [...new Set(value.map(errorMessage).filter(Boolean))].join(' · ');
  if(!value||typeof value!=='object')return '';
  if(Array.isArray(value.loc)&&value.type){
    return 'Girilen bilgiler geçersiz veya eksik. Alanları kontrol edip tekrar deneyin.';
  }
  return errorMessage([value.message,value.detail,value.errors,value.error]);
};
const jsonFetch=async(url,options={})=>{
  const failure=(r,message)=>({r:{ok:false,status:r?.status||0},j:{detail:message,message}});
  const token=document.querySelector('meta[name="csrf-token"]')?.content;
  if(token){const headers=new Headers(options.headers||{});headers.set('X-CSRF-Token',token);options={...options,headers}}
  const periodId=document.querySelector('meta[name="pp-period-id"]')?.content;
  // PP APIs always receive the year shown in this tab, including on first load.
  if(periodId&&/^\/api\/(indicators|activities|departments|submissions|activity-mappings|progress|operations|release)(\/|$)/.test(url)){
    const target=new URL(url,location.origin);
    if(!target.searchParams.has('period_id'))target.searchParams.set('period_id',periodId);
    url=target.pathname+target.search;
  }
  let r;
  try{r=await fetch(url,options)}catch{return failure(null,'Sunucuya ulaşılamadı. İnternet bağlantınızı kontrol edin. '+requestFailure)}
  if(r.redirected&&new URL(r.url,location.origin).pathname==='/change-password'){
    location.href='/change-password';
    return failure(r,'Devam etmek için kendi parolanızı belirleyin.');
  }
  if(r.status===401||(r.redirected&&new URL(r.url,location.origin).pathname==='/login')){
    return failure(r,'Oturumunuz sona ermiş veya giriş yapmanız gerekiyor. Yeniden giriş yapın; ardından kayıt durumunu kontrol edin.');
  }
  if(r.status>=500)return failure(r,'Sunucu isteği tamamlayamadı. '+requestFailure);
  let j;
  try{j=await r.json()}catch{return failure(r,'Sunucudan beklenen yanıt alınamadı. '+requestFailure)}
  if(!r.ok){
    const defaults={403:'Bu işlem için yetkiniz yok. Erişiminizi kontrol edin.',404:'İstenen kayıt bulunamadı. Sayfayı yenileyip kontrol edin.',422:'Girilen bilgileri kontrol edip tekrar deneyin.'};
    const message=errorMessage(j)||defaults[r.status]||'İşlem tamamlanamadı. Bilgileri kontrol edip tekrar deneyin.';
    const payload=j&&typeof j==='object'&&!Array.isArray(j)?j:{};
    const errors=payload.errors||(Array.isArray(payload.detail)?payload.detail:payload.detail?.errors);
    return {r,j:{...payload,errors,detail:message,message}};
  }
  if(!j||typeof j!=='object'||Array.isArray(j))return failure(r,'Sunucudan beklenen yanıt alınamadı. '+requestFailure);
  return {r,j};
};
const escapeHtml=(value)=>String(value??'').replace(/[&<>'\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','\"':'&quot;'}[c]));

document.querySelectorAll('[data-draft-removal]').forEach(form=>{
  const panel=form.closest('.draft-removal'),error=form.querySelector('[role="alert"]'),submit=form.querySelector('[type="submit"]');
  form.querySelector('[data-cancel-removal]').addEventListener('click',()=>{
    panel.open=false;error.hidden=true;panel.querySelector('summary').focus();
  });
  form.addEventListener('submit',async event=>{
    event.preventDefault();
    if(submit.disabled)return;
    submit.disabled=true;error.hidden=true;
    const {r,j}=await jsonFetch(form.action,{method:'POST',headers:{Accept:'application/json'},body:new FormData(form)});
    if(r.ok){drafts.allowNavigation();location.href=j.redirect_url;return}
    error.textContent=j.detail;error.hidden=false;error.focus();submit.disabled=false;
  });
});

(function(){
  const button=document.getElementById('notificationButton'),panel=document.getElementById('notificationPanel'),list=document.getElementById('notificationList'),badge=document.getElementById('notificationBadge');
  if(!button||!panel||!list||!badge)return;
  let items=[];
  function render(){
    const unread=items.filter(item=>!item.is_read).length;
    badge.textContent=String(unread);badge.hidden=unread===0;
    list.innerHTML=items.length?items.map(item=>`<a class="notification-item ${item.is_read?'':'unread'}" href="${escapeHtml(item.link||'/dashboard')}" data-notification="${item.id}"><b>${escapeHtml(item.message)}</b><span>${new Date(item.created_at).toLocaleString('tr-TR')}</span></a>`).join(''):'<p class="muted">Yeni bildirim yok.</p>';
    list.querySelectorAll('[data-notification]').forEach(link=>link.addEventListener('click',async event=>{
      const item=items.find(row=>String(row.id)===link.dataset.notification);
      if(item&&!item.is_read){event.preventDefault();await jsonFetch('/api/notifications/'+item.id+'/read',{method:'POST'});location.href=link.href}
    }));
  }
  async function load(){const {r,j}=await jsonFetch('/api/notifications');if(r.ok){items=j.items||[];render()}}
  button.addEventListener('click',()=>{panel.hidden=!panel.hidden;if(!panel.hidden)load()});
  document.getElementById('closeNotifications')?.addEventListener('click',()=>panel.hidden=true);
  load();
})();

(function(){
  const open=document.getElementById('changePasswordButton'),modal=document.getElementById('passwordModal');
  if(!open||!modal)return;
  const current=document.getElementById('currentPassword'),next=document.getElementById('newPassword'),confirm=document.getElementById('confirmPassword');
  open.addEventListener('click',()=>{modal.hidden=false;current.focus()});
  document.getElementById('cancelPasswordChange')?.addEventListener('click',()=>{modal.hidden=true;current.value=next.value=confirm.value=''});
  document.getElementById('savePasswordChange')?.addEventListener('click',async()=>{
    const {r,j}=await jsonFetch('/api/me/change-password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({current_password:current.value,new_password:next.value,confirmation:confirm.value})});
    if(!r.ok){toast(j.detail||'Parola değiştirilemedi.');return}
    modal.hidden=true;current.value=next.value=confirm.value='';toast('Parolanız değiştirildi.');
  });
})();

function removeUnusedNewActivity(){const row=document.querySelector('#activityBody tr[data-new="1"]');if(!row)return;const hasText=[...row.querySelectorAll('input,textarea')].some(el=>el.value.trim());if(!hasText)row.remove();}
document.querySelectorAll('.tab').forEach(btn=>btn.addEventListener('click',()=>{if(btn.dataset.tab!=='activities')removeUnusedNewActivity();document.querySelectorAll('.tab').forEach(b=>b.classList.remove('active'));document.querySelectorAll('.tabpane').forEach(p=>p.classList.remove('active'));btn.classList.add('active');document.getElementById(btn.dataset.tab)?.classList.add('active')}));

// Drafts stay in the current DOM. Only a confirmed save advances that record's
// baseline; edits made while a request is pending remain unsaved.
const drafts=(()=>{
  const states=new WeakMap();
  const fields=record=>[...record.querySelectorAll('[data-field], [data-actual-form] input:not([type="hidden"]), [data-actual-form] textarea, [data-actual-form] select')];
  const key=field=>field.dataset.field||field.name;
  const values=record=>Object.fromEntries(fields(record).map(field=>[key(field),field.value]));
  let navigationApproved=false;
  function render(record){
    const state=states.get(record);
    if(!state)return;
    state.dirty=state.failed||JSON.stringify(values(record))!==JSON.stringify(state.baseline);
    record.classList.toggle('has-draft',state.dirty);
    state.marker.hidden=!state.dirty&&!state.saving&&!state.saved;
    state.marker.textContent=state.dirty?'Kaydedilmedi':(state.saving?'Kaydediliyor…':'Kaydedildi');
    state.marker.classList.toggle('unsaved',state.dirty);
  }
  function register(record){
    const marker=document.createElement('p');marker.className='draft-status';marker.setAttribute('role','status');
    (record.querySelector('h2, h3')||record.firstElementChild).after(marker);
    states.set(record,{baseline:values(record),marker,dirty:false,saving:false,saved:false,failed:!!record.querySelector('[role="alert"]:not([hidden])')});
    render(record);
    ['input','change'].forEach(type=>record.addEventListener(type,()=>{navigationApproved=false;render(record)}));
  }
  function error(record,message,invalidFields=[]){
    let box=record.querySelector('.draft-error');
    if(!box){box=document.createElement('p');box.className='draft-error';box.id=`draft-error-${record.id||record.dataset.id}`;box.setAttribute('role','alert');record.append(box)}
    box.textContent=errorMessage(message)||'Kayıt yapılamadı. Bu kaydın alanlarını kontrol edip tekrar deneyin.';
    fields(record).forEach(field=>{if(invalidFields.includes(key(field))){field.setAttribute('aria-invalid','true');field.setAttribute('aria-describedby',box.id)}});
    states.get(record).failed=true;render(record);
  }
  function begin(record){
    const state=states.get(record);if(!state||state.saving)return null;
    state.saving=true;
    record.querySelectorAll('.save-indicator, [data-actual-form] button').forEach(button=>button.disabled=true);
    render(record);return values(record);
  }
  function finish(record){
    const state=states.get(record);state.saving=false;
    record.querySelectorAll('.save-indicator, [data-actual-form] button').forEach(button=>button.disabled=false);
    render(record);
  }
  function saved(record,baseline){
    const state=states.get(record);state.baseline=baseline;state.failed=false;state.saved=true;
    record.querySelectorAll('.draft-error, [id^="form-error-"]').forEach(box=>box.remove());
    fields(record).forEach(field=>{field.removeAttribute('aria-invalid');field.removeAttribute('aria-describedby')});
    render(record);
  }
  const records=()=>[...document.querySelectorAll('[data-draft-record]')];
  const hasUnsaved=()=>records().some(record=>{render(record);const state=states.get(record);return state&&(state.dirty||state.saving)});
  const initial=records();initial.forEach(register);
  if(initial.length){
    // Browsers ignore custom beforeunload text. In-app navigation uses this
    // Turkish dialog; reload/tab-close also gets the browser's native warning.
    const dialog=document.createElement('dialog');dialog.className='draft-confirm';dialog.setAttribute('aria-labelledby','draft-confirm-title');
    dialog.innerHTML='<h2 id="draft-confirm-title">Kaydedilmemiş değişiklikler var</h2><p>Bu sayfadan ayrılırsanız kaydedilmemiş değişiklikler kaybolacak. Ayrılmak istiyor musunuz?</p><div class="actions"><button type="button" class="button primary" data-stay>Sayfada kal</button><button type="button" class="button" data-leave>Kaydetmeden ayrıl</button></div>';
    document.body.append(dialog);
    let leave=null;
    function confirm(action){if(dialog.open)return;leave=action;dialog.showModal();dialog.querySelector('[data-stay]').focus()}
    dialog.querySelector('[data-stay]').addEventListener('click',()=>{leave=null;dialog.close()});
    dialog.addEventListener('cancel',()=>leave=null);
    dialog.querySelector('[data-leave]').addEventListener('click',()=>{const action=leave;leave=null;dialog.close();navigationApproved=true;action?.()});
    window.addEventListener('beforeunload',event=>{
      if(navigationApproved||!hasUnsaved())return;
      event.preventDefault();event.returnValue='Kaydedilmemiş değişiklikler var. Ayrılmak istiyor musunuz?';
    });
    document.addEventListener('click',event=>{
      const link=event.target.closest('a[href]');
      if(!link||navigationApproved||event.button!==0||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey||link.hasAttribute('download')||(link.target&&link.target!=='_self'))return;
      const destination=new URL(link.href,location.href);
      if(destination.origin===location.origin&&destination.pathname===location.pathname&&destination.search===location.search)return;
      if(!hasUnsaved())return;
      event.preventDefault();event.stopImmediatePropagation();confirm(()=>link.click());
    },true);
    document.addEventListener('submit',event=>{
      if(event.defaultPrevented||event.target.matches('[data-actual-form]')||navigationApproved||!hasUnsaved())return;
      event.preventDefault();const form=event.target,button=event.submitter;confirm(()=>form.requestSubmit(button));
    });
  }
  return {fields,key,values,register,render,error,begin,finish,saved,allowNavigation:()=>{navigationApproved=true}};
})();

async function saveIndicatorCard(card){
  const data=drafts.begin(card);if(!data)return false;
  try{
    const {r,j}=await jsonFetch(`/api/indicators/${card.dataset.id}/save`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
    if(!r.ok){drafts.error(card,j.detail);return false}
    drafts.saved(card,data);
    card.querySelector('h3').textContent=data.name.trim();
    const issues=j.issues||[],badge=card.querySelector('.record-head .badge');
    badge.textContent=`${issues.length} kontrol`;badge.classList.toggle('bad',!!issues.length);badge.classList.toggle('ok',!issues.length);
    card.classList.toggle('has-issue',!!issues.length);card.classList.toggle('validated',!issues.length);
    card.querySelector('.issue-list')?.remove();
    if(issues.length){const list=document.createElement('div');list.className='issue-list';issues.forEach(issue=>{const button=document.createElement('button');button.type='button';button.className='issue-jump';button.dataset.issue=issue;button.textContent=issue;list.append(button)});card.querySelector('.record-head').after(list)}
    toast(issues.length?`Kaydedildi · ${issues.length} kontrol kaldı`:'Kaydedildi · kontrol temiz');return true;
  }finally{drafts.finish(card)}
}

document.addEventListener('submit',async event=>{
  const form=event.target;if(!form.matches('[data-actual-form]'))return;
  event.preventDefault();
  const record=form.closest('[data-draft-record]'),sent=drafts.begin(record);if(!sent)return;
  try{
    const token=document.querySelector('meta[name="csrf-token"]')?.content;
    const response=await fetch(form.action,{method:'POST',headers:token?{'X-CSRF-Token':token}:{},body:new URLSearchParams(new FormData(form))});
    if(response.status===401||(response.redirected&&new URL(response.url).pathname==='/login')){
      drafts.error(record,'Oturumunuz sona ermiş veya giriş yapmanız gerekiyor. Yeniden giriş yapın; ardından kayıt durumunu kontrol edin.');return;
    }
    if(response.status>=500){drafts.error(record,'Sunucu isteği tamamlayamadı. '+requestFailure);return}
    if(!response.headers.get('content-type')?.includes('text/html')){
      let message;try{message=errorMessage(await response.json())}catch{}
      drafts.error(record,message||'Sunucudan beklenen yanıt alınamadı. '+requestFailure);return;
    }
    const page=new DOMParser().parseFromString(await response.text(),'text/html');
    const replacement=page.getElementById(record.id);
    if(!response.ok){
      const invalidFields=[...(replacement?.querySelectorAll('[aria-invalid="true"]')||[])].map(drafts.key);
      drafts.error(record,replacement?.querySelector('[role="alert"]')?.textContent||page.querySelector('main [role="alert"]')?.textContent||'Gerçekleşme kaydedilemedi. Alanları kontrol edip tekrar deneyin.',invalidFields);return;
    }
    if(!replacement?.querySelector('[data-actual-form]')){drafts.error(record,'Kayıt sonucu ekranda doğrulanamadı. '+requestFailure);return}
    const current=drafts.values(record),focused=document.activeElement;
    const focusKey=record.contains(focused)?drafts.key(focused):null;
    const selection=focused?.selectionStart;
    const detailsOpen=record.querySelector('details')?.open;
    record.replaceWith(replacement);drafts.register(replacement);
    const baseline=drafts.values(replacement);
    // The server response carries the new CAS revision and complete history.
    // Preserve only changes made after submitting, atop the saved baseline.
    drafts.fields(replacement).forEach(field=>{const key=drafts.key(field);if(current[key]!==sent[key])field.value=current[key]});
    if(detailsOpen&&replacement.querySelector('details'))replacement.querySelector('details').open=true;
    drafts.saved(replacement,baseline);
    if(focusKey){const next=drafts.fields(replacement).find(field=>drafts.key(field)===focusKey);next?.focus();if(selection!=null&&next?.setSelectionRange)next.setSelectionRange(selection,selection)}
    toast('Gerçekleşme kaydedildi.');
  }catch{
    drafts.error(record,'Sunucuya ulaşılamadı. İnternet bağlantınızı kontrol edin. '+requestFailure);
  }finally{drafts.finish(record)}
});
document.querySelectorAll('.save-indicator').forEach(btn=>btn.addEventListener('click',()=>saveIndicatorCard(btn.closest('.record'))));
document.querySelectorAll('.fix-unit').forEach(btn=>btn.addEventListener('click',async()=>{const card=btn.closest('.record');const unit=card.querySelector('[data-field="unit"]');unit.value='Adet';unit.focus();unit.classList.add('field-fixed');unit.scrollIntoView({behavior:'smooth',block:'center'});toast('Öneri uygulandı · kontrol ediliyor.');await saveIndicatorCard(card)}));
document.addEventListener('click',event=>{const btn=event.target.closest('.issue-jump');if(!btn)return;const card=btn.closest('.record');const text=btn.dataset.issue||'';let field=null;if(text.includes('Ölçü')||text.includes('ölçü'))field=card.querySelector('[data-field="unit"]');else if(text.includes('Gösterge adı'))field=card.querySelector('[data-field="name"]');else if(text.includes('açıklama')||text.includes('Açıklama'))field=card.querySelector('[data-field="explanation"]');else if(text.includes('Hesaplama'))field=card.querySelector('[data-field="calculation_method"]');else if(text.includes('Verinin'))field=card.querySelector('[data-field="data_source"]');else if(text.includes('hedefi'))field=card.querySelector('[data-field$="_target"]');field?.scrollIntoView({behavior:'smooth',block:'center'});field?.focus();field?.classList.add('field-attention');setTimeout(()=>field?.classList.remove('field-attention'),1600)});

const submit=document.getElementById('submitDepartment');if(submit)submit.addEventListener('click',async()=>{const {r,j}=await jsonFetch(`/api/departments/${submit.dataset.department}/submit`,{method:'POST'});if(!r.ok){toast(j.message||j.detail||'Gönderim yapılamadı.');if(j.errors?.length){const box=document.createElement('div');box.className='return-note';const list=document.createElement('ul');j.errors.forEach(message=>{const li=document.createElement('li');li.textContent=errorMessage(message);list.append(li)});box.append(list);submit.after(box);box.scrollIntoView({behavior:'smooth',block:'center'});return}const first=j.problems&&Object.keys(j.problems)[0];if(first){const card=document.querySelector(`.record[data-id="${first}"]`);card?.scrollIntoView({behavior:'smooth',block:'center'});return}const firstActivity=j.activity_problems&&Object.keys(j.activity_problems)[0];if(firstActivity){document.querySelector('.tab[data-tab="activities"]')?.click();setTimeout(()=>{const row=document.querySelector(`tr[data-activity="${firstActivity}"]`);row?.scrollIntoView({behavior:'smooth',block:'center'});row?.querySelector('.activity-subprogram')?.classList.add('field-attention')},120)}return}toast('Paket Strateji Geliştirme incelemesine gönderildi.');setTimeout(()=>location.assign(j.redirect_url),700)});

function setActivityEditMode(tr,editing){tr.classList.toggle('editing-row',editing);tr.querySelectorAll('.activity-name,.activity-explanation,.activity-cost').forEach(i=>i.readOnly=!editing);const sub=tr.querySelector('.activity-subprogram');if(sub)sub.disabled=!editing;const edit=tr.querySelector('.edit-activity');const del=tr.querySelector('.delete-activity');if(edit){edit.textContent=editing?'Kaydet':'Düzenle';edit.classList.toggle('primary',editing)}if(del){del.textContent=editing?'Vazgeç':'Sil';del.dataset.mode=editing?'cancel':''}}
async function saveActivity(tr){const name=tr.querySelector('.activity-name');if(!name.value.trim()){name.focus();name.classList.add('field-attention');toast('Faaliyet adı boş bırakılamaz.');return}const sub=tr.querySelector('.activity-subprogram');if(!sub?.value){sub?.focus();sub?.classList.add('field-attention');toast('Program / Alt Program seçimi zorunlu.');return}const body={subprogram_id:sub.value,name:name.value,explanation:tr.querySelector('.activity-explanation')?.value||''};tr.querySelectorAll('.activity-cost').forEach(i=>body[`cost_${i.dataset.year}_${i.dataset.kind}${i.dataset.funding?"_"+i.dataset.funding:""}`]=i.value);const {r,j}=await jsonFetch(`/api/activities/${tr.dataset.activity}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});if(!r.ok){toast(j.detail||'Faaliyet kaydedilemedi.');return}tr.querySelectorAll('.activity-cost').forEach(i=>i.value=trNumber(i.value,true));applySavedActivityTotals(tr,j);setActivityEditMode(tr,false);toast('Faaliyet güncellendi.');return true}

// Exact cents for live source comparison; no floating point money arithmetic.
function sourceMoneyCents(raw){
  let text=String(raw??'').trim();
  if(!text)return null;
  if(!/^(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d{1,2})?$/.test(text))return null;
  const [whole,fraction='']=text.replaceAll('.','').split(',');
  return BigInt(whole)*100n+BigInt(fraction.padEnd(2,'0'));
}
function sourceDecimalCents(raw){const [whole,fraction=""]=String(raw).split(".");return BigInt(whole)*100n+BigInt(fraction.padEnd(2,"0"))}
function displaySourceCents(value){
  if(value===null)return 'Belirlenmedi';
  const digits=value.toString().padStart(3,'0');
  return digits.slice(0,-2).replace(/\B(?=(\d{3})+(?!\d))/g,'.')+','+digits.slice(-2);
}
function applySavedActivityTotals(tr,result){
  tr.querySelectorAll('[data-cost-key]').forEach(cell=>cell.dataset.savedTotal=result.cost_totals?.[cell.dataset.costKey]??'');
  refreshSavedActivityTotals();
}
async function confirmActivitySourceTotal(box){
  const tr=box.closest('tr'),prefix=`cost_${box.dataset.year}_${box.dataset.kind}`;
  const body={[prefix+'_use_computed']:true,[prefix+'_reason']:box.querySelector('.source-total-reason').value};
  tr.querySelectorAll('.activity-cost').forEach(field=>{
    if(field.dataset.year===box.dataset.year&&field.dataset.kind===box.dataset.kind)body[prefix+'_'+field.dataset.funding]=field.value;
  });
  const {r,j}=await jsonFetch(`/api/activities/${tr.dataset.activity}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(!r.ok){toast(j.detail||'Kaynak toplamı kararı kaydedilemedi.');return}
  applySavedActivityTotals(tr,j);box.remove();toast('Hesaplanan toplam gerekçesiyle kaydedildi.');
}
function refreshSavedActivityTotals(){
  document.querySelectorAll('[data-activity-total]').forEach(label=>{
    const key=label.dataset.activityTotal;
    const amounts=[...document.querySelectorAll('#activityBody [data-cost-key]')].filter(cell=>cell.dataset.costKey===key).map(cell=>cell.dataset.savedTotal?sourceDecimalCents(cell.dataset.savedTotal):null);
    const total=amounts.length&&amounts.every(v=>v!==null)?amounts.reduce((a,b)=>a+b,0n):null;
    label.textContent=total===null?'Eksik veri':displaySourceCents(total);
    const personnel=[...document.querySelectorAll('.personnel-cost')].find(field=>`${field.dataset.year}:${field.dataset.kind}`===key);
    const general=[...document.querySelectorAll('[data-general-total]')].find(el=>el.dataset.generalTotal===key);
    if(general)general.textContent=total!==null&&personnel?.dataset.savedAmount?displaySourceCents(total+sourceDecimalCents(personnel.dataset.savedAmount)):'Eksik veri';
  });
}
function refreshSourceDisagreements(tr){
  tr.querySelectorAll('.source-disagreement').forEach(box=>{
    const fields=[...tr.querySelectorAll('.activity-cost')].filter(i=>i.dataset.year===box.dataset.year&&i.dataset.kind===box.dataset.kind);
    const amounts=fields.map(i=>sourceMoneyCents(i.value));
    const computed=amounts.length===2&&amounts.every(v=>v!==null)?amounts[0]+amounts[1]:null;
    const source=sourceDecimalCents(box.dataset.source);
    box.hidden=computed===source;box.querySelector('.computed-total').textContent=displaySourceCents(computed);
  });
}
document.addEventListener('input',e=>{if(e.target.matches('.activity-cost'))refreshSourceDisagreements(e.target.closest('tr'))});
document.addEventListener('click',async e=>{
  const button=e.target.closest('.confirm-source-total');if(!button)return;
  const box=button.closest('.source-disagreement'),reason=box.querySelector('.source-total-reason');
  if(reason.value.trim().length<10){reason.focus();toast('Karar gerekçesi en az 10 karakter olmalı.');return}
  button.disabled=true;try{await confirmActivitySourceTotal(box)}finally{button.disabled=false}
});

document.addEventListener('click',async(e)=>{const edit=e.target.closest('.edit-activity');if(edit){const tr=edit.closest('tr');if(edit.textContent.trim()==='Düzenle'){setActivityEditMode(tr,true);tr.querySelector('.activity-name')?.focus()}else if(edit.textContent.trim()==='Kaydet'){await saveActivity(tr)}else if(edit.textContent.trim()==='Vazgeç'){location.reload()}return}const del=e.target.closest('.delete-activity');if(del){const tr=del.closest('tr');if(del.dataset.mode==='cancel'){location.reload();return}if(del.dataset.mode!=='confirm'){del.dataset.mode='confirm';del.textContent='Evet, sil';const editBtn=tr.querySelector('.edit-activity');if(editBtn){editBtn.textContent='Vazgeç';editBtn.classList.remove('primary')}toast('Silmek için “Evet, sil”e tekrar basın.');return}const {r,j}=await jsonFetch(`/api/activities/${tr.dataset.activity}`,{method:'DELETE'});if(!r.ok){toast(j.detail||'Faaliyet silinemedi.');return}tr.remove();toast('Faaliyet silindi.');setTimeout(()=>location.assign(j.redirect_url),350);return}});

const add=document.getElementById('addActivity');if(add)add.addEventListener('click',()=>{if(document.querySelector('#activityBody tr[data-new="1"]')){document.querySelector('#activityBody tr[data-new="1"] .activity-name')?.focus();return}const proto=document.getElementById('subprogramPrototype');const columns=[...document.querySelectorAll('.cost-table thead th')].slice(2,-1);const tr=document.createElement('tr');tr.dataset.new='1';tr.className='new-activity-row editing-row';const costCells=columns.map(th=>{const label=th.textContent.trim();const m=label.match(/(20\d{2})/);let kind=label.includes('Haziran')?'midyear_spend':label.includes('Yıl Sonu')?'year_end_estimate':label.includes('Bütçe')?'budget':'forecast';return `<td>${["inside","outside"].map(f=>`<label>Bütçe ${f==="inside"?"İçi":"Dışı"}<input class="money activity-cost" data-year="${m?m[1]:''}" data-kind="${kind}" data-funding="${f}" placeholder="Belirlenmedi"></label>`).join('')}</td>`}).join('');tr.innerHTML=`<td><select class="activity-subprogram">${proto?proto.innerHTML:''}</select></td><td><input class="activity-name" placeholder="Faaliyet adı"><textarea class="activity-explanation" rows="2" placeholder="Faaliyet açıklaması"></textarea></td>${costCells}<td><div class="rowbuttons"><button class="button small primary save-new">Kaydet</button><button class="button small cancel-new">İptal</button></div></td>`;document.getElementById('activityBody').prepend(tr);tr.querySelector('.activity-name').focus();tr.scrollIntoView({behavior:'smooth',block:'center'});tr.querySelector('.cancel-new').addEventListener('click',()=>tr.remove());tr.querySelector('.save-new').addEventListener('click',async()=>{const name=tr.querySelector('.activity-name');if(!name.value.trim()){name.focus();toast('Faaliyet adı zorunlu.');return}const sub=tr.querySelector('.activity-subprogram');if(!sub?.value){sub?.focus();sub?.classList.add('field-attention');toast('Program / Alt Program seçimi zorunlu.');return}const body={subprogram_id:sub.value,name:name.value,explanation:tr.querySelector('.activity-explanation')?.value||''};tr.querySelectorAll('.activity-cost').forEach(i=>body[`cost_${i.dataset.year}_${i.dataset.kind}${i.dataset.funding?"_"+i.dataset.funding:""}`]=i.value);const {r,j}=await jsonFetch('/api/activities',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});if(!r.ok){toast(j.detail||'Faaliyet eklenemedi.');return}toast('Faaliyet eklendi.');setTimeout(()=>location.assign(j.redirect_url),500)})});

const savePersonnel=document.getElementById('savePersonnel');if(savePersonnel)savePersonnel.addEventListener('click',async()=>{const body={};document.querySelectorAll('.personnel-cost').forEach(i=>body[`cost_${i.dataset.year}_${i.dataset.kind}${i.dataset.funding?"_"+i.dataset.funding:""}`]=i.value);const {r,j}=await jsonFetch(`/api/departments/${savePersonnel.dataset.department}/personnel-costs`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});if(!r.ok){toast(j.detail||'Personel ve SGK giderleri kaydedilemedi.');return}document.querySelectorAll('.personnel-cost').forEach(i=>i.value=trNumber(i.value,true));toast('Personel ve SGK giderleri kaydedildi.');setTimeout(()=>location.assign(j.redirect_url),450)});

document.querySelectorAll('.money').forEach(i=>i.addEventListener('blur',()=>{if(!i.readOnly)i.value=trNumber(i.value,true)}));

let pendingReturn=null;document.querySelectorAll('.review-action').forEach(btn=>btn.addEventListener('click',async()=>{if(btn.dataset.decision==='return'){pendingReturn=btn.dataset.id;document.getElementById('reviewModal').hidden=false;document.getElementById('returnNote').focus();return}if(!window.confirm('Bu müdürlük paketi onaylanacak ve veri girişi kilitlenecek. Devam edilsin mi?'))return;await decide(btn.dataset.id,'approve','')}));async function decide(id,decision,note){const {r,j}=await jsonFetch(`/api/submissions/${id}/decision`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({decision,note})});if(!r.ok){
  const box=document.getElementById('reviewErrors-'+id);
  if(decision==='approve'&&box){
    const title=document.createElement('strong');title.textContent='Paket onaylanamadı. Aşağıdaki sorunları düzeltip yeniden onaylayın.';
    const list=document.createElement('ul');
    const messages=Array.isArray(j.errors)&&j.errors.length?j.errors:[j.detail||'İşlem yapılamadı.'];
    messages.forEach(message=>{const item=document.createElement('li');item.textContent=errorMessage(message)||'Bilgileri kontrol edip tekrar deneyin.';list.append(item)});
    box.replaceChildren(title,list);box.hidden=false;box.focus();box.scrollIntoView({behavior:'smooth',block:'center'});
  }else toast(j.detail||'İşlem yapılamadı.');
  return;
}
const box=document.getElementById('reviewErrors-'+id);if(box){box.replaceChildren();box.hidden=true}
toast(decision==='approve'?'Müdürlük paketi onaylandı.':'Paket müdürlüğe iade edildi.');setTimeout(()=>location.reload(),600)}
const cancelReturn=document.getElementById('cancelReturn');if(cancelReturn)cancelReturn.addEventListener('click',()=>{document.getElementById('reviewModal').hidden=true;pendingReturn=null});const confirmReturn=document.getElementById('confirmReturn');if(confirmReturn)confirmReturn.addEventListener('click',()=>{const note=document.getElementById('returnNote').value.trim();if(!note){toast('İade açıklaması zorunlu.');return}decide(pendingReturn,'return',note)});

const npb=document.getElementById('newPeriodBtn');if(npb)npb.addEventListener('click',()=>{document.getElementById('newPeriodForm').hidden=false;document.getElementById('newPeriodYear').focus()});const cp=document.getElementById('cancelPeriod');if(cp)cp.addEventListener('click',()=>document.getElementById('newPeriodForm').hidden=true);const createP=document.getElementById('createPeriod');if(createP)createP.addEventListener('click',async()=>{const year=document.getElementById('newPeriodYear').value;const base=document.getElementById('basePeriod').value;const {r,j}=await jsonFetch('/api/periods',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({year,base_period_id:base})});if(!r.ok){toast(j.detail||'Dönem oluşturulamadı.');return}toast(`${j.year} dönemi taslak olarak oluşturuldu.`);setTimeout(()=>location.reload(),600)});document.querySelectorAll('.verify-period').forEach(b=>b.addEventListener('click',async()=>{const {r,j}=await jsonFetch(`/api/periods/${b.dataset.id}/verify-template`,{method:'POST'});if(!r.ok){toast(j.detail||'Şablon doğrulanamadı.');return}toast('Şablon doğrulandı.');setTimeout(()=>location.reload(),500)}));document.querySelectorAll('.activate-period').forEach(b=>b.addEventListener('click',async()=>{const {r,j}=await jsonFetch(`/api/periods/${b.dataset.id}/activate`,{method:'POST'});if(!r.ok){toast(j.detail||'Dönem aktif edilemedi.');return}toast('Dönem aktif edildi.');setTimeout(()=>location.reload(),500)}));

function renderTemplateReport(j){const box=document.getElementById('templateResult');if(!box)return;const present=j.present||[],missing=j.missing||[],departments=j.departments||[],extra=j.extra||[];box.innerHTML=`<div class="template-report"><div class="template-box present"><h4>Bulunan alanlar · ${present.length}</h4><ul>${present.map(x=>`<li>${escapeHtml(x)}</li>`).join('')}</ul></div><div class="template-box missing"><h4>Eksik / eşleşmeyen alanlar · ${missing.length}</h4><ul>${missing.map(x=>`<li>${escapeHtml(x)}</li>`).join('')||'<li>Eksik alan bulunmadı.</li>'}</ul></div></div>${departments.length?`<p class="muted"><b>Şablonda bulunan müdürlükler:</b> ${departments.map(escapeHtml).join(' · ')}</p>`:''}${extra.length?`<p class="muted">Olası yeni/farklı başlıklar: ${extra.map(escapeHtml).join(' · ')}</p>`:''}`}
const tu=document.getElementById('templateUpload');if(tu)tu.addEventListener('change',async()=>{if(!tu.files[0])return;const fd=new FormData();fd.append('file',tu.files[0]);toast('Şablon analiz ediliyor...');const {r,j}=await jsonFetch(`/api/periods/${tu.dataset.period}/template-upload`,{method:'POST',body:fd});if(!r.ok){toast(j.detail||'Şablon analiz edilemedi.');return}renderTemplateReport(j);toast(`${j.present.length} alan bulundu · ${j.missing.length} alan kontrol edilmeli.`)});document.querySelectorAll('.snapshot-item').forEach(b=>b.addEventListener('click',async()=>{const {r,j}=await jsonFetch(`/api/template-snapshots/${b.dataset.snapshot}`);if(r.ok)renderTemplateReport(j)}));

function renderImportReport(j){
  const box=document.getElementById('importResult');if(!box)return;
  const s=j.summary||{};const batchId=j.batch_id||j.id;const status=j.status||'preview';
  const mappings=(j.mappings||[]).slice(0,12);
  const mappingHtml=mappings.length?`<div class="import-preview"><h4>Müdürlük eşleştirmesi</h4>${mappings.map(m=>`<div class="import-dept"><b>${escapeHtml(m.source_name)}</b><span>${m.action==='match'?`→ ${escapeHtml(m.target_name)} · eşleşti`:m.action==='create'?`→ ${escapeHtml(m.target_name)} · yeni kayıt`:`⚠ ${escapeHtml(m.reason||'eşleştirme gerekli')}`}</span></div>`).join('')}</div>`:'';
  const linkWarning=s.unlinked_activity_estimate?`<p class="smallnote">${s.unlinked_activity_estimate} faaliyet için Program / Alt Program bağlantısı kaynak dosyadan güvenle belirlenemiyor. Kayıtlar içe aktarılır; müdürlük gönderiminden önce eşleştirme zorunludur.</p>`:'';
  const applyHtml=batchId&&j.can_apply&&status==='preview'?`<div class="import-apply"><button class="button primary" id="applyImport" data-batch="${batchId}">Önizlemeyi Veritabanına Uygula</button><span>Yalnız taslak/iadedeki müdürlükler güncellenir; incelemede veya onaylı paketlerin üzerine yazılmaz.</span></div>`:status==='applied'?(j.can_revert?`<div class="import-apply"><span class="ok-text">Bu içe aktarma paketi veritabanına uygulandı.</span><button class="button danger" id="revertImport" data-batch="${batchId}">İçe Aktarmayı Geri Al</button></div>`:`<p class="smallnote">Bu paket uygulandı. Otomatik geri alma kullanılamıyor: ${escapeHtml(j.revert_reason||'veri sonradan değişmiş olabilir.')}</p>`):status==='reverted'?'<p class="muted">Bu içe aktarma paketi güvenli biçimde geri alındı.</p>':(s.unresolved_department_count?`<p class="smallnote">${s.unresolved_department_count} müdürlük eşleştirmesi netleşmeden içe aktarma uygulanamaz.</p>`:'');
  const conflictsHtml=(j.conflicts||[]).length?`<div class="import-conflicts"><h3>Kaynak tutarı çelişkileri</h3><p>Her çelişki için kaynak tutarı seçilip gerekçe kaydedilmeden içe aktarma uygulanamaz.</p>${j.conflicts.map(c=>`<div class="issue-list import-conflict" data-conflict="${escapeHtml(c.id)}"><p>${escapeHtml(c.message)}</p>${c.decision?`<p class="ok-text">Karar: ${escapeHtml(displaySourceCents(sourceDecimalCents(c.decision.chosen_amount)))} · ${escapeHtml(c.decision.reason)}</p>`:status==='preview'?`<label>Kaynak tutarı<select class="conflict-amount"><option value="">Tutar seçin</option>${c.candidates.map(candidate=>`<option value="${escapeHtml(candidate.amount)}">${escapeHtml(displaySourceCents(sourceDecimalCents(candidate.amount)))} · ${candidate.locations.map(loc=>`Tablo ${loc.table_number}, satır ${loc.row_number}`).join(' · ')}</option>`).join('')}</select></label><label>Karar gerekçesi<input class="conflict-reason" minlength="10" placeholder="En az 10 karakter"></label><button type="button" class="button save-conflict">Kararı Kaydet</button>`:''}</div>`).join('')}</div>`:'';
  box.innerHTML=`<div class="cards import-cards"><div class="card"><span>Müdürlük</span><b>${s.department_count||0}</b></div><div class="card"><span>Gösterge</span><b>${s.indicator_count||0}</b></div><div class="card"><span>Faaliyet</span><b>${s.activity_count||0}</b></div><div class="card"><span>Word tablosu</span><b>${s.table_count||0}</b></div></div><div class="import-preview"><h4>İlk müdürlükler</h4>${(j.departments||[]).slice(0,12).map(d=>`<div class="import-dept"><b>${escapeHtml(d.name)}</b><span>${Number(d.indicator_count)||0} gösterge · ${Number(d.activity_count)||0} faaliyet · ${Number(d.block_count)||0} program bloğu</span></div>`).join('')||'<p>Veri bloğu bulunamadı.</p>'}</div>${mappingHtml}${j.warnings&&j.warnings.length?`<div class="issue-list">${j.warnings.slice(0,20).map(w=>`<div>${escapeHtml(w)}</div>`).join('')}</div>`:'<p class="ok-text">Yapısal eşleştirme uyarısı oluşmadı.</p>'}${j.coverage_items&&j.coverage_items.length?`<details class="import-coverage"><summary>Bilgi amaçlı tablolar (${j.coverage_items.length})</summary>${j.coverage_items.map(item=>`<p>${escapeHtml(item.message)}</p>`).join('')}</details>`:''}${j.review_items?.length?`<details class="import-review"><summary>Kaynak kontrolü gereken hücreler (${j.review_items.length})</summary>${j.review_items.map(item=>`<p>${escapeHtml(item.table_number?`Tablo ${item.table_number}: `:'')}${escapeHtml(item.message)} Ham kaynak: ${escapeHtml(item.raw_text)}</p>`).join('')}</details>`:''}${linkWarning}${conflictsHtml}${applyHtml}<p class="muted">Önizleme tek başına veritabanındaki performans kayıtlarını değiştirmez.</p>`;
  box.querySelectorAll('.save-conflict').forEach(button=>button.addEventListener('click',async()=>{
    const item=button.closest('.import-conflict');const amount=item.querySelector('.conflict-amount').value;
    const reason=item.querySelector('.conflict-reason').value.trim();
    if(!amount||reason.length<10){toast('Kaynak tutarı seçip en az 10 karakterlik gerekçe yazın.');return}
    button.disabled=true;
    const {r,j:result}=await jsonFetch(`/api/import-batches/${batchId}/conflicts/${item.dataset.conflict}/decision`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({chosen_amount:amount.replace('.',','),reason})});
    if(!r.ok){button.disabled=false;toast(result.detail||'Karar kaydedilemedi.');return}
    renderImportReport(result);toast('Kaynak tutarı kararı gerekçesiyle kaydedildi.');
  }));
  document.getElementById('applyImport')?.addEventListener('click',async(e)=>{
    const btn=e.currentTarget;btn.disabled=true;btn.textContent='İçe aktarılıyor...';
    const {r,j:result}=await jsonFetch(`/api/import-batches/${btn.dataset.batch}/apply`,{method:'POST'});
    if(!r.ok){btn.disabled=false;btn.textContent='Önizlemeyi Veritabanına Uygula';toast(result.detail||'İçe aktarma uygulanamadı.');return}
    toast(`${result.departments} müdürlük · ${result.indicators} gösterge · ${result.activities} faaliyet içe aktarıldı.`);
    setTimeout(()=>location.reload(),900);
  });
  document.getElementById('revertImport')?.addEventListener('click',async(e)=>{
    const btn=e.currentTarget;
    if(!window.confirm('Bu Word içe aktarması uygulanmadan önceki veriler geri yüklenecek. Devam edilsin mi?'))return;
    btn.disabled=true;btn.textContent='Geri alınıyor...';
    const {r,j:result}=await jsonFetch(`/api/import-batches/${btn.dataset.batch}/revert`,{method:'POST'});
    if(!r.ok){btn.disabled=false;btn.textContent='İçe Aktarmayı Geri Al';toast(result.detail||'Geri alma yapılamadı.');return}
    toast(`${result.departments_restored} müdürlük geri yüklendi · ${result.departments_removed} yeni müdürlük kaldırıldı.`);
    setTimeout(()=>location.reload(),900);
  });
}
const diu=document.getElementById('dataImportUpload');if(diu)diu.addEventListener('change',async()=>{if(!diu.files[0])return;const fd=new FormData();fd.append('file',diu.files[0]);toast('Word verileri ayrıştırılıyor...');const {r,j}=await jsonFetch(`/api/periods/${diu.dataset.period}/data-import-preview`,{method:'POST',body:fd});if(!r.ok){toast(j.detail||'Veri önizlemesi oluşturulamadı.');return}renderImportReport(j);toast(`${j.summary.department_count} müdürlük · ${j.summary.indicator_count} gösterge bulundu.`)});document.querySelectorAll('.import-item').forEach(b=>b.addEventListener('click',async()=>{const {r,j}=await jsonFetch(`/api/import-batches/${b.dataset.import}`);if(r.ok)renderImportReport(j)}));

const nub=document.getElementById('newUserBtn');if(nub)nub.addEventListener('click',()=>{document.getElementById('newUserForm').hidden=false;document.getElementById('userName').focus()});document.querySelectorAll('.create-department-user').forEach(button=>button.addEventListener('click',()=>{document.getElementById('newUserForm').hidden=false;document.getElementById('userRole').value='department';document.getElementById('departmentLabel').hidden=false;document.getElementById('userDepartment').value=button.dataset.createDepartment;document.getElementById('userName').focus();document.getElementById('newUserForm').scrollIntoView({behavior:'smooth',block:'center'})}));const cur=document.getElementById('cancelUser');if(cur)cur.addEventListener('click',()=>document.getElementById('newUserForm').hidden=true);const ur=document.getElementById('userRole');if(ur)ur.addEventListener('change',()=>document.getElementById('departmentLabel').hidden=ur.value==='strategy');const su=document.getElementById('saveUser');if(su)su.addEventListener('click',async()=>{const body={full_name:document.getElementById('userName').value,email:document.getElementById('userEmail').value,role:document.getElementById('userRole').value,position:document.getElementById('userPosition').value,department_id:document.getElementById('userDepartment').value,password:document.getElementById('userPassword').value};const {r,j}=await jsonFetch('/api/users',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});if(!r.ok){toast(j.detail||'Kullanıcı oluşturulamadı.');return}toast('Kullanıcı oluşturuldu.');setTimeout(()=>location.reload(),500)});
document.querySelectorAll('.toggle-user-active').forEach(button=>button.addEventListener('click',async()=>{const active=button.dataset.active!=='1';if(!window.confirm(active?'Hesap etkinleştirilsin mi?':'Hesap devre dışı bırakılıp giriş erişimi kapatılsın mı?'))return;const {r,j}=await jsonFetch('/api/users/'+button.dataset.user+'/active',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({active})});if(!r.ok){toast(j.detail||'Hesap durumu değiştirilemedi.');return}toast(active?'Hesap etkinleştirildi.':'Hesap devre dışı bırakıldı.');setTimeout(()=>location.reload(),500)}));
document.querySelectorAll('.show-password-reset').forEach(button=>button.addEventListener('click',()=>{const box=document.querySelector('[data-reset-user="'+button.dataset.user+'"]');box.hidden=!box.hidden;if(!box.hidden)box.querySelector('input').focus()}));
document.querySelectorAll('.save-password-reset').forEach(button=>button.addEventListener('click',async()=>{const box=button.closest('.password-reset'),password=box.querySelector('input').value;const {r,j}=await jsonFetch('/api/users/'+box.dataset.resetUser+'/reset-password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password})});if(!r.ok){toast(j.detail||'Parola yenilenemedi.');return}box.querySelector('input').value='';box.hidden=true;toast('Geçici parola yenilendi.')})); 

// Strategy activity mapping queue: designed for high-volume Word imports.
(function(){
  const selects=[...document.querySelectorAll('.mapping-select')];
  if(!document.getElementById('mappingGroups'))return;
  const topSave=document.getElementById('saveAllMappings');
  const bottomSave=document.getElementById('saveMappingsBottom');
  const count=document.getElementById('selectedMappingCount');
  const filter=document.getElementById('mappingDepartmentFilter');
  const search=document.getElementById('mappingSearch');
  function updateCount(){
    const n=selects.filter(s=>s.value).length;
    if(count)count.textContent=String(n);
    [topSave,bottomSave].forEach(b=>{if(b)b.disabled=n===0});
  }
  selects.forEach(s=>s.addEventListener('change',()=>{s.classList.toggle('changed',!!s.value);updateCount()}));
  document.querySelectorAll('.choose-suggestion').forEach(button=>button.addEventListener('click',()=>{
    const select=selects.find(s=>s.dataset.activity===button.dataset.activity);
    if(!select)return;
    select.value=button.dataset.subprogram||'';
    select.classList.toggle('changed',!!select.value);
    updateCount();
    toast('Öneri seçildi; kaydedilmeden önce kontrol edin.');
  }));
  document.getElementById('selectStrongSuggestions')?.addEventListener('click',()=>{
    let selected=0;
    document.querySelectorAll('.choose-suggestion').forEach(button=>{
      if(Number(button.dataset.score)<50)return;
      const select=selects.find(s=>s.dataset.activity===button.dataset.activity);
      if(!select||select.value)return;
      select.value=button.dataset.subprogram||'';
      select.classList.toggle('changed',!!select.value);
      selected++;
    });
    updateCount();
    toast(selected?selected+' güçlü öneri seçildi; kaydetmeden önce kontrol edin.':'Seçilebilecek yeni güçlü öneri yok.');
  });
  function applyFilter(){
    const did=filter?.value||''; const q=(search?.value||'').trim().toLowerCase();
    document.querySelectorAll('.mapping-group').forEach(group=>{
      const groupOk=!did||group.dataset.department===did;
      let visible=0;
      group.querySelectorAll('.mapping-row').forEach(row=>{
        const ok=groupOk&&(!q||(row.dataset.name||'').includes(q)); row.hidden=!ok;if(ok)visible++;
      });
      group.hidden=visible===0;
    });
  }
  filter?.addEventListener('change',applyFilter);search?.addEventListener('input',applyFilter);
  async function saveMappings(){
    const assignments=selects.filter(s=>s.value).map(s=>({activity_id:s.dataset.activity,subprogram_id:s.value}));
    if(!assignments.length){toast('Kaydedilecek eşleştirme seçilmedi.');return}
    if(!window.confirm(assignments.length+' faaliyet için seçilen Program / Alt Program bağlantıları kaydedilsin mi?'))return;
    [topSave,bottomSave].forEach(b=>{if(b){b.disabled=true;b.dataset.old=b.textContent;b.textContent='Kaydediliyor...'}});
    const {r,j}=await jsonFetch('/api/activity-mappings/bulk',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({assignments})});
    if(!r.ok){[topSave,bottomSave].forEach(b=>{if(b){b.disabled=false;b.textContent=b.dataset.old||'Seçimleri Kaydet'}});toast(j.detail||'Eşleştirmeler kaydedilemedi.');return}
    if(j.errors?.length)toast(`${j.updated} eşleştirme kaydedildi · ${j.errors.length} kayıt kontrol edilmeli.`);else toast(`${j.updated} faaliyet eşleştirildi · ${j.remaining} kayıt kaldı.`);
    setTimeout(()=>location.reload(),800);
  }
  topSave?.addEventListener('click',saveMappings);bottomSave?.addEventListener('click',saveMappings);updateCount();applyFilter();
})();

(function(){
  const file=document.getElementById('mappingCsvFile'),preview=document.getElementById('previewMappingCsv'),apply=document.getElementById('applyMappingCsv'),result=document.getElementById('mappingCsvResult');
  if(!file||!preview||!apply||!result)return;
  let fingerprint='';
  const currentFingerprint=()=>file.files[0]?[file.files[0].name,file.files[0].size,file.files[0].lastModified].join(':'):'';
  const body=()=>{const form=new FormData();form.append('file',file.files[0]);return form};
  file.addEventListener('change',()=>{fingerprint='';apply.disabled=true;result.textContent='Dosya değişti. Uygulamadan önce yeniden kontrol edin.'});
  preview.addEventListener('click',async()=>{
    if(!file.files.length){toast('Önce eşleştirme CSV dosyasını seçin.');return}
    preview.disabled=true;result.textContent='Eşleştirmeler kontrol ediliyor…';
    const {r,j}=await jsonFetch('/api/activity-mappings/import-preview',{method:'POST',body:body()});preview.disabled=false;
    if(!r.ok){result.textContent=j.detail||'CSV kontrol edilemedi.';return}
    if(!j.ok){fingerprint='';apply.disabled=true;result.innerHTML='<b>Dosya uygulanamaz.</b><ul>'+j.errors.map(error=>'<li>'+escapeHtml(error)+'</li>').join('')+'</ul>';return}
    fingerprint=currentFingerprint();apply.disabled=false;
    result.innerHTML='<b class="ok">'+j.count+' faaliyet eşleştirilmeye hazır.</b> Uygulama sırasında dosya yeniden doğrulanacak.';
  });
  apply.addEventListener('click',async()=>{
    if(!fingerprint||fingerprint!==currentFingerprint()){toast('Dosyayı yeniden kontrol edin.');return}
    if(!window.confirm('Önizlemesi doğrulanan faaliyet eşleştirmeleri kaydedilsin mi?'))return;
    apply.disabled=true;result.textContent='Eşleştirmeler kaydediliyor…';
    const {r,j}=await jsonFetch('/api/activity-mappings/import-apply',{method:'POST',body:body()});
    if(!r.ok){const detail=j.detail;result.textContent=(detail&&detail.message)||detail||'Eşleştirmeler kaydedilemedi.';fingerprint='';return}
    result.innerHTML='<b class="ok">'+j.updated+' faaliyet eşleştirildi · '+j.remaining+' kayıt kaldı.</b> İşlem: '+escapeHtml(j.batch_id);
    toast('CSV eşleştirmeleri kaydedildi.');setTimeout(()=>location.reload(),800);
  });
})();
document.querySelectorAll('.revert-mapping-batch').forEach(button=>button.addEventListener('click',async()=>{
  if(!window.confirm('Bu CSV işlem grubundaki eşleştirmeler geri alınsın mı?'))return;
  button.disabled=true;const {r,j}=await jsonFetch('/api/activity-mappings/batches/'+button.dataset.batch+'/revert',{method:'POST'});
  if(!r.ok){button.disabled=false;const detail=j.detail;toast((detail&&detail.message)||detail||'İşlem geri alınamadı.');return}
  toast(j.reverted+' faaliyet yeniden eşleştirme kuyruğuna alındı.');setTimeout(()=>location.reload(),700);
}));

(function(){
  const form=document.getElementById('economicGridForm'),box=document.getElementById('economicGridErrors');
  if(!form||!box)return;
  const button=form.querySelector('button[type="submit"],button:not([type])');
  if(!button)return;
  let saving=false;
  form.addEventListener('submit',async event=>{
    event.preventDefault();if(saving)return;
    saving=true;button.disabled=true;
    try{
      const {r,j}=await jsonFetch(form.action,{method:'POST',headers:{Accept:'application/json'},body:new FormData(form)});
      if(r.ok&&j.ok===true&&j.redirect_url){
        box.replaceChildren();box.hidden=true;location.assign(j.redirect_url);return;
      }
      const title=document.createElement('strong');title.textContent='Tablo kaydı doğrulanamadı. Girdiğiniz değerler bu ekranda korunuyor.';
      const list=document.createElement('ul');
      const messages=Array.isArray(j.errors)&&j.errors.length?j.errors:[j.detail||'İşlem sonucu doğrulanamadı. Yeniden denemeden önce kayıt durumunu kontrol edin.'];
      messages.forEach(message=>{const item=document.createElement('li');item.textContent=errorMessage(message)||'Bilgileri kontrol edip tekrar deneyin.';list.append(item)});
      box.replaceChildren(title,list);box.hidden=false;box.focus();box.scrollIntoView({behavior:'smooth',block:'center'});
    }finally{saving=false;button.disabled=false}
  });
})();

// Released-flow position and PP submission authorisation (CIV-025).
document.querySelectorAll('.toggle-submit-authorization').forEach(button=>button.addEventListener('click',async()=>{
  const can_submit=button.dataset.authorized!=='1';
  const {r,j}=await jsonFetch('/api/users/'+button.dataset.user+'/submit-authorization',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({can_submit})});
  if(!r.ok){toast(j.detail||'Gönderim yetkisi değiştirilemedi. Listeyi yenileyip tekrar deneyin.');return;}
  location.reload();
}));
document.querySelectorAll('.save-user-position').forEach(button=>button.addEventListener('click',async()=>{
  const position=button.closest('tr').querySelector('.user-position').value;
  const {r,j}=await jsonFetch('/api/users/'+button.dataset.user+'/position',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({position})});
  if(!r.ok){toast(j.detail||'Unvan değiştirilemedi. Kullanıcılar ekranını yenileyip tekrar deneyin.');return;}
  location.reload();
}));

// CIV-045: exact programme shares and one atomic directorate save.
(function(){
  const form=document.getElementById('economicSplitForm');
  if(!form)return;
  const box=document.getElementById('economicSplitErrors'),button=form.querySelector('button[type="submit"]');
  form.querySelectorAll('[data-split-cell]').forEach(row=>{
    const inputs=[...row.querySelectorAll('[data-split-share]')],remaining=row.querySelector('[data-split-remaining]');
    function update(){
      if(!row.dataset.sourceAmount){remaining.textContent='Kaynak doğrulanmalı';return}
      const amounts=inputs.map(input=>input.value.trim()?sourceMoneyCents(input.value):0n);
      if(amounts.some(amount=>amount===null)){remaining.textContent='Payı kontrol edin';return}
      const rest=sourceDecimalCents(row.dataset.sourceAmount)-amounts.reduce((sum,value)=>sum+value,0n);
      remaining.textContent=(rest<0n?'-':'')+displaySourceCents(rest<0n?-rest:rest);
    }
    inputs.forEach(input=>input.addEventListener('input',update));update();
  });
  let saving=false;
  form.addEventListener('submit',async event=>{
    event.preventDefault();if(saving)return;
    saving=true;button.disabled=true;
    try{
      const {r,j}=await jsonFetch(form.action,{method:'POST',headers:{Accept:'application/json'},body:new FormData(form)});
      if(r.ok&&j.ok===true&&j.redirect_url){location.assign(j.redirect_url);return}
      box.textContent=errorMessage(j.detail)||'Dağılım kaydedilemedi. Payları kontrol edip tekrar deneyin.';
      box.hidden=false;box.focus();box.scrollIntoView({behavior:'smooth',block:'center'});
    }finally{saving=false;button.disabled=false}
  });
})();
