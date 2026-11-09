// CIV-199: page script kept out of the template because the CSP allows only same-origin scripts.
(function(){
  const input=document.getElementById('bindingSearch'), count=document.getElementById('bindingSearchCount');
  if(!input)return;
  const rows=[...document.querySelectorAll('.binding-row')];
  const fold=t=>t.toLocaleLowerCase('tr-TR');
  input.addEventListener('input',()=>{
    const q=fold(input.value.trim());
    let shown=0;
    rows.forEach(r=>{const hit=!q||fold(r.dataset.search||'').includes(q);r.hidden=!hit;if(hit)shown++;});
    document.querySelectorAll('.binding-dept').forEach(d=>{const any=[...d.querySelectorAll('.binding-row')].some(r=>!r.hidden);d.hidden=!any;if(q&&any)d.open=true;});
    count.textContent=q?`${shown} gösterge bulundu.`:'';
  });
})();
