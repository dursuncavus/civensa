const PRINT = location.hash === '#pdf';
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
if (PRINT) document.documentElement.classList.add('pdf');
const fmt = (value, decimals) => new Intl.NumberFormat('tr-TR', {
  minimumFractionDigits: decimals ?? 0, maximumFractionDigits: decimals ?? 6
}).format(value);
const deck = new Reveal({width:1920, height:1080, margin:0, minScale:.1, maxScale:2,
  hash:false, history:false, center:false, controls:!PRINT, progress:!PRINT,
  transition:reducedMotion ? 'none' : 'fade', transitionSpeed:'default', backgroundTransition:'fade',
  autoAnimate:!reducedMotion, autoAnimateDuration:.8, autoAnimateEasing:'cubic-bezier(.65,0,.35,1)',
  slideNumber:'c/t', view:PRINT ? 'print' : 'slide', pdfSeparateFragments:false,
  pdfMaxPagesPerSlide:1, pdfPageHeightOffset:0, showNotes:false});
window.deck = deck;
const charts = new Map();
function draw(el, animate) {
  const data = JSON.parse(el.parentElement.querySelector('.chart-data').textContent);
  const horizontal = data.variant === 'horizontal' || data.variant === 'stacked';
  const chart = charts.get(el) || echarts.init(el, null, {renderer:'svg', width:1680, height:640});
  const colors = ['#1e6b65','#c9ded9','#17554f','#545b64'];
  const category = {type:'category', data:data.categories,
    axisTick:{show:false}, axisLine:{show:!horizontal,lineStyle:{color:'#1f2328'}},
    axisLabel:{fontSize:horizontal ? 24 : 26, color:'#1f2328', interval:0, width:horizontal ? 410 : 420, overflow:'break'}};
  const value = {type:'value', name:data.unit, nameTextStyle:{fontSize:20,color:'#545b64'},
    axisLabel:{fontSize:20,color:'#545b64',formatter:v=>fmt(v)},
    splitLine:{lineStyle:{color:'#e3e1dc'}}, show:!horizontal};
  chart.setOption({textStyle:{fontFamily:'Fira Sans'}, animation:animate,
    animationDuration:800, animationEasing:'cubicOut', animationDelay:i=>Math.min(i*40,150),
    legend:{show:data.series.length>1,top:0,right:0,textStyle:{fontSize:24,color:'#545b64'}},
    grid:{left:horizontal?440:140,right:160,top:60,bottom:80},
    xAxis:horizontal?value:category,yAxis:horizontal?category:value,
    series:data.series.map((series,i)=>({name:series.name,type:'bar',
      stack:data.variant==='stacked'?'total':undefined,barMaxWidth:horizontal?48:200,
      data:series.values,itemStyle:{color:colors[i%colors.length],borderRadius:4},
      label:{show:true,position:data.variant==='stacked'?'inside':horizontal?'right':'top',
        fontSize:26,color:data.variant==='stacked'&&i===0?'#fff':'#1f2328',
        valueAnimation:animate,formatter:p=>series.display[p.dataIndex]}}))});
  charts.set(el,chart);
}
const counters = new WeakMap();
function countUp(el) {
  const previous = counters.get(el);
  if (previous) cancelAnimationFrame(previous);
  const finalText = el.dataset.final || el.textContent;
  el.dataset.final = finalText;
  if (PRINT || reducedMotion) { el.textContent = finalText; return; }
  const target = Number(el.dataset.count), start = performance.now();
  function step(now) {
    const progress = Math.min(1,(now-start)/900);
    el.textContent = progress===1 ? finalText : fmt(target*(1-Math.pow(1-progress,3)),Number(el.dataset.decimals));
    if (progress<1) counters.set(el,requestAnimationFrame(step));
  }
  counters.set(el,requestAnimationFrame(step));
}
const lastOf = {};
document.querySelectorAll('.slides>section[data-sec]').forEach(s=>lastOf[s.dataset.sec]=s);
function onShow(s) {
  if (!s || PRINT) return;
  s.querySelectorAll('tr.row').forEach(row=>{row.classList.remove('in');void row.offsetWidth;row.classList.add('in');});
  s.querySelectorAll('[data-count]').forEach(countUp);
  s.querySelectorAll('[data-chart]').forEach(el=>draw(el,!reducedMotion));
  if (s.dataset.sec && lastOf[s.dataset.sec]===s) {
    const tile = document.querySelector('#harita [data-id="'+s.dataset.sec+'"]');
    if (tile) tile.classList.add('done');
  }
}
// Load embedded fonts before layout and SVG chart measurement, including PDF.
window.sunumReady = document.fonts.ready.then(()=>deck.initialize()).then(()=>{
  if (PRINT) {
    document.querySelectorAll('[data-count]').forEach(countUp);
    document.querySelectorAll('[data-chart]').forEach(el=>draw(el,false));
  } else onShow(deck.getCurrentSlide());
  window.sunumRendered = true;
});
deck.on('slidechanged',event=>onShow(event.currentSlide));
function goTo(id) {
  const target = document.getElementById(id);
  if (target) { const index = deck.getIndices(target); deck.slide(index.h,index.v); }
}
document.querySelectorAll('#harita [data-go]').forEach(tile=>tile.addEventListener('click',()=>goTo(tile.dataset.go)));
document.getElementById('goMap').addEventListener('click',()=>goTo('harita'));
document.getElementById('toggleNotes').addEventListener('click',event=>{
  const visible=document.body.classList.toggle('shownotes');
  event.currentTarget.setAttribute('aria-pressed',String(visible));
});
// Changing to #pdf on an already open deck must reinitialize Reveal's print view.
window.addEventListener('hashchange',()=>{if ((location.hash==='#pdf')!==PRINT) location.reload();});
const tools=document.getElementById('tools');let timer;
function wake() {
  tools.classList.remove('hide');clearTimeout(timer);
  timer=setTimeout(()=>{if (!tools.matches(':hover,:focus-within')) tools.classList.add('hide');},2500);
}
['pointermove','pointerdown','keydown','focusin'].forEach(name=>document.addEventListener(name,wake));
wake();
window.addEventListener('beforeprint',()=>{
  if (!PRINT) {location.hash='pdf';location.reload();}
});
