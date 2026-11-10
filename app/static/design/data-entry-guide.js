// CIV-210 · Veri Girişi at a glance: plain badges, a "what is left" summary,
// a grouped submit-error list and a clear note for staff who cannot submit.
// Built in the browser so the frozen department markup (CIV-024/114) stays.
(() => {
  const page = document.querySelector('.data-entry-page');
  if (!page) return;
  const css = document.createElement('link');
  css.rel = 'stylesheet';
  css.href = '/static/design/data-entry-guide.css';
  document.head.append(css);
  const pane = page.querySelector('#indicators');
  const cards = () => [...page.querySelectorAll('#indicators article.record')];
  const issuesOf = card => card.querySelectorAll('.issue-list .issue-jump').length;

  function badges() {
    cards().forEach(card => {
      const badge = card.querySelector('.record-head .badge');
      const n = issuesOf(card);
      const label = n ? n + ' düzeltme' : 'Sorun yok';
      if (badge && badge.textContent !== label) badge.textContent = label;
    });
  }

  function jumpTo(card) {
    if (!card) return;
    card.scrollIntoView({ behavior: 'smooth', block: 'start' });
    const first = card.querySelector('.issue-jump') || card.querySelector('input, textarea');
    if (first) first.focus({ preventScroll: true });
  }

  // Summary above the indicator cards, only where the user can still edit.
  let summary = null;
  if (pane && !page.classList.contains('is-readonly') && cards().length) {
    summary = document.createElement('div');
    summary.className = 'entry-summary';
    summary.setAttribute('role', 'status');
    const text = document.createElement('p');
    const go = document.createElement('button');
    go.type = 'button';
    go.className = 'button small entry-summary-jump';
    go.textContent = 'İlk düzeltmeye git';
    go.addEventListener('click', () => jumpTo(page.querySelector('#indicators article.record.has-issue')));
    summary.append(text, go);
    pane.insertBefore(summary, pane.firstElementChild);
  }
  function refresh() {
    badges();
    if (!summary) return;
    const all = cards();
    const open = all.filter(card => card.classList.contains('has-issue'));
    const [text, go] = summary.children;
    let line;
    if (open.length) {
      const total = open.reduce((sum, card) => sum + issuesOf(card), 0);
      line = all.length + ' göstergeden ' + open.length + ' tanesinde düzeltme gerekli (' + total + ' madde). '
        + 'Kırmızı maddeye tıklayınca ilgili kutuya gidersiniz; düzeltip “Kaydet ve Kontrol Et”e basın.';
    } else {
      line = all.length + ' göstergenin hepsi kontrolden geçti. Faaliyet Maliyetleri sekmesine de bakıp paketi gönderin.';
    }
    // Only write on change: the observer below watches this same subtree.
    if (text.textContent !== line) text.textContent = line;
    if (go.hidden !== !open.length) go.hidden = !open.length;
    if (summary.classList.contains('is-clean') !== !open.length) summary.classList.toggle('is-clean', !open.length);
  }
  refresh();
  if (pane) new MutationObserver(refresh).observe(pane, { subtree: true, childList: true, attributes: true, attributeFilter: ['class'] });

  // Staff without submit permission: say who sends the package instead of a button that fails.
  const bar = page.querySelector('.submit-bar');
  const submit = bar && bar.querySelector('#submitDepartment');
  if (submit && document.querySelector('meta[name="pp-can-submit"][content="0"]')) {
    submit.hidden = true;
    const note = bar.querySelector('div span');
    if (note) note.textContent = 'Paketi Müdürünüz gönderir. Siz verileri girip kaydedin; tamamlandığında Müdürünüze haber verin. '
      + 'Gönderim yetkisini Müdürünüz Gönderim Yetkileri ekranından verebilir.';
    bar.classList.add('submit-bar-staff');
  }

  // Grouped submit errors: where each item is fixed, and who fixes it.
  window.civSubmitErrors = (anchor, messages) => {
    page.querySelectorAll('.submit-errors').forEach(node => node.remove());
    const indicatorNames = cards().map(card => ({ card, name: (card.querySelector('h3') || {}).textContent || '' }));
    const activityNames = [...page.querySelectorAll('.activity-name')].map(input => input.value.trim()).filter(Boolean);
    const startsWith = (msg, name) => name && msg.startsWith(name + ':');
    const groups = {
      indicators: { title: 'Performans göstergeleri', items: [], first: null },
      strategy: { title: 'Strateji biriminin tamamlayacağı eşleştirmeler', items: [] },
      activities: { title: 'Faaliyet maliyetleri', items: [] },
      program: { title: 'Performans kartları ve ekonomik tablolar', items: [] },
    };
    messages.forEach(msg => {
      const hit = indicatorNames.find(({ name }) => startsWith(msg, name.trim()));
      if (hit) { groups.indicators.items.push(msg); groups.indicators.first = groups.indicators.first || hit.card; return; }
      if (/kataloğu bağlantısı|katalog kapsamı|kart bağlantısı eksik|kart ve alt program kapsamı/.test(msg)) { groups.strategy.items.push(msg); return; }
      if (activityNames.some(name => startsWith(msg, name))) { groups.activities.items.push(msg); return; }
      groups.program.items.push(msg);
    });
    const box = document.createElement('div');
    box.className = 'return-note submit-errors';
    box.setAttribute('role', 'alert');
    box.tabIndex = -1;
    const head = document.createElement('b');
    head.textContent = 'Paket gönderilemedi: ' + messages.length + ' eksik var.';
    const lead = document.createElement('p');
    lead.textContent = 'Eksikler aşağıda yerlerine göre ayrıldı. Her grubu açıp düzeltin, sonra yeniden gönderin.';
    box.append(head, lead);
    const programLink = page.querySelector('.page-actions a');
    Object.entries(groups).forEach(([key, group]) => {
      if (!group.items.length) return;
      const details = document.createElement('details');
      details.className = 'submit-error-group';
      const sum = document.createElement('summary');
      sum.textContent = group.title + ' · ' + group.items.length + ' eksik';
      details.append(sum);
      if (key === 'strategy') {
        const hint = document.createElement('p');
        hint.className = 'smallnote';
        hint.textContent = 'Bu maddeleri müdürlük düzeltemez; Strateji birimine haber verin.';
        details.append(hint);
      }
      let action = null;
      if (key === 'indicators') {
        action = document.createElement('button');
        action.type = 'button';
        action.textContent = 'İlk göstergeye git';
        action.addEventListener('click', () => { page.querySelector('.tab[data-tab="indicators"]')?.click(); jumpTo(group.first); });
      } else if (key === 'activities') {
        action = document.createElement('button');
        action.type = 'button';
        action.textContent = 'Faaliyet Maliyetleri sekmesini aç';
        action.addEventListener('click', () => { const tab = page.querySelector('.tab[data-tab="activities"]'); tab?.click(); tab?.scrollIntoView({ behavior: 'smooth', block: 'start' }); });
      } else if (key === 'program' && programLink) {
        action = document.createElement('a');
        action.href = programLink.getAttribute('href');
        action.textContent = 'Performans Kartları ve Ekonomik Tablolar sayfasını aç';
      }
      if (action) { action.className = 'button small'; details.append(action); }
      const list = document.createElement('ul');
      group.items.forEach(msg => { const li = document.createElement('li'); li.textContent = msg; list.append(li); });
      details.append(list);
      box.append(details);
    });
    const only = box.querySelectorAll('details');
    if (only.length === 1) only[0].open = true;
    (anchor.closest('.submit-bar') || anchor).after(box);
    box.scrollIntoView({ behavior: 'smooth', block: 'center' });
    box.focus({ preventScroll: true });
  };
})();
