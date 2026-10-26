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

// CIV-108 · Sentetik durumlar yalnız 022 prototipinde kullanılır.
const homeState = document.querySelector(".department-home-prototype #home-state");
if (homeState) {
  const states = {
    a: { entry: "Başlanmadı", issues: 0, submission: "draft", started: false },
    b: { entry: "Devam ediyor", issues: 3, submission: "draft", started: true },
    c: { entry: "Tamamlandı", issues: 0, submission: "draft", started: true },
    d: { entry: "Tamamlandı", issues: 0, submission: "submitted", started: true },
    e: { entry: "Devam ediyor", issues: 3, submission: "returned", started: true },
  };
  const submissionLabels = {
    draft: "Gönderilmedi",
    submitted: "Gönderildi",
    returned: "İade edildi — düzeltip yeniden gönderin",
    approved: "Onaylandı",
  };
  const setTag = (id, text, tone) => {
    const tag = document.getElementById(id);
    tag.textContent = text;
    tag.className = `badge ${tone}`;
  };
  const showHomeState = () => {
    const state = states[homeState.value];
    setTag("home-entry-status", state.entry, state.entry === "Tamamlandı" ? "success" : "neutral");
    setTag("home-check-status", state.issues > 0
      ? `Düzeltme gerekli · ${state.issues} gösterge`
      : state.started ? "Sorun yok" : "Bekliyor",
    state.issues > 0 ? "warning" : state.started ? "success" : "neutral");
    setTag("home-send-status", submissionLabels[state.submission],
      state.submission === "returned" ? "warning" : state.submission === "approved" ? "success" : "neutral");
    const count = document.getElementById("home-issue-count");
    count.textContent = state.issues;
    count.classList.toggle("home-has-issues", state.issues > 0);
    document.getElementById("home-submission").textContent =
      state.submission === "draft" ? "Taslak" : state.submission === "submitted" ? "İncelemede" : state.submission === "returned" ? "İade edildi" : submissionLabels[state.submission];
  };
  homeState.addEventListener("change", showHomeState);
  showHomeState();
}
