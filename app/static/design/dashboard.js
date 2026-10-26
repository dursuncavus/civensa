(() => {
  const section = document.querySelector('#mudurluk-ilerleme');
  if (!section) return;

  const cards = [...section.querySelectorAll('.progress-filter[data-filter-states]')];
  for (const card of cards) {
    card.setAttribute('role', 'button');
    card.setAttribute('aria-pressed', 'false');
  }

  const rows = [...section.querySelectorAll('tbody tr[data-state]')];
  const status = section.querySelector('#progressFilterStatus');
  const count = status?.querySelector('[data-filter-count]');
  const clear = status?.querySelector('[data-clear-progress-filter]');
  if (!cards.length || !rows.length || !status || !count || !clear) return;

  const setFilter = states => {
    const selected = states ? new Set(states) : null;
    let visible = 0;

    for (const row of rows) {
      const matches = !selected || selected.has(row.dataset.state);
      row.hidden = !matches;
      if (matches) visible += 1;
    }

    for (const card of cards) {
      const active = selected !== null &&
        card.dataset.filterStates.split(',').some(state => selected.has(state));
      card.setAttribute('aria-pressed', String(active));
    }

    count.textContent = String(visible);
    status.hidden = selected === null;
  };

  for (const card of cards) {
    card.addEventListener('click', event => {
      event.preventDefault();
      setFilter(card.dataset.filterStates.split(','));
    });
    card.addEventListener('keydown', event => {
      if (event.key === ' ' || event.key === 'Enter') {
        event.preventDefault();
        setFilter(card.dataset.filterStates.split(','));
      }
    });
  }

  clear.addEventListener('click', event => {
    event.preventDefault();
    setFilter(null);
  });
})();
