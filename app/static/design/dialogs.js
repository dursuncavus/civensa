(() => {
  document.addEventListener('click', event => {
    const button = event.target.closest('[data-open-dialog]');
    if (!button || event.defaultPrevented) return;
    const dialog = document.getElementById(button.dataset.openDialog);
    if (dialog instanceof HTMLDialogElement && !dialog.open) dialog.showModal();
  });
  // Preserve the full secondary text while keeping each preview on one line.
  document.querySelectorAll('.directorate-dialog p').forEach(paragraph => {
    if (paragraph.textContent.trim().length <= 140 || paragraph.closest('details')
        || paragraph.querySelector('input,select,textarea,button')
        || paragraph.hasAttribute('role')) return;
    const details = document.createElement('details');
    const summary = document.createElement('summary');
    summary.textContent = paragraph.textContent.trim().slice(0, 100) + '…';
    paragraph.before(details);
    details.append(summary, paragraph);
  });
  const errorDialog = document.querySelector('dialog[data-dialog-error]');
  if (errorDialog && !errorDialog.open) errorDialog.showModal();
  document.querySelectorAll('[data-directorate-search]').forEach(input => {
    const grid = document.getElementById(input.dataset.directorateSearch);
    if (!grid) return;
    input.addEventListener('input', () => {
      const query = input.value.toLocaleLowerCase('tr').trim();
      let count = 0;
      grid.querySelectorAll('[data-directorate-card]').forEach(card => {
        card.hidden = !card.dataset.directorateCard.toLocaleLowerCase('tr').includes(query);
        if (!card.hidden) count += 1;
      });
      const status = document.getElementById(input.dataset.directorateSearch + '-status');
      if (status) status.textContent = `${count} müdürlük gösteriliyor.`;
    });
  });
})();
