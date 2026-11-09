/* Page-local native dialogs; deliberately independent of data-open-dialog. */
(() => {
  const page = document.querySelector('[data-program-page]');
  if (!page) return;
  const storageKey = `program-save:${page.dataset.programPage}`;
  const forms = [...page.querySelectorAll('form[method="post"]:not([data-draft-removal])')];
  const identity = form => [new URL(form.action).pathname,
    ...['id', 'kind', 'record_id', 'activity_id'].map(name => form.elements.namedItem(name)?.value || '')].join(':');
  const values = form => JSON.stringify([...new FormData(form)].filter(([name]) => name !== 'csrf_token'));
  const initial = new Map();
  const saving = new Set();
  const buttons = form => [...form.querySelectorAll('button:not([type]), button[type="submit"], input[type="submit"]')];
  const update = form => {
    const unchanged = initial.get(form) === values(form);
    buttons(form).forEach(button => { button.disabled = saving.has(form) || unchanged; });
  };
  forms.forEach((form, index) => {
    if (!form.getAttribute('id')) form.setAttribute('id', `program-form-${index}`);
    initial.set(form, values(form));
    update(form);
    ['input', 'change'].forEach(event => form.addEventListener(event, () => update(form)));
    form.addEventListener('reset', () => setTimeout(() => update(form), 0));
  });
  const reveal = (dialog, target) => {
    if (!dialog || !page.contains(dialog)) return;
    if (!dialog.open) dialog.showModal();
    if (target) {
      for (let parent = target.parentElement; parent && parent !== dialog; parent = parent.parentElement) {
        if (parent.matches('details')) parent.open = true;
      }
      target.scrollIntoView({block: 'nearest'});
    }
  };
  const fromHash = () => {
    const target = document.getElementById(location.hash.slice(1));
    reveal(target?.matches('dialog') ? target : target?.closest('dialog'), target);
  };
  page.addEventListener('click', event => {
    const trigger = event.target.closest('[data-program-dialog]');
    if (!trigger || !page.contains(trigger)) return;
    event.preventDefault();
    const dialog = document.getElementById(trigger.dataset.programDialog);
    history.replaceState(null, '', `#${dialog.id}`);
    reveal(dialog);
  });
  page.querySelectorAll('.program-dialog').forEach(dialog => dialog.addEventListener('close', () => {
    const target = document.getElementById(location.hash.slice(1));
    if (target === dialog || dialog.contains(target)) history.replaceState(null, '', location.pathname + location.search);
  }));
  window.addEventListener('hashchange', fromHash);
  const search = page.querySelector('[data-program-search]');
  search.addEventListener('input', () => {
    const query = search.value.trim().toLocaleLowerCase('tr');
    const cards = [...page.querySelectorAll('[data-program-card]')];
    cards.forEach(card => { card.hidden = !card.textContent.toLocaleLowerCase('tr').includes(query); });
    page.querySelector('[data-program-empty]').hidden = cards.some(card => !card.hidden);
  });
  page.addEventListener('submit', event => {
    const form = event.target;
    if (!initial.has(form)) return;
    // The existing economic-grid and removal handlers retain their own requests.
    if (saving.has(form)) { event.preventDefault(); return; }
    const dialog = form.closest('dialog');
    if (!dialog) return;
    const newCard = new URL(form.action).pathname.endsWith('/cards') && !form.elements.namedItem('id');
    const pending = {dialog: dialog.id, form: identity(form), period: form.elements.namedItem('period_id')?.value,
      previousCards: newCard ? forms.filter(item => new URL(item.action).pathname.endsWith('/cards'))
        .map(item => item.elements.namedItem('id')?.value).filter(Boolean) : null,
      grid: form.getAttribute('id') === 'economicGridForm', time: Date.now()};
    try { sessionStorage.setItem(storageKey, JSON.stringify(pending)); } catch { /* Storage is optional. */ }
    if (!event.defaultPrevented) {
      // A 303 inherits this fragment; rejected POSTs cannot mark a later GET saved.
      const action = new URL(form.action);
      action.hash = form.getAttribute('id');
      form.action = action.href;
      saving.add(form);
      update(form);
    }
  });
  window.addEventListener('pageshow', () => {
    saving.clear();
    forms.forEach(update);
  });
  const gridErrors = page.querySelector('#economicGridErrors');
  if (gridErrors) new MutationObserver(() => {
    if (!gridErrors.hidden) {
      try { sessionStorage.removeItem(storageKey); } catch { /* Storage is optional. */ }
    }
  }).observe(gridErrors, {attributes: true, attributeFilter: ['hidden']});
  let pending;
  try {
    pending = JSON.parse(sessionStorage.getItem(storageKey));
    sessionStorage.removeItem(storageKey);
  } catch { /* Storage is optional. */ }
  const invalid = page.querySelector('form [aria-invalid="true"], form [role="alert"]:not([hidden])');
  const recovery = page.querySelector('[data-program-recovery] form');
  if (recovery) {
    // A rejected record can have disappeared; keep the server's recovery form usable.
    const dialog = page.querySelector('#program-cards-dialog');
    dialog.append(recovery);
    reveal(dialog, recovery);
  } else if (invalid) {
    reveal(invalid.closest('dialog'), invalid.closest('form'));
  } else if (pending && location.pathname === page.dataset.programPage &&
      (location.hash || pending.grid) && Date.now() - pending.time < 120000 &&
      pending.period === new URLSearchParams(location.search).get('period_id')) {
    const dialog = document.getElementById(pending.dialog);
    const form = pending.previousCards ? forms.find(form =>
      new URL(form.action).pathname.endsWith('/cards') && form.elements.namedItem('id')?.value &&
      !pending.previousCards.includes(form.elements.namedItem('id').value)) :
      forms.find(form => identity(form) === pending.form);
    if (dialog) {
      const notice = document.createElement('span');
      notice.className = 'program-saved'; notice.role = 'status'; notice.textContent = 'Kaydedildi';
      (form?.querySelector('button') || dialog.querySelector('h2')).after(notice);
      history.replaceState(null, '', `#${form?.getAttribute('id') || dialog.id}`);
      reveal(dialog, notice);
      // The browser follows the inherited POST fragment after deferred scripts.
      // Finish at the confirmation once that initial navigation has settled.
      window.addEventListener('load', () => notice.scrollIntoView({block: 'center'}), {once: true});
    }
  } else fromHash();
})();
