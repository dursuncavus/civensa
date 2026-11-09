// CIV-199: page script kept out of the template because the CSP allows only same-origin scripts.
(function(){
  // (11) After a save the row lives in a closed dialog: reopen it and bring the row into view.
  const saved=document.querySelector('.binding-row.is-saved');
  const dialog=saved&&saved.closest('dialog');
  if(dialog&&typeof dialog.showModal==='function'){dialog.showModal();saved.scrollIntoView({block:'center'});}
  // (14) Owner, 9 Nov: the save button stays inactive until something actually changed.
  document.querySelectorAll('.indicator-direction-form').forEach(form=>{
    const select=form.querySelector('select[name=direction]'),reason=form.querySelector('textarea[name=reason]'),button=form.querySelector('button.primary');
    if(!select||!reason||!button)return;
    const initial=select.value;
    const sync=()=>{const changed=select.value!==initial;button.disabled=!(changed&&reason.value.trim());
      button.title=changed?(reason.value.trim()?'':'Önce gerekçe yazın.'):'Yön değişmedi.';};
    select.addEventListener('change',sync);reason.addEventListener('input',sync);sync();
  });
  const input=document.getElementById('bindingSearch'), count=document.getElementById('bindingSearchCount');
  if(!input)return;
  const rows=[...document.querySelectorAll('.binding-row')];
  const fold=t=>t.toLocaleLowerCase('tr-TR');
  input.addEventListener('input',()=>{
    const q=fold(input.value.trim());
    let shown=0;
    rows.forEach(r=>{const hit=!q||fold(r.dataset.search||'').includes(q);r.hidden=!hit;if(hit)shown++;});
    document.querySelectorAll('.binding-dept').forEach(d=>{const any=[...d.querySelectorAll('.binding-row')].some(r=>!r.hidden);d.hidden=!any;if(q&&any)d.open=true;});
    document.querySelectorAll('[data-binding-card]').forEach(card=>{
      const hits=[...card.querySelectorAll('.binding-row')].filter(r=>!r.hidden).length;
      card.hidden=hits===0;
      const note=card.querySelector('[data-binding-hits]');if(note)note.textContent=q&&hits?`${hits} gösterge aramayla eşleşti.`:'';
    });
    count.textContent=q?`${shown} gösterge bulundu.`:'';
  });
})();
