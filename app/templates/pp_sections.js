
const renderPPImport = renderImportReport;
renderImportReport = function(result) {
  const generalTables=new Set((result.general_sections||[]).filter(s=>s.kind==='table').map(s=>s.content.source?.table_number));
  renderPPImport({...result, coverage_items:(result.coverage_items||[]).filter(item=>!generalTables.has(item.table_number))});
  if (!result.general_sections?.length) return;
  const content=document.createElement('div');
  const heading=document.createElement('h3'); heading.textContent='Genel Kitap Bölümleri'; content.append(heading);
  for (const section of result.general_sections) {
    const line=document.createElement('p');
    line.textContent=section.title+' · '+({create:'Eklenecek',keep:'Mevcut bölüm korunacak',conflict:'Çakışma — hedef bölüm korunacak'}[section.action]);
    content.append(line);
  }
  for (const warning of result.general_section_warnings||[]) {
    const line=document.createElement('p'); line.className='bad'; line.textContent=warning; content.append(line);
  }
  const link=document.createElement('a'); link.href=result.section_preview_url; link.textContent='Genel Bölüm İçeriklerini İncele'; content.append(link);
  document.getElementById('importResult').prepend(content);
};

for (const [id, action] of [['applySections','apply'],['revertSections','revert']]) {
  const button=document.getElementById(id);
  button?.addEventListener('click', async () => {
    button.disabled = true;
    const {r,j} = await jsonFetch('/api/import-batches/'+button.dataset.batchId+'/'+action, {method:'POST'});
    if (!r.ok) {button.disabled=false; toast(j.detail || 'İçe aktarma işlenemedi. Sayfayı yenileyip paket durumunu kontrol edin.'); return;}
    location.href='/report-builder/manifest?period_id='+button.dataset.periodId;
  });
}
const openSection = () => {
  const section=document.getElementById(location.hash.slice(1));
  if (section?.tagName === 'DETAILS') section.open=true;
};
openSection(); window.addEventListener('hashchange',openSection);
