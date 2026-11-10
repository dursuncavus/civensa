// CIV-210 · İnceleme kuyruğu at a glance: packages waiting for Strateji first,
// a one-line count, and "not sent yet" instead of "old record" for drafts.
// Browser-only so the frozen 042 review markup stays.
(() => {
  const page = document.querySelector('.review-page');
  const tbody = page && page.querySelector('.review-panel tbody');
  if (!tbody) return;
  const ORDER = ['submitted', 'returned', 'draft', 'approved'];
  const LABEL = { submitted: 'incelemenizi bekliyor', returned: 'iade edildi', draft: 'henüz gönderilmedi', approved: 'onaylandı' };
  const rows = [...tbody.querySelectorAll(':scope > tr')].map((tr, index) => {
    const status = tr.querySelector('.status');
    const kind = status ? ORDER.find(name => status.classList.contains(name)) || 'other' : 'other';
    return { tr, index, kind };
  });
  rows.forEach(({ tr, kind }) => {
    if (kind !== 'draft') return;
    const muted = tr.querySelector('td:nth-child(3) .muted');
    if (muted && muted.textContent.trim() === 'Eski kayıt · geçmiş yok') muted.textContent = 'Henüz gönderilmedi';
  });
  const rank = kind => { const i = ORDER.indexOf(kind); return i < 0 ? ORDER.length : i; };
  rows.slice().sort((a, b) => rank(a.kind) - rank(b.kind) || a.index - b.index).forEach(({ tr }) => tbody.appendChild(tr));
  const count = kind => rows.filter(r => r.kind === kind).length;
  const summary = document.createElement('p');
  summary.className = 'review-summary';
  summary.setAttribute('role', 'status');
  const waiting = count('submitted');
  const head = document.createElement('b');
  head.textContent = waiting ? 'İncelemenizi bekleyen ' + waiting + ' paket var; listenin başında.' : 'İncelemenizi bekleyen paket yok.';
  const rest = document.createElement('span');
  rest.textContent = ORDER.filter(kind => kind !== 'submitted' && count(kind)).map(kind => count(kind) + ' müdürlük ' + LABEL[kind]).join(' · ');
  summary.append(head, rest);
  page.querySelector('.review-panel').before(summary);
})();
