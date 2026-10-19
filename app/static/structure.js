(() => {
  const profileForm = document.querySelector('[data-profile-form]');
  if (profileForm) {
    const select = profileForm.elements.department_id;
    function fillProfile() {
      const values = JSON.parse(select.dataset.profiles || '{}')[select.value] || {};
      for (const name of ['display_name', 'budget_code', 'active_from', 'active_to', 'status', 'reason']) {
        profileForm.elements[name].value = values[name] || (name === 'status' ? 'required' : '');
      }
    }
    select.addEventListener('change', fillProfile);
    if (profileForm.dataset.attempted !== '1') fillProfile();
  }
  const form = document.getElementById('structure-wizard');
  if (!form) return;
  const steps = [...form.querySelectorAll('[data-structure-step]')];
  const previous = document.getElementById('structure-previous');
  const next = document.getElementById('structure-next');
  const kind = document.getElementById('structure-kind');
  let step = 0;
  const selected = name => [...form.querySelectorAll(`input[name="${name}"]:checked:not(:disabled)`)];
  function update() {
    const type = kind.value;
    const transfer = ['MERGED', 'SPLIT', 'CLOSED'].includes(type);
    for (const [selector, visible] of [['[data-old-departments]', type !== 'CREATED'], ['[data-rename]', type === 'RENAMED'], ['[data-receivers]', transfer], ['[data-new-departments]', type !== 'RENAMED']]) {
      const group = form.querySelector(selector);
      group.hidden = !visible;
      group.querySelectorAll('input,textarea').forEach(input => { input.disabled = !visible; });
    }
    const newNames = form.elements.new_names.value.split('\n').map(s => s.trim()).filter(Boolean);
    const targets = selected('to_department_ids').map(input => [input.value, input.dataset.name]).concat(newNames.map((name, index) => [`new:${index}`, name]));
    const sources = selected('from_department_ids').map(input => input.value);
    form.querySelectorAll('[data-transfer-source]').forEach(row => {
      const active = transfer && sources.includes(row.dataset.transferSource);
      row.hidden = !active;
      const select = row.querySelector('select');
      select.disabled = !active;
      const value = select.value || select.dataset.attempted;
      select.replaceChildren(new Option('Aktarılmadı', ''), ...targets.map(([id, name]) => new Option(name, id)));
      if (targets.some(([id]) => id === value)) select.value = value;
    });
    form.querySelector('[data-no-transfers]').hidden = transfer;
    steps.forEach((fieldset, index) => { fieldset.hidden = index !== step; });
    previous.hidden = step === 0; next.hidden = step === steps.length - 1;
    document.getElementById('structure-step-label').textContent = `${step + 1} / 6 · ${steps[step].querySelector('legend').textContent.replace(/^\d+ · /, '')}`;
    if (step === 5) {
      const summary = document.getElementById('structure-summary');
      summary.replaceChildren();
      const lines = [`${kind.selectedOptions[0].textContent} · ${form.elements.effective_date.value}`, `Meclis: ${form.elements.council_decision_no.value} · ${form.elements.council_decision_date.value}`, `Eski müdürlükler: ${selected('from_department_ids').map(input => input.parentElement.textContent.trim()).join(', ') || 'Yok'}`, `Yeni ad / devralanlar: ${type === 'RENAMED' ? form.elements.new_name.value : targets.map(([, name]) => name).join(', ') || 'Yok'}`];
      const rows = [...form.querySelectorAll('[data-transfer-select]')].filter(input => !input.disabled);
      lines.push(`Aktarılan işler: ${rows.filter(input => input.value).length} · Aktarılmayan işler: ${rows.filter(input => !input.value).length}`);
      for (const input of rows) lines.push(`${input.closest('tr').firstElementChild.innerText.replaceAll('\n', ' · ')} → ${input.selectedOptions[0].textContent}`);
      lines.forEach(line => { const p = document.createElement('p'); p.textContent = line; summary.append(p); });
    }
  }
  next.addEventListener('click', () => {
    const invalid = [...steps[step].querySelectorAll('input,select,textarea')].find(input => !input.disabled && !input.checkValidity());
    if (invalid) { invalid.reportValidity(); return; }
    step = Math.min(steps.length - 1, step + 1); update();
  });
  previous.addEventListener('click', () => { step = Math.max(0, step - 1); update(); });
  kind.addEventListener('change', update);
  form.querySelectorAll('input[type=checkbox], #structure-new-names').forEach(input => input.addEventListener('change', update));
  form.addEventListener('submit', event => { if (step !== steps.length - 1) { event.preventDefault(); next.click(); } });
  update();
})();
