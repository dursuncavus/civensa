const toast=(msg)=>{const el=document.getElementById('toast');if(!el)return;el.textContent=msg;el.classList.add('show');clearTimeout(window.__toastTimer);window.__toastTimer=setTimeout(()=>el.classList.remove('show'),2800)};
const trNumber=(raw,money=false)=>{let s=String(raw??'').trim().replace(/\s/g,'');if(!s)return '';s=s.replace(/₺/g,'').replace(/\./g,'').replace(',','.');let n=Number(s);if(Number.isNaN(n))return raw;return new Intl.NumberFormat('tr-TR',{minimumFractionDigits:money?2:0,maximumFractionDigits:money?2:2}).format(n)};
const jsonFetch=async(url,options={})=>{const token=document.querySelector('meta[name=\"csrf-token\"]')?.content;if(token){const headers=new Headers(options.headers||{});headers.set('X-CSRF-Token',token);options={...options,headers}}const r=await fetch(url,options);let j={};try{j=await r.json()}catch{}return {r,j}};
const escapeHtml=(value)=>String(value??'').replace(/[&<>'\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','\"':'&quot;'}[c]));

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

async function saveIndicatorCard(card){const data={};card.querySelectorAll('[data-field]').forEach(el=>data[el.dataset.field]=el.value);const {r,j}=await jsonFetch(`/api/indicators/${card.dataset.id}/save`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});if(!r.ok){toast(j.detail||'Kayıt yapılamadı.');return false}toast(j.issues.length?`Kaydedildi · ${j.issues.length} kontrol kaldı`:'Kaydedildi · kontrol temiz');setTimeout(()=>location.reload(),600);return true}
document.querySelectorAll('.save-indicator').forEach(btn=>btn.addEventListener('click',()=>saveIndicatorCard(btn.closest('.record'))));
document.querySelectorAll('.fix-unit').forEach(btn=>btn.addEventListener('click',async()=>{const card=btn.closest('.record');const unit=card.querySelector('[data-field="unit"]');unit.value='Adet';unit.focus();unit.classList.add('field-fixed');unit.scrollIntoView({behavior:'smooth',block:'center'});toast('Öneri uygulandı · kontrol ediliyor.');await saveIndicatorCard(card)}));
document.querySelectorAll('.issue-jump').forEach(btn=>btn.addEventListener('click',()=>{const card=btn.closest('.record');const text=btn.dataset.issue||'';let field=null;if(text.includes('Ölçü')||text.includes('ölçü'))field=card.querySelector('[data-field="unit"]');else if(text.includes('Gösterge adı'))field=card.querySelector('[data-field="name"]');else if(text.includes('açıklama')||text.includes('Açıklama'))field=card.querySelector('[data-field="explanation"]');else if(text.includes('Hesaplama'))field=card.querySelector('[data-field="calculation_method"]');else if(text.includes('Verinin'))field=card.querySelector('[data-field="data_source"]');else if(text.includes('hedefi'))field=card.querySelector('[data-field$="_target"]');field?.scrollIntoView({behavior:'smooth',block:'center'});field?.focus();field?.classList.add('field-attention');setTimeout(()=>field?.classList.remove('field-attention'),1600)}));

const submit=document.getElementById('submitDepartment');if(submit)submit.addEventListener('click',async()=>{const {r,j}=await jsonFetch(`/api/departments/${submit.dataset.department}/submit`,{method:'POST'});if(!r.ok){toast(j.message||j.detail||'Gönderim yapılamadı.');const first=j.problems&&Object.keys(j.problems)[0];if(first){const card=document.querySelector(`.record[data-id="${first}"]`);card?.scrollIntoView({behavior:'smooth',block:'center'});return}const firstActivity=j.activity_problems&&Object.keys(j.activity_problems)[0];if(firstActivity){document.querySelector('.tab[data-tab="activities"]')?.click();setTimeout(()=>{const row=document.querySelector(`tr[data-activity="${firstActivity}"]`);row?.scrollIntoView({behavior:'smooth',block:'center'});row?.querySelector('.activity-subprogram')?.classList.add('field-attention')},120)}return}toast('Paket Strateji Geliştirme incelemesine gönderildi.');setTimeout(()=>location.reload(),700)});

function setActivityEditMode(tr,editing){tr.classList.toggle('editing-row',editing);tr.querySelectorAll('input,textarea').forEach(i=>i.readOnly=!editing);const sub=tr.querySelector('.activity-subprogram');if(sub)sub.disabled=!editing;const edit=tr.querySelector('.edit-activity');const del=tr.querySelector('.delete-activity');if(edit){edit.textContent=editing?'Kaydet':'Düzenle';edit.classList.toggle('primary',editing)}if(del){del.textContent=editing?'Vazgeç':'Sil';del.dataset.mode=editing?'cancel':''}}
async function saveActivity(tr){const name=tr.querySelector('.activity-name');if(!name.value.trim()){name.focus();name.classList.add('field-attention');toast('Faaliyet adı boş bırakılamaz.');return}const sub=tr.querySelector('.activity-subprogram');if(!sub?.value){sub?.focus();sub?.classList.add('field-attention');toast('Program / Alt Program seçimi zorunlu.');return}const body={subprogram_id:sub.value,name:name.value,explanation:tr.querySelector('.activity-explanation')?.value||''};tr.querySelectorAll('.activity-cost').forEach(i=>body[`cost_${i.dataset.year}_${i.dataset.kind}`]=i.value);const {r,j}=await jsonFetch(`/api/activities/${tr.dataset.activity}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});if(!r.ok){toast(j.detail||'Faaliyet kaydedilemedi.');return}tr.querySelectorAll('.activity-cost').forEach(i=>i.value=trNumber(i.value,true));setActivityEditMode(tr,false);toast('Faaliyet güncellendi.');setTimeout(()=>location.reload(),450)}

document.addEventListener('click',async(e)=>{const edit=e.target.closest('.edit-activity');if(edit){const tr=edit.closest('tr');if(edit.textContent.trim()==='Düzenle'){setActivityEditMode(tr,true);tr.querySelector('.activity-name')?.focus()}else if(edit.textContent.trim()==='Kaydet'){await saveActivity(tr)}else if(edit.textContent.trim()==='Vazgeç'){location.reload()}return}const del=e.target.closest('.delete-activity');if(del){const tr=del.closest('tr');if(del.dataset.mode==='cancel'){location.reload();return}if(del.dataset.mode!=='confirm'){del.dataset.mode='confirm';del.textContent='Evet, sil';const editBtn=tr.querySelector('.edit-activity');if(editBtn){editBtn.textContent='Vazgeç';editBtn.classList.remove('primary')}toast('Silmek için “Evet, sil”e tekrar basın.');return}const {r,j}=await jsonFetch(`/api/activities/${tr.dataset.activity}`,{method:'DELETE'});if(!r.ok){toast(j.detail||'Faaliyet silinemedi.');return}tr.remove();toast('Faaliyet silindi.');setTimeout(()=>location.reload(),350);return}});

const add=document.getElementById('addActivity');if(add)add.addEventListener('click',()=>{if(document.querySelector('#activityBody tr[data-new="1"]')){document.querySelector('#activityBody tr[data-new="1"] .activity-name')?.focus();return}const proto=document.getElementById('subprogramPrototype');const columns=[...document.querySelectorAll('.cost-table thead th')].slice(2,-1);const tr=document.createElement('tr');tr.dataset.new='1';tr.className='new-activity-row editing-row';const costCells=columns.map(th=>{const label=th.textContent.trim();const m=label.match(/(20\d{2})/);let kind=label.includes('Haziran')?'midyear_spend':label.includes('Yıl Sonu')?'year_end_estimate':label.includes('Bütçe')?'budget':'forecast';return `<td><input class="money activity-cost" data-year="${m?m[1]:''}" data-kind="${kind}" placeholder="0,00"></td>`}).join('');tr.innerHTML=`<td><select class="activity-subprogram">${proto?proto.innerHTML:''}</select></td><td><input class="activity-name" placeholder="Faaliyet adı"><textarea class="activity-explanation" rows="2" placeholder="Faaliyet açıklaması"></textarea></td>${costCells}<td><div class="rowbuttons"><button class="button small primary save-new">Kaydet</button><button class="button small cancel-new">İptal</button></div></td>`;document.getElementById('activityBody').prepend(tr);tr.querySelector('.activity-name').focus();tr.scrollIntoView({behavior:'smooth',block:'center'});tr.querySelector('.cancel-new').addEventListener('click',()=>tr.remove());tr.querySelector('.save-new').addEventListener('click',async()=>{const name=tr.querySelector('.activity-name');if(!name.value.trim()){name.focus();toast('Faaliyet adı zorunlu.');return}const sub=tr.querySelector('.activity-subprogram');if(!sub?.value){sub?.focus();sub?.classList.add('field-attention');toast('Program / Alt Program seçimi zorunlu.');return}const body={subprogram_id:sub.value,name:name.value,explanation:tr.querySelector('.activity-explanation')?.value||''};tr.querySelectorAll('.activity-cost').forEach(i=>body[`cost_${i.dataset.year}_${i.dataset.kind}`]=i.value);const {r,j}=await jsonFetch('/api/activities',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});if(!r.ok){toast(j.detail||'Faaliyet eklenemedi.');return}toast('Faaliyet eklendi.');setTimeout(()=>location.reload(),500)})});

const savePersonnel=document.getElementById('savePersonnel');if(savePersonnel)savePersonnel.addEventListener('click',async()=>{const body={};document.querySelectorAll('.personnel-cost').forEach(i=>body[`cost_${i.dataset.year}_${i.dataset.kind}`]=i.value);const {r,j}=await jsonFetch(`/api/departments/${savePersonnel.dataset.department}/personnel-costs`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});if(!r.ok){toast(j.detail||'Personel ve SGK giderleri kaydedilemedi.');return}document.querySelectorAll('.personnel-cost').forEach(i=>i.value=trNumber(i.value,true));toast('Personel ve SGK giderleri kaydedildi.');setTimeout(()=>location.reload(),450)});

document.querySelectorAll('.money').forEach(i=>i.addEventListener('blur',()=>{if(!i.readOnly)i.value=trNumber(i.value,true)}));

let pendingReturn=null;document.querySelectorAll('.review-action').forEach(btn=>btn.addEventListener('click',async()=>{if(btn.dataset.decision==='return'){pendingReturn=btn.dataset.id;document.getElementById('reviewModal').hidden=false;document.getElementById('returnNote').focus();return}if(!window.confirm('Bu müdürlük paketi onaylanacak ve veri girişi kilitlenecek. Devam edilsin mi?'))return;await decide(btn.dataset.id,'approve','')}));async function decide(id,decision,note){const {r,j}=await jsonFetch(`/api/submissions/${id}/decision`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({decision,note})});if(!r.ok){toast(j.detail||'İşlem yapılamadı.');return}toast(decision==='approve'?'Müdürlük paketi onaylandı.':'Paket müdürlüğe iade edildi.');setTimeout(()=>location.reload(),600)}
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
  box.innerHTML=`<div class="cards import-cards"><div class="card"><span>Müdürlük</span><b>${s.department_count||0}</b></div><div class="card"><span>Gösterge</span><b>${s.indicator_count||0}</b></div><div class="card"><span>Faaliyet</span><b>${s.activity_count||0}</b></div><div class="card"><span>Word tablosu</span><b>${s.table_count||0}</b></div></div><div class="import-preview"><h4>İlk müdürlükler</h4>${(j.departments||[]).slice(0,12).map(d=>`<div class="import-dept"><b>${escapeHtml(d.name)}</b><span>${Number(d.indicator_count)||0} gösterge · ${Number(d.activity_count)||0} faaliyet · ${Number(d.block_count)||0} program bloğu</span></div>`).join('')||'<p>Veri bloğu bulunamadı.</p>'}</div>${mappingHtml}${j.warnings&&j.warnings.length?`<div class="issue-list">${j.warnings.slice(0,20).map(w=>`<div>${escapeHtml(w)}</div>`).join('')}</div>`:'<p class="ok-text">Yapısal eşleştirme uyarısı oluşmadı.</p>'}${linkWarning}${applyHtml}<p class="muted">Önizleme tek başına veritabanındaki performans kayıtlarını değiştirmez.</p>`;
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

const nub=document.getElementById('newUserBtn');if(nub)nub.addEventListener('click',()=>{document.getElementById('newUserForm').hidden=false;document.getElementById('userName').focus()});document.querySelectorAll('.create-department-user').forEach(button=>button.addEventListener('click',()=>{document.getElementById('newUserForm').hidden=false;document.getElementById('userRole').value='department';document.getElementById('departmentLabel').hidden=false;document.getElementById('userDepartment').value=button.dataset.createDepartment;document.getElementById('userName').focus();document.getElementById('newUserForm').scrollIntoView({behavior:'smooth',block:'center'})}));const cur=document.getElementById('cancelUser');if(cur)cur.addEventListener('click',()=>document.getElementById('newUserForm').hidden=true);const ur=document.getElementById('userRole');if(ur)ur.addEventListener('change',()=>document.getElementById('departmentLabel').hidden=ur.value==='strategy');const su=document.getElementById('saveUser');if(su)su.addEventListener('click',async()=>{const body={full_name:document.getElementById('userName').value,email:document.getElementById('userEmail').value,role:document.getElementById('userRole').value,department_id:document.getElementById('userDepartment').value,password:document.getElementById('userPassword').value};const {r,j}=await jsonFetch('/api/users',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});if(!r.ok){toast(j.detail||'Kullanıcı oluşturulamadı.');return}toast('Kullanıcı oluşturuldu.');setTimeout(()=>location.reload(),500)});
const bulkFile=document.getElementById('bulkUserFile'),bulkPreview=document.getElementById('previewBulkUsers'),bulkApply=document.getElementById('applyBulkUsers'),bulkResult=document.getElementById('bulkUserResult');let bulkPreviewedFile=null;const bulkForm=()=>{const form=new FormData();form.append('file',bulkFile.files[0]);return form};if(bulkFile)bulkFile.addEventListener('change',()=>{bulkPreviewedFile=null;bulkApply.disabled=true;bulkResult.textContent='Dosya değişti. Uygulamadan önce yeniden kontrol edin.'});if(bulkPreview)bulkPreview.addEventListener('click',async()=>{if(!bulkFile.files.length){toast('Önce CSV dosyasını seçin.');return}bulkPreview.disabled=true;bulkResult.textContent='Dosya kontrol ediliyor…';const {r,j}=await jsonFetch('/api/users/bulk-preview',{method:'POST',body:bulkForm()});bulkPreview.disabled=false;if(!r.ok){bulkResult.textContent=j.detail||'Dosya kontrol edilemedi.';return}if(!j.ok){bulkPreviewedFile=null;bulkApply.disabled=true;bulkResult.innerHTML='<b>Dosya uygulanamaz.</b><ul>'+j.errors.map(error=>'<li>'+escapeHtml(error)+'</li>').join('')+'</ul>';return}bulkPreviewedFile=bulkFile.files[0];bulkApply.disabled=false;bulkResult.innerHTML='<b class="ok">'+j.count+' hesap oluşturulmaya hazır.</b> Parolalar önizlemede gösterilmez veya kaydedilmez.'});if(bulkApply)bulkApply.addEventListener('click',async()=>{if(!bulkPreviewedFile||bulkFile.files[0]!==bulkPreviewedFile){toast('Dosyayı yeniden kontrol edin.');return}if(!confirm('Önizlemesi doğrulanan hesaplar oluşturulsun mu? Bu işlem canlı kullanıcı erişimi sağlar.'))return;bulkApply.disabled=true;bulkResult.textContent='Hesaplar oluşturuluyor…';const {r,j}=await jsonFetch('/api/users/bulk-import',{method:'POST',body:bulkForm()});if(!r.ok){const detail=j.detail;bulkResult.textContent=(detail&&detail.message)||detail||'Hesaplar oluşturulamadı.';bulkPreviewedFile=null;return}bulkResult.innerHTML='<b class="ok">'+j.created+' hesap oluşturuldu.</b> İşlem: '+escapeHtml(j.batch_id);toast('Toplu hesap oluşturma tamamlandı.');setTimeout(()=>location.reload(),700)});
document.querySelectorAll('.toggle-user-active').forEach(button=>button.addEventListener('click',async()=>{const active=button.dataset.active!=='1';if(!window.confirm(active?'Hesap etkinleştirilsin mi?':'Hesap devre dışı bırakılıp giriş erişimi kapatılsın mı?'))return;const {r,j}=await jsonFetch('/api/users/'+button.dataset.user+'/active',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({active})});if(!r.ok){toast(j.detail||'Hesap durumu değiştirilemedi.');return}toast(active?'Hesap etkinleştirildi.':'Hesap devre dışı bırakıldı.');setTimeout(()=>location.reload(),500)}));
document.querySelectorAll('.show-password-reset').forEach(button=>button.addEventListener('click',()=>{const box=document.querySelector('[data-reset-user="'+button.dataset.user+'"]');box.hidden=!box.hidden;if(!box.hidden)box.querySelector('input').focus()}));
document.querySelectorAll('.save-password-reset').forEach(button=>button.addEventListener('click',async()=>{const box=button.closest('.password-reset'),password=box.querySelector('input').value;const {r,j}=await jsonFetch('/api/users/'+box.dataset.resetUser+'/reset-password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password})});if(!r.ok){toast(j.detail||'Parola yenilenemedi.');return}box.querySelector('input').value='';box.hidden=true;toast('Geçici parola yenilendi.')})); 

// Strategy activity mapping queue: designed for high-volume Word imports.
(function(){
  const selects=[...document.querySelectorAll('.mapping-select')];
  if(!selects.length)return;
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
