// CIV-199: page script kept out of the template because the CSP allows only same-origin scripts.
(function(){
  const input=document.getElementById('reportSearch'),count=document.getElementById('reportSearchCount');
  if(!input)return;
  const groups=[...document.querySelectorAll('.report-group')],fold=t=>t.toLocaleLowerCase('tr-TR');
  input.addEventListener('input',()=>{
    const q=fold(input.value.trim());let shown=0;
    groups.forEach(g=>{const hit=!q||fold(g.querySelector('h3')?.textContent||'').includes(q);g.hidden=!hit;if(hit)shown++});
    count.textContent=q?`${shown} rapor bulundu.`:'';
  });
})();
