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

// CIV-116 · Sentetik durumlar yalnız 037 prototipinde; gerçek hesaplama veya kayıt yok.
const reportState = document.querySelector('.report-preparation-prototype #report-state');
if (reportState) {
  const scope = document.querySelector('.report-preparation-prototype');
  const controls = [...scope.querySelectorAll('.rp-content input, .rp-content textarea, .rp-content select')];
  scope.querySelectorAll('#section-3 select').forEach((el, i) => { el.selectedIndex = i; });
  const initial = controls.map(el => el.value);
  const setVisible = (selector, visible) => scope.querySelectorAll(selector).forEach(el => { el.hidden = !visible; });
  const showReportState = () => {
    const state = reportState.value;
    const empty = state === 'a', complete = state === 'c' || state === 'd', readonly = state === 'd';
    scope.classList.toggle('is-readonly', readonly);
    const role = scope.querySelector('.userbox > span');
    const user = document.createElement('strong');
    user.textContent = state === 'e' ? 'Strateji uzmanı (sentetik)' : 'Birim Müdürü (sentetik)';
    role.replaceChildren(document.createTextNode(state === 'e' ? 'Strateji' : 'Müdürlük'), document.createElement('br'), user);
    setVisible('.rp-empty', empty);
    setVisible('.rp-existing', !empty);
    setVisible('.rp-unverified, #rp-issues, #rp-warnings', !empty && !complete);
    setVisible('.rp-complete', complete);
    setVisible('.rp-save, [data-edit-only], .rp-new', !readonly);
    setVisible('#section-2 [data-edit-only]', !readonly && !empty);
    setVisible('#rp-readonly', readonly);
    setVisible('#rp-strategy', state === 'e');
    document.getElementById('rp-counts').textContent = empty ? '0 kart · 0 gösterge · 0 faaliyet' : '2 kart · 4 gösterge · 3 faaliyet';
    document.getElementById('rp-checks').textContent = empty ? 'Henüz kontrol edilecek kayıt yok.' : complete ? 'Kart ve mali tablo kontrolleri tamamlandı.' : 'Önce eksik kayıtları tamamlayın, ardından kaynak değerlerini doğrulayın.';
    const statuses = empty ? Array(6).fill('Başlanmadı') : complete ? Array(6).fill('Tamamlandı') : ['2 kart', '2 faaliyet kartsız', 'Tamamlandı', '3 kayıt doğrulanacak', '1 tutar doğrulanacak', '1 hücre doğrulanacak'];
    statuses.forEach((text, i) => {
      const el = document.getElementById(`rp-status-${i + 1}`);
      el.textContent = text;
      el.className = `badge ${text === 'Tamamlandı' ? 'success' : !empty && i !== 0 ? 'warning' : 'neutral'}`;
    });
    controls.forEach((el, i) => {
      el.disabled = readonly && el.tagName === 'SELECT';
      el.readOnly = readonly;
      if (el.tagName !== 'SELECT') el.value = empty ? '' : initial[i];
      else el.value = initial[i];
    });
    // İki kartsız faaliyet; diğer tüm göstergeler ve faaliyetler kartlıdır.
    if (!empty && !complete) {
      const assignments = scope.querySelectorAll('#section-2 form select');
      assignments[4].value = 'Kart seçin';
      assignments[5].value = 'Kart seçin';
    }
    scope.querySelectorAll('.rp-record-status').forEach(el => {
      if (el.closest('[data-edit-only], .rp-new')) return;
      const pending = !complete && el.closest('#section-5') && el.closest('details') === scope.querySelector('#section-5 details');
      el.textContent = pending ? 'Kaynak doğrulaması bekliyor' : 'Tamamlandı';
      el.className = `badge rp-record-status ${pending ? 'warning' : 'success'}`;
    });
    const rows = ['Çevre programı', 'Çevre hizmetleri', 'Örnek Hizmet Müdürlüğü'];
    document.getElementById('rp-reconciliation').replaceChildren(...rows.map(label => {
      const row = document.createElement('tr');
      [label, '2026 bütçe', empty ? '—' : complete ? '4.000.000,00' : 'Eksik ara toplam', empty ? '—' : complete ? '4.000.000,00' : 'Kaynak toplamı yok', complete ? '0,00' : '—', empty ? 'Henüz kayıt yok' : complete ? 'Mutabık' : 'Eksik bağlantı / tutar · Atamaları ve kaynakları kontrol edin.'].forEach((text, i) => {
        const cell = document.createElement(i === 0 ? 'th' : 'td');
        if (i === 0) cell.scope = 'row';
        if (i >= 2 && i <= 4) cell.className = 'numeric';
        cell.textContent = text;
        row.append(cell);
      });
      return row;
    }));
    // Uzun formlar her yeni örnek durumda kapalı, uyarı özeti açık başlar.
    scope.querySelectorAll('.rp-record').forEach(el => { el.open = el.id === 'rp-issues'; });
  };
  reportState.addEventListener('change', showReportState);
  showReportState();
}
