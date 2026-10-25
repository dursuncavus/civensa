/* CIV-099 presentation only: no requests and no changes to stored data. */
(() => {
  const page = document.querySelector('.section-editor-page');
  if (!page) return;
  page.addEventListener('keydown', event => {
    if (event.key !== 'Escape') return;
    const disclosure = event.target.closest('details[open]');
    if (!disclosure) return;
    disclosure.open = false;
    disclosure.querySelector('summary').focus();
    event.preventDefault();
    event.stopPropagation();
  });
  page.querySelectorAll('[data-section-export]').forEach(menu => {
    document.addEventListener('click', event => {
      if (!menu.contains(event.target)) menu.open = false;
    });
  });
  const statuses = {empty: 'Boş', draft: 'Taslak', ready: 'Hazır', not_applicable: 'Uygulanamaz'};
  const equal = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  page.querySelectorAll('[data-section-audit]').forEach(entry => {
    const summary = entry.querySelector('[data-section-change]');
    const lines = [];
    try {
      const raw = entry.querySelectorAll('pre');
      const before = JSON.parse(raw[0].textContent) || {};
      const after = JSON.parse(raw[1].textContent) || {};
      if (before.status !== after.status && statuses[before.status] && statuses[after.status]) {
        lines.push(`Durum: ${statuses[before.status]} → ${statuses[after.status]}`);
      }
      if (Array.isArray(before.blocks) && Array.isArray(after.blocks) && !equal(before.blocks, after.blocks)) {
        // Count additions only when the old blocks remain an exact prefix.
        const added = after.blocks.slice(before.blocks.length);
        const prefix = equal(before.blocks, after.blocks.slice(0, before.blocks.length));
        if (prefix && added.length && added.every(block => block.type === 'paragraph')) {
          lines.push(`İçerik: ${added.length} paragraf eklendi`);
        } else if (after.blocks.length === 0) {
          lines.push('İçerik temizlendi.');
        } else {
          lines.push('İçerik güncellendi.');
        }
      }
      if (typeof before.reason === 'string' && typeof after.reason === 'string' && before.reason !== after.reason) {
        lines.push(after.reason ? 'Uygulanamaz gerekçesi güncellendi.' : 'Uygulanamaz gerekçesi temizlendi.');
      }
      if (Array.isArray(before.rows) && Array.isArray(after.rows) && !equal(before.rows, after.rows)) {
        lines.push('Tablo satırları güncellendi.');
      }
    } catch (_) {
      // Old/unrecognized payloads keep a truthful Turkish fallback; raw data stays closed.
    }
    if (!lines.length) lines.push('Kayıt ayrıntılarını Teknik ayrıntı bölümünde inceleyebilirsiniz.');
    summary.replaceChildren(...lines.map(line => {
      const p = document.createElement('p'); p.textContent = line; return p;
    }));
  });
})();
