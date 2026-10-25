/* Yalnız menü/pencere davranışı. Veri, API veya depolama katmanı yoktur. */
const dialogTriggers = new WeakMap();
function openDialog(id, trigger, focusTarget = trigger) {
  const dialog = document.getElementById(id);
  if (!dialog) return;
  dialogTriggers.set(dialog, focusTarget);
  if (id === "destination-dialog") {
    document.getElementById("destination-target").textContent =
      trigger.dataset.originalTarget ||
      "Bu örneğin uygulama hedefi ekran haritasında yer alır.";
  }
  dialog.showModal();
}
document.addEventListener("click", (event) => {
  const trigger = event.target.closest("[data-open], [data-close]");
  if (trigger) {
    event.preventDefault();
    if (trigger.hasAttribute("data-close")) {
      trigger.closest("dialog").close();
      return;
    }
    const current = trigger.closest("dialog");
    const focusTarget = current ? dialogTriggers.get(current) : trigger;
    if (current) current.close();
    openDialog(trigger.dataset.open, trigger, focusTarget || trigger);
    return;
  }
  document.querySelectorAll("details.menu[open]").forEach((menu) => {
    if (!menu.contains(event.target)) menu.open = false;
  });
});
document.addEventListener("submit", (event) => {
  if (event.target.method === "dialog") return;
  event.preventDefault();
  openDialog("simulation-dialog", event.submitter || event.target);
});
document.querySelectorAll("dialog").forEach((dialog) => {
  dialog.addEventListener("close", () => {
    const returnFocus = dialogTriggers.get(dialog);
    if (returnFocus?.isConnected && !returnFocus.closest("dialog:not([open])"))
      returnFocus.focus();
  });
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    document.querySelectorAll("details.menu[open]").forEach((menu) => {
      menu.open = false;
      menu.querySelector("summary").focus();
    });
  }
});
