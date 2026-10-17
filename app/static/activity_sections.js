(() => {
  const form = document.querySelector('[data-ar-section-form]');
  if (form) {
    const input = form.querySelector('[name=text]');
    const preview = document.querySelector('[data-ar-preview]');
    const render = () => {
      preview.replaceChildren();
      let list = null, table = null;
      for (const line of input.value.split('\n')) {
        if (line.startsWith('- ')) {
          table = null;
          if (!list) { list = document.createElement('ul'); preview.append(list); }
          const item = document.createElement('li'); item.textContent = line.slice(2); list.append(item);
        } else if (line.startsWith('|') && line.endsWith('|')) {
          list = null;
          if (!table) { table = document.createElement('table'); table.className = 'ar-table'; preview.append(table); }
          const row = table.insertRow();
          for (const text of line.slice(1, -1).split('|')) row.insertCell().textContent = text.trim();
        } else {
          list = null; table = null;
          const p = document.createElement('p'); p.textContent = line; preview.append(p);
        }
      }
    };
    input.addEventListener('input', render); render();
  }
  document.querySelectorAll('[data-ar-add-row]').forEach(button => {
    button.addEventListener('click', () => {
      const body = button.closest('form').querySelector('tbody');
      const count = body.rows.length;
      if (count >= 2000) { button.disabled = true; return; }
      const row = body.rows[count - 1].cloneNode(true);
      row.querySelectorAll('input,select').forEach(input => {
        input.name = input.name.replace(/_\d+$/, `_${count}`);
        if (input.type === 'checkbox') input.checked = false;
        else input.value = '';
        input.setAttribute('aria-label', (input.getAttribute('aria-label') || '').replace(/\d+/, String(count + 1)));
      });
      body.append(row);
    });
  });
  const dirtyForms = new Set();
  document.querySelectorAll('[data-ar-section-form], [data-ar-resource-form]').forEach(form => {
    form.addEventListener('input', () => { dirtyForms.add(form); });
    form.addEventListener('submit', event => {
      if (event.submitter && [...dirtyForms].some(other => other !== form) && !window.confirm('Bu form kaydedilecek. Diğer formlardaki kaydedilmemiş değişiklikler kaybolabilir. Devam edilsin mi?')) {
        event.preventDefault(); return;
      }
      dirtyForms.clear();
    });
  });
  window.addEventListener('beforeunload', event => {
    if (dirtyForms.size) { event.preventDefault(); event.returnValue = ''; }
  });
})();
