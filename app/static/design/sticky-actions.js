// CIV-218: the İç Kontrol answers form keeps its save bar stuck to the bottom
// of the screen. A control reached with the keyboard that lands behind the bar
// is scrolled up just enough to stay visible (scroll-padding does not apply to
// focus moves inside the viewport).
(() => {
  const bar = document.querySelector('.questionnaire-form form[action$="/answers"] > .ic-actions');
  if (!bar) return;
  bar.closest('form').addEventListener('focusin', event => {
    const target = event.target;
    if (!(target instanceof HTMLElement) || bar.contains(target)) return;
    const overlap = target.getBoundingClientRect().bottom - bar.getBoundingClientRect().top;
    if (overlap > 0) window.scrollBy(0, overlap + 8);
  });
})();
