/* Credentials remain in this page's memory until the single download is used. */
(() => {
  const file = document.getElementById('bulkUserFile');
  if (!file) return;
  const preview = document.getElementById('previewBulkUsers');
  const apply = document.getElementById('applyBulkUsers');
  const download = document.getElementById('downloadBulkCredentials');
  const result = document.getElementById('bulkUserResult');
  let checkedFile = null, credentials = null, batch = null, busy = false;
  const form = () => {const body = new FormData(); body.append('file', file.files[0]); return body;};
  file.addEventListener('change', () => {
    checkedFile = null; apply.disabled = true;
    result.textContent = 'Dosya değişti. Oluşturmadan önce yeniden önizleyin.';
  });
  preview.addEventListener('click', async () => {
    if (busy) return;
    if (!file.files.length) {toast('Önce CSV dosyasını seçin.'); return;}
    busy = true; checkedFile = null; preview.disabled = apply.disabled = file.disabled = true;
    result.textContent = 'Dosya kontrol ediliyor…';
    const selectedFile = file.files[0];
    const {r, j} = await jsonFetch('/api/users/bulk-preview', {method: 'POST', body: form()});
    busy = false; preview.disabled = file.disabled = false;
    if (!r.ok || !j.ok) {
      result.innerHTML = '<b>Dosya uygulanamaz.</b><p>' + escapeHtml(errorMessage(j)) + '</p>';
      return;
    }
    checkedFile = selectedFile; apply.disabled = false;
    result.innerHTML = '<b class="ok">' + j.count + ' kişisel hesap oluşturulmaya hazır.</b>' +
      '<div class="table-wrap"><table><thead><tr><th>Müdürlük</th><th>Ad Soyad</th><th>E-posta</th><th>Görev</th></tr></thead><tbody>' +
      j.rows.map(row => '<tr>' + [row.department_name, row.full_name, row.email, row.duty].map(value => '<td>' + escapeHtml(value) + '</td>').join('') + '</tr>').join('') + '</tbody></table></div>';
  });
  apply.addEventListener('click', async () => {
    if (busy || credentials) return;
    if (!checkedFile || file.files[0] !== checkedFile) {toast('Dosyayı yeniden önizleyin.'); return;}
    if (!confirm('Önizlenen kişisel hesaplar oluşturulsun mu? Ardından tek seferlik parola dosyasını indirin.')) return;
    busy = true; apply.disabled = preview.disabled = file.disabled = true;
    result.textContent = 'Hesaplar oluşturuluyor…';
    try {
      const response = await fetch('/api/users/bulk-import', {
        method: 'POST', body: form(), cache: 'no-store',
        headers: {'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.content || ''}
      });
      if (response.redirected) {location.href = response.url; return;}
      if (!response.ok) {
        const payload = await response.json();
        result.textContent = errorMessage(payload) || 'Hesaplar oluşturulamadı. Kullanıcı listesini kontrol edin.';
        return;
      }
      credentials = await response.blob();
      batch = response.headers.get('X-Account-Batch');
      download.hidden = false;
      result.textContent = response.headers.get('X-Accounts-Created') + ' hesap oluşturuldu. Sayfadan ayrılmadan Parola dosyasını indir düğmesine basın.';
    } catch {
      result.textContent = 'İşlem sonucu veya parola dosyası alınamadı. Kullanıcılar listesini yenileyin; oluşturulmuş hesaplar için Parola sıfırla seçin.';
    } finally {
      busy = false; checkedFile = null;
      if (!credentials) preview.disabled = file.disabled = false;
    }
  });
  download.addEventListener('click', () => {
    if (!credentials) return;
    const url = URL.createObjectURL(credentials), link = document.createElement('a');
    link.href = url; link.download = 'civensa-gecici-parolalar-' + batch + '.csv';
    document.body.appendChild(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    credentials = null; download.hidden = true;
    result.innerHTML = 'Parola dosyası teslim edildi; tekrar indirilemez. Kaybolursa her hesap için Parola sıfırla seçin. <a href="/users">Kullanıcı listesini yenile</a>';
    preview.disabled = file.disabled = false;
  });
  window.addEventListener('beforeunload', event => {
    if (credentials || busy) {event.preventDefault(); event.returnValue = '';}
  });
})();

(() => {
  const button = document.getElementById('retireSelectedUsers');
  if (!button) return;
  button.addEventListener('click', async () => {
    const ids = [...document.querySelectorAll('.retire-user:checked')].map(box => Number(box.value));
    const reason = document.getElementById('retireUsersReason').value.trim();
    const result = document.getElementById('retireUsersResult');
    if (!ids.length || !reason) {result.textContent = 'En az bir hesap seçin ve pasifleştirme gerekçesini yazın.'; return;}
    if (!confirm(ids.length + ' hesabın giriş erişimi kapatılsın mı?')) return;
    button.disabled = true;
    const {r, j} = await jsonFetch('/api/users/bulk-deactivate', {method: 'POST',
      headers: {'Content-Type': 'application/json'}, body: JSON.stringify({user_ids: ids, reason})});
    if (!r.ok) {result.textContent = j.detail; button.disabled = false; return;}
    result.textContent = j.deactivated + ' hesap gerekçeyle pasifleştirildi.';
    location.reload();
  });
})();

(() => {
  const form = document.getElementById('firstPasswordForm');
  if (!form) return;
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const button = form.querySelector('button'); button.disabled = true;
    const {r, j} = await jsonFetch('/api/me/change-password', {method: 'POST',
      headers: {'Content-Type': 'application/json'}, body: JSON.stringify({
        current_password: document.getElementById('firstCurrentPassword').value,
        new_password: document.getElementById('firstNewPassword').value,
        confirmation: document.getElementById('firstConfirmPassword').value
      })});
    if (!r.ok) {document.getElementById('firstPasswordError').textContent = j.detail; button.disabled = false; return;}
    form.reset(); location.href = '/modules';
  });
})();
