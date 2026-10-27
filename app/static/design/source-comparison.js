(() => {
  const root = document.querySelector('.source-comparison-page');
  if (!root) return;
  const filter = root.querySelector('.status-filter');
  const buttons = [...filter.querySelectorAll('[data-filter-status]')];
  const rows = [...root.querySelectorAll('#source-comparison tr[data-status]')];
  const empty = root.querySelector('.filter-empty');
  const setFilter = status => {
    let visible = 0;
    for (const row of rows) {
      row.hidden = status !== '' && row.dataset.status !== status;
      if (!row.hidden) visible += 1;
    }
    for (const button of buttons) {
      button.setAttribute('aria-pressed', String(button.dataset.filterStatus === status));
    }
    empty.hidden = visible !== 0;
  };
  for (const button of buttons) {
    // Native buttons provide Tab, Space and Enter activation.
    button.addEventListener('click', () => setFilter(button.dataset.filterStatus));
  }
  setFilter('');
  filter.hidden = false;
})();
