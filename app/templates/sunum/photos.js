
// The divider owns its arrow keys; Reveal must keep the current slide.
document.querySelectorAll('.ba-wrap').forEach(w => {
  const handle=w.querySelector('.handle');
  let dragging=false, entrance;
  const set=value=>{
    const x=Math.max(0,Math.min(100,value));
    w.style.setProperty('--x',x+'%');handle.setAttribute('aria-valuenow',String(Math.round(x)));
  };
  const position=e=>{
    const r=w.getBoundingClientRect();set((e.clientX-r.left)/r.width*100);
  };
  const enter=()=>{
    clearTimeout(entrance);
    if (PRINT || reducedMotion) {set(50);return;}
    set(100);void w.offsetWidth;
    entrance=setTimeout(()=>set(50),350);
  };
  w.addEventListener('pointerdown',e=>{
    if (PRINT) return;
    clearTimeout(entrance);dragging=true;w.classList.add('drag');
    w.setPointerCapture(e.pointerId);handle.focus();position(e);e.preventDefault();e.stopPropagation();
  });
  w.addEventListener('pointermove',e=>{if(dragging){position(e);e.stopPropagation();}});
  const end=()=>{dragging=false;w.classList.remove('drag');};
  w.addEventListener('pointerup',end);w.addEventListener('pointercancel',end);
  handle.addEventListener('keydown',e=>{
    if (!['ArrowLeft','ArrowRight','Home','End'].includes(e.key)) return;
    clearTimeout(entrance);e.preventDefault();e.stopImmediatePropagation();w.classList.add('drag');
    const current=Number(handle.getAttribute('aria-valuenow'));
    set(e.key==='Home'?0:e.key==='End'?100:current+(e.key==='ArrowLeft'?-5:5));
  },true);
  handle.addEventListener('keyup',()=>{if(!dragging)w.classList.remove('drag');});
  deck.on('slidechanged',e=>{if(e.currentSlide.contains(w))enter();else clearTimeout(entrance);});
  window.sunumReady.then(()=>{if(PRINT || deck.getCurrentSlide().contains(w))enter();});
});
