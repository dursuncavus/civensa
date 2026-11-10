// CIV-206 · Kullanıcılar list: status / directorate / search filters and
// directorate groups, built in the browser so the frozen users markup stays.
(() => {
  const wrap = document.querySelector('.users-page .users-table');
  const tbody = wrap && wrap.querySelector('tbody');
  if (!tbody) return;
  const fold = t => (t || '').toLocaleLowerCase('tr-TR').replace(/\s+/g, ' ').trim();
  const rows = [...tbody.querySelectorAll('tr[data-user]')].map(tr => {
    const cells = tr.children;
    const dept = (cells[2] && cells[2].textContent.replace(/\s+/g, ' ').trim()) || '-';
    const status = tr.querySelector('.user-status-controls .status');
    return {
      tr,
      dept: dept === '-' ? 'Müdürlüğü yok' : dept,
      active: !!status && fold(status.textContent) === 'etkin',
      text: fold(tr.querySelector('.user-identity') ? tr.querySelector('.user-identity').textContent : ''),
    };
  });
  if (!rows.length) return;
  const cols = tbody.closest('table').querySelectorAll('thead th').length || 6;

  const bar = document.createElement('div');
  bar.className = 'users-filter';
  bar.innerHTML =
    '<label>Durum <select id="usersStatusFilter">' +
      '<option value="active">Etkin</option><option value="inactive">Pasif</option><option value="all">Tümü</option>' +
    '</select></label>' +
    '<label>Müdürlük <select id="usersDeptFilter"><option value="">Tüm müdürlükler</option></select></label>' +
    '<label class="users-filter-search">Ara <input id="usersSearch" type="search" placeholder="Ad veya e-posta" autocomplete="off"></label>' +
    '<p id="usersFilterCount" class="muted" aria-live="polite"></p>';
  // Above the policy panel: the panel's paragraph must stay right before the table.
  const panel = wrap.closest('.users-policy-table') || wrap;
  panel.parentNode.insertBefore(bar, panel);
  const statusSel = bar.querySelector('#usersStatusFilter');
  const deptSel = bar.querySelector('#usersDeptFilter');
  const search = bar.querySelector('#usersSearch');
  const count = bar.querySelector('#usersFilterCount');

  const names = [...new Set(rows.map(r => r.dept))].sort((a, b) => a.localeCompare(b, 'tr-TR'));
  names.forEach(name => {
    const o = document.createElement('option');
    o.value = name; o.textContent = name;
    deptSel.appendChild(o);
  });

  // Regroup rows under one header row per directorate, in name order.
  const groups = names.map(name => {
    const head = document.createElement('tr');
    head.className = 'user-group-row';
    const th = document.createElement('td');
    th.colSpan = cols;
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'user-group-toggle';
    th.appendChild(btn);
    head.appendChild(th);
    tbody.appendChild(head);
    const members = rows.filter(r => r.dept === name);
    members.forEach(r => tbody.appendChild(r.tr));
    const group = { name, head, btn, members, open: null };
    btn.addEventListener('click', () => { group.open = !isOpen(group); apply(); });
    return group;
  });

  let auto = true;
  function isOpen(g) { return g.open === null ? auto : g.open; }
  function matches(r) {
    const s = statusSel.value;
    if (s === 'active' && !r.active) return false;
    if (s === 'inactive' && r.active) return false;
    if (deptSel.value && r.dept !== deptSel.value) return false;
    const q = fold(search.value);
    return !q || r.text.includes(q);
  }
  function apply() {
    const visible = rows.filter(matches);
    // Few rows, a chosen directorate or a search: open every group by default.
    auto = visible.length <= 25 || !!deptSel.value || !!fold(search.value);
    let shown = 0;
    groups.forEach(g => {
      const hits = g.members.filter(matches);
      const open = isOpen(g);
      g.head.hidden = hits.length === 0;
      const act = hits.filter(r => r.active).length;
      const parts = [hits.length + ' hesap'];
      if (statusSel.value === 'all') parts.push(act + ' etkin, ' + (hits.length - act) + ' pasif');
      g.btn.textContent = (open ? '▾ ' : '▸ ') + g.name + ' · ' + parts.join(' · ');
      g.btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      g.members.forEach(r => {
        const on = hits.includes(r) && open;
        r.tr.hidden = !on;
        if (on) shown += 1;
      });
    });
    count.textContent = visible.length
      ? visible.length + ' hesap bulundu' + (shown < visible.length ? ', grupları açarak görün.' : '.')
      : 'Bu seçime uyan hesap yok.';
  }
  [statusSel, deptSel].forEach(el => el.addEventListener('change', () => { groups.forEach(g => { g.open = null; }); apply(); }));
  search.addEventListener('input', () => { groups.forEach(g => { g.open = null; }); apply(); });
  apply();

  // CIV-207 · "Sil" only on accounts nothing in the system refers to yet.
  if (typeof jsonFetch !== 'function') return;
  jsonFetch('/api/users/deletable').then(({ r, j }) => {
    if (!r.ok || !j || !Array.isArray(j.ids)) return;
    const ids = new Set(j.ids.map(String));
    rows.forEach(({ tr }) => {
      const id = tr.dataset.user;
      const buttons = tr.querySelector('.rowbuttons');
      if (!ids.has(id) || !buttons) return;
      const name = (tr.querySelector('.user-identity b') || {}).textContent || 'Bu';
      const del = document.createElement('button');
      del.type = 'button';
      del.className = 'button small danger delete-user';
      del.textContent = 'Sil';
      del.title = 'Bu hesabın sistemde hiç kaydı yok; kalıcı olarak silinebilir.';
      del.addEventListener('click', async () => {
        if (!window.confirm(name + ' hesabı kalıcı olarak silinsin mi? Bu işlem geri alınamaz.')) return;
        del.disabled = true;
        const res = await jsonFetch('/api/users/' + id + '/delete', { method: 'POST' });
        if (!res.r.ok) { del.disabled = false; toast(res.j.detail || 'Hesap silinemedi.'); return; }
        toast('Hesap silindi.');
        setTimeout(() => location.reload(), 500);
      });
      buttons.appendChild(del);
    });
  });
})();
