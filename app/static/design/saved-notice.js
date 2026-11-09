(() => {
  const key = 'civensa-form-position';
  const notice = document.getElementById('saved-notice');
  try {
    const previous = JSON.parse(sessionStorage.getItem(key) || 'null');
    sessionStorage.removeItem(key);
    if (notice && !notice.hidden && previous && previous.at > Date.now() - 300000) {
      if (previous.dialog) {
        const dialog = document.getElementById(previous.dialog);
        if (dialog instanceof HTMLDialogElement && !dialog.open) dialog.showModal();
      }
      requestAnimationFrame(() => window.scrollTo(previous.x, previous.y));
    }
  } catch (_) { /* Feedback still works when session storage is unavailable. */ }
  document.addEventListener('submit', event => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || form.method.toLowerCase() !== 'post'
        || event.defaultPrevented || new URL(form.action, location.href).origin !== location.origin) return;
    try {
      sessionStorage.setItem(key, JSON.stringify({x: scrollX, y: scrollY,
        dialog: form.closest('dialog')?.id || '', at: Date.now()}));
    } catch (_) { /* A storage restriction must never prevent saving. */ }
  });
})();
