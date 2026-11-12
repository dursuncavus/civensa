/* Directorate guide table interactions. All authoritative checks run on server. */
(() => {
  const parse = value => {
    const text = value.trim();
    if (!text) return null;
    if (!/^(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d{1,2})?$/.test(text)) return null;
    return Math.round(Number(text.replaceAll('.', '').replace(',', '.')) * 100);
  };
  const display = value => value === null ? '—' : (value / 100).toLocaleString('tr-TR', {maximumFractionDigits: 2});
  document.querySelectorAll('[data-unit-table]').forEach(form => {
    const update = () => {
      const totals = {};
      let mismatch = false;
      form.querySelectorAll('[data-unit-rows] tr').forEach(row => {
        const included = row.querySelector('[name^=include_]');
        if (included && !included.checked) return;
        const values = {};
        row.querySelectorAll('input.unit-number').forEach(input => {
          const key = input.name.replace(/_\d+$/, '');
          const value = parse(input.value);
          values[key] = value;
          if (value !== null) totals[key] = (totals[key] ?? 0) + value;
        });
        const output = row.querySelector('[data-total]');
        if (output) {
          const total = values.inside != null && values.outside != null ? values.inside + values.outside : null;
          output.textContent = display(total);
          if (total !== null) totals.total = (totals.total ?? 0) + total;
        }
        if (form.dataset.unitTable === '2') {
          const wrong = ['women', 'men', 'actual'].every(k => values[k] != null) && values.women + values.men !== values.actual;
          row.querySelector('[name^=actual_]').setAttribute('aria-invalid', String(wrong));
          mismatch ||= wrong;
        }
      });
      form.querySelectorAll('[data-column-total]').forEach(output => { output.textContent = display(totals[output.dataset.columnTotal] ?? null); });
      const warning = form.querySelector('[data-staff-warning]');
      if (warning) warning.textContent = mismatch ? 'Kadın + Erkek = Fiili Çalışan olmalıdır. Tutarsızlık gönderimi engeller; personel sayılarını düzeltin.' : 'Kadın + Erkek = Fiili Çalışan olmalıdır. Taslak kaydedilebilir; tutarsızlık gönderimi engeller.';
    };
    form.addEventListener('input', update);
    form.querySelector('[data-unit-add]')?.addEventListener('click', () => {
      const counter = form.elements.namedItem('row_count');
      const index = Number(counter.value);
      if (index >= 2000) return;
      const last = form.querySelector('[data-unit-rows] tr:last-child');
      if (!last) return;
      const copy = last.cloneNode(true);
      copy.id = copy.id.replace(/row-\d+$/, `row-${index}`);
      copy.querySelectorAll('input, select, textarea').forEach(input => {
        input.name = input.name.replace(/_\d+$/, `_${index}`);
        if (input.id) input.id = input.id.replace(/row-\d+-/, `row-${index}-`);
        if (input.hasAttribute('aria-label')) input.setAttribute('aria-label', input.getAttribute('aria-label').replace(/\d+/, String(index + 1)));
        if (input.type === 'checkbox') input.checked = false; else input.value = '';
      });
      form.querySelector('[data-unit-rows]').append(copy);
      counter.value = index + 1;
      copy.querySelector('input').focus();
    });
    update();
  });
})();
