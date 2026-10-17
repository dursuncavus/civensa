(() => {
  const $ = id => document.getElementById(id);
  const names = {mayor_instruction:'Başkanlık talimatı', council_decision:'Meclis kararı', executive_decision:'Encümen kararı', mayor_approval:'Başkan onayı'};
  const error = message => { $('budget-error').hidden = false; $('budget-error').textContent = message; $('budget-error').scrollIntoView({block:'center'}); };
  const node = (tag, text) => { const el = document.createElement(tag); if (text !== undefined) el.textContent = text; return el; };
  // Format canonical decimal strings without converting money to binary floats.
  const money = value => { if (value === null) return 'Eksik veri'; const [whole, fraction = ''] = String(value).split('.'); return whole.replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ',' + fraction.padEnd(2, '0'); };
  const canonical = value => { const raw = value.trim(); if (!/^(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d+)?$/.test(raw)) throw Error('Tutar / oran geçersiz. Türkçe biçimde girin: 5.000.000,00 veya 3.'); return raw.replaceAll('.', '').replace(',', '.'); };
  async function post(path, data) {
    const response = await fetch(path, {method:'POST', headers:{'Content-Type':'application/json', 'X-CSRF-Token':document.querySelector('meta[name="csrf-token"]').content}, body:JSON.stringify(data)});
    const body = await response.json();
    if (!response.ok) throw Error(typeof body.detail === 'string' ? body.detail : 'İşlem tamamlanamadı. Alanları kontrol edip yeniden deneyin.');
    return body;
  }
  let current = null;
  const countDepartments = () => $('reversal-section') ? Number($('reversal-section').dataset.departments) : new Set([...document.querySelectorAll('.leg .department')].map(x => x.value)).size;
  function updateReference() {
    const type = $('phase').value === 'before_adoption' ? 'mayor_instruction' : countDepartments() > 1 ? 'council_decision' : $('transfer-scope').value === 'functional_classes' ? 'executive_decision' : 'mayor_approval';
    $('reference-type').value = type; $('reference-label').value = names[type];
    $('transfer-scope').disabled = countDepartments() > 1 || $('phase').value === 'before_adoption';
  }
  function reference() {
    updateReference();
    if (!$('reference-date').value || !$('reference-number').value.trim() || !$('reason').value.trim()) throw Error('Dayanak tarihi, sayısı ve gerekçe zorunlu. Eksik alanları tamamlayın.');
    return {phase:$('phase').value, transfer_scope:$('transfer-scope').value, reference_type:$('reference-type').value, reference_date:$('reference-date').value, reference_number:$('reference-number').value.trim(), reason:$('reason').value.trim()};
  }
  function invalidate() { current = null; if ($('reference-section')) $('reference-section').hidden = true; if ($('preview-result')) $('preview-result').textContent = 'Güncel önizleme için seçimlerle yeniden hesaplayın.'; }
  function request() {
    return {period_id:Number($('period').value), year:Number($('year').value), value_kind:$('value-kind').value,
      change_total:$('change-total').checked, change_outside:$('change-outside').checked,
      legs:[...document.querySelectorAll('.leg')].map((row, index) => {
        const leg = {department_id:Number(row.querySelector('.department').value), direction:row.querySelector('.direction').value};
        leg[row.querySelector('.input-mode').value] = canonical(row.querySelector('.leg-amount').value);
        const choices = document.querySelector(`[data-choice-leg="${index}"]`);
        if (choices && choices.dataset.department === String(leg.department_id)) {
          leg.excluded_categories = [...choices.querySelectorAll('.category-choice:not(:checked)')].map(x => x.value);
          leg.excluded_activities = [...choices.querySelectorAll('.activity-choice:not(:checked)')].map(x => Number(x.value));
        }
        return leg;
      })};
  }
  function renderChoices(choices, req) {
    $('eligible-choices').replaceChildren();
    choices.forEach(choice => {
      const group = node('details'); group.dataset.choiceLeg = choice.index; group.dataset.department = req.legs[choice.index].department_id;
      group.append(node('summary', choice.name + ' · Uygun kayıtları seç'));
      [['categories','Ekonomik kategoriler','category-choice','excluded_categories'],['activities','Faaliyetler','activity-choice','excluded_activities']].forEach(([key,label,cls,excluded]) => {
        group.append(node('h3',label));
        choice[key].forEach(item => { const lbl = node('label'); const check = node('input'); check.type = 'checkbox'; check.className = cls; check.value = item.id; check.checked = !(req.legs[choice.index][excluded] || []).includes(item.id); check.addEventListener('change', invalidate); lbl.append(check, document.createTextNode(' '+item.name+' ')); group.append(lbl); });
      }); $('eligible-choices').append(group);
    });
  }
  function renderPreview(data) {
    const root = $('preview-result'); root.replaceChildren();
    data.summaries.forEach(s => { const card = node('div'); card.append(node('h3',s.name), node('p',`Bütçe içi: ${money(s.before)} → ${money(s.after)} TL · Değişim: ${money(s.change)} TL (%${String(s.percent).replace('.', ',')})`), node('p',`Hesaplanan tutar: ${money(s.amount)} TL · Bütçe dışı değişim: ${money(s.outside_change)} TL`), node('p',`Ekonomik / faaliyet toplamları arasındaki mevcut fark: ${money(s.source_difference)} TL — fark korunur.`)); root.append(card); });
    if (data.department_results.length < data.summaries.length) data.department_results.forEach(s => root.append(node('p', `${s.name} — işlem sonunda: ${money(s.after)} TL · Net değişim: ${money(s.change)} TL (%${s.percent.replace('.', ',')})`)));
    data.warnings.forEach(w => root.append(node('p',w)));
    const wrap = node('div'); wrap.className = 'table-wrap'; const table = node('table'); const head = node('tr'); ['Müdürlük','Kayıt','Kaynak','Önce (TL)','Değişim (TL)','Sonra (TL)'].forEach(x => head.append(node('th',x))); const thead = node('thead'); thead.append(head); table.append(thead); const tbody = node('tbody');
    data.lines.forEach(line => { const tr = node('tr'); const dep = data.summaries.find(s => s.department_id === line.department_id); [dep.name, (line.value_table==='economic_values' ? 'Ekonomik · ' : 'Faaliyet · ')+line.label, {inside:'Bütçe içi',outside:'Bütçe dışı',total:'Toplam'}[line.funding_type], money(line.before), money(line.change), money(line.after)].forEach(x => tr.append(node('td',x))); tbody.append(tr); });
    table.append(tbody); wrap.append(table); root.append(wrap);
  }
  async function preview() {
    invalidate(); $('budget-error').hidden = true;
    try { const req = request(); const eligible = await post('/api/budget-reallocations/choices', req); renderChoices(eligible.choices,req); $('preview-section').hidden = false; const data = await post('/api/budget-reallocations/preview', req); current = data; renderChoices(data.choices,req); renderPreview(data); $('preview-section').hidden = false; $('preview-section').scrollIntoView(); }
    catch (e) { error(e.message); }
  }
  if ($('legs')) {
    function addLeg() { $('legs').append($('leg-template').content.cloneNode(true)); invalidate(); }
    addLeg(); addLeg(); document.querySelectorAll('.direction')[1].value = 'increase';
    $('add-leg').onclick = addLeg;
    $('legs').addEventListener('click', event => { if(event.target.closest('.remove-leg')) { event.target.closest('.leg').remove(); $('eligible-choices').replaceChildren(); invalidate(); } });
    $('legs').addEventListener('input', invalidate);
    ['period','year','value-kind','change-total','change-outside'].forEach(id => $(id).addEventListener('change', invalidate));
    $('period').addEventListener('change', () => { $('year').value = $('period').selectedOptions[0].dataset.year; $('eligible-choices').replaceChildren(); });
    $('preview-button').onclick = preview; $('refresh-preview').onclick = preview;
    $('continue-reference').onclick = () => { if (!current) { error('Seçimler değişti. Önce “Seçimlerle yeniden hesapla” düğmesine basın.'); return; } updateReference(); $('reference-section').hidden = false; $('reference-section').scrollIntoView(); };
    $('apply-button').onclick = async () => { const button = $('apply-button'); button.disabled = true; try { if (!current) throw Error('Önizleme güncel değil. Yeniden hesaplayın.'); const result = await post('/api/budget-reallocations/apply', {token:current.token,...reference()}); location.href = `/budget-reallocations/${result.id}`; } catch(e) { error(e.message); } finally { button.disabled = false; } };
  }
  if ($('reverse-button')) $('reverse-button').onclick = async () => { const button = $('reverse-button'); button.disabled = true; try { const result = await post(`/api/budget-reallocations/${$('reversal-section').dataset.operation}/reverse`, reference()); location.href = `/budget-reallocations/${result.id}`; } catch(e) { error(e.message); } finally { button.disabled = false; } };
  if ($('phase')) { $('phase').onchange = updateReference; $('transfer-scope').onchange = updateReference; updateReference(); }
})();
