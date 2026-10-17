document.addEventListener('change', async event => {
  const field = event.target.closest('.contract-bound');
  if (!field) return;
  field.disabled = true;
  try {
    const response = await fetch(`/api/activities/${field.dataset.activityId}/contract-bound`, {
      method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').content},
      body: JSON.stringify({contract_bound: field.checked})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Sözleşme işareti kaydedilemedi. Sayfayı yenileyin.');
  } catch (error) { field.checked = !field.checked; alert(error.message); }
  finally { field.disabled = false; }
});
