/* Presentation/accessibility only. app.js retains password and notification requests. */
(() => {
  // Old screens include both wrapped and bare tables. Keep their column widths
  // and controls reachable in a local scrollport within the narrower workspace.
  const main = document.querySelector('.workspace > main');
  const containTables = () => main.querySelectorAll('table').forEach(table => {
    for (let parent = table.parentElement; parent && parent !== main; parent = parent.parentElement) {
      if (['auto', 'scroll'].includes(getComputedStyle(parent).overflowX)) return;
    }
    const scroll = document.createElement('div');
    scroll.className = 'shell-table-scroll';
    scroll.tabIndex = 0;
    scroll.setAttribute('role', 'region');
    scroll.setAttribute('aria-label', 'Yatay kaydırılabilir tablo');
    table.before(scroll);
    scroll.append(table);
  });
  if (main) {
    containTables();
    new MutationObserver(containTables).observe(main, {childList: true, subtree: true});
  }
  const modal = document.getElementById('passwordModal');
  if (!modal) return;
  const shell = document.querySelector('.app-shell');
  const opener = document.getElementById('changePasswordButton');
  const cancel = document.getElementById('cancelPasswordChange');
  new MutationObserver(() => {
    shell.inert = !modal.hidden;
    if (modal.hidden) opener.focus();
  }).observe(modal, {attributes: true, attributeFilter: ['hidden']});
  modal.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      event.preventDefault();
      cancel.click();
    }
    if (event.key === 'Tab') {
      const controls = [...modal.querySelectorAll('input, button')].filter(el => !el.disabled);
      const first = controls[0], last = controls.at(-1);
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault(); last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault(); first.focus();
      }
    }
  });
  const panel = document.getElementById('notificationPanel');
  const button = document.getElementById('notificationButton');
  new MutationObserver(() => {
    button.setAttribute('aria-expanded', String(!panel.hidden));
    if (!panel.hidden) document.getElementById('closeNotifications').focus();
    else button.focus();
  }).observe(panel, {attributes: true, attributeFilter: ['hidden']});
  panel.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      event.preventDefault(); document.getElementById('closeNotifications').click();
    }
  });
})();
