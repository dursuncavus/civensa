/* Screen 024 presentation only. Existing app.js owns every request and selector. */
(() => {
  const page = document.querySelector('.data-entry-page');
  if (!page) return;
  const steps = page.querySelector('.workflow-strip');
  steps.setAttribute('role', 'list');
  steps.querySelectorAll('span').forEach(step => {
    step.setAttribute('role', 'listitem');
    if (step.classList.contains('active')) step.setAttribute('aria-current', 'step');
  });
  page.querySelectorAll('.tab').forEach(button => {
    button.setAttribute('aria-controls', button.dataset.tab);
    const sync = () => button.setAttribute('aria-pressed', String(button.classList.contains('active')));
    sync();
    new MutationObserver(sync).observe(button, {attributes: true, attributeFilter: ['class']});
  });
  // Native disclosure keyboard activation; Escape follows the prototype menu pattern.
  page.addEventListener('keydown', event => {
    if (event.key !== 'Escape') return;
    const panel = event.target.closest('.source-disclosure[open]');
    if (!panel) return;
    event.preventDefault();
    panel.open = false;
    panel.querySelector('summary').focus();
  });
  // Reuse the existing unsaved-navigation dialog, with this screen's styles.
  const draftConfirm = document.querySelector('.draft-confirm');
  if (draftConfirm) page.append(draftConfirm);
  page.querySelectorAll('.draft-removal').forEach(panel => {
    const trigger = panel.querySelector('summary');
    const dialog = document.createElement('dialog');
    dialog.className = 'removal-dialog';
    dialog.id = `removal-${panel.dataset.removal}`;
    trigger.setAttribute('aria-haspopup', 'dialog');
    trigger.setAttribute('aria-controls', dialog.id);
    const title = document.createElement('h2');
    title.id = `removal-title-${panel.dataset.removal}`;
    title.textContent = trigger.textContent;
    dialog.setAttribute('aria-labelledby', title.id);
    dialog.append(title);
    // Keep the original nodes, form ancestry, names, data attributes and handlers.
    [...panel.children].filter(node => node !== trigger).forEach(node => dialog.append(node));
    panel.append(dialog);
    const cancel = dialog.querySelector('[data-cancel-removal]');
    const close = () => {
      if (dialog.open) dialog.close();
      panel.open = false;
      trigger.focus();
    };
    trigger.addEventListener('click', event => {
      event.preventDefault();
      panel.open = true;
      dialog.showModal();
      cancel.focus();
    });
    cancel.addEventListener('click', close);
    dialog.addEventListener('cancel', event => { event.preventDefault(); close(); });
    dialog.addEventListener('keydown', event => {
      if (event.key !== 'Tab') return;
      const controls = [...dialog.querySelectorAll('button, [tabindex]')]
        .filter(control => !control.disabled && !control.hidden && control.tabIndex >= 0);
      const first = controls[0], last = controls.at(-1);
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault(); last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault(); first.focus();
      }
    });
  });
})();
