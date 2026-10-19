// Transform the comparison as one canvas; device/image coordinates stay unchanged.
(()=>{
  const viewport=document.getElementById('compare-viewport'),canvas=viewport.querySelector('.main'),reset=document.getElementById('zoom-reset');
  let scale=1,x=0,y=64,space=false,drag=null,suppressClick=false,hand=false;
  const panButton=document.getElementById('canvas-pan');
  window.setCanvasHand=value=>{hand=value;panButton.setAttribute('aria-pressed',String(hand));viewport.classList.toggle('hand-mode',hand);};
  panButton.onclick=()=>{window.setCanvasHand(!hand);if(hand)window.cancelAISelection?.();};
  const editing=target=>target.closest('textarea,input,select,[contenteditable="true"]');
  function paint(){window.reviewZoomScale=scale;canvas.style.transform=`translate(${x}px,${y}px) scale(${scale})`;reset.textContent=`${Math.round(scale*100)}% · 重置`;positionBubble();}
  function zoomAt(px,py,next){const ratio=next/scale;x=px-(px-x)*ratio;y=py-(py-y)*ratio;scale=next;paint();}
  viewport.addEventListener('wheel',event=>{
    if(editing(event.target)||event.target.closest('#bubble-layer,.canvas-tools'))return;
    event.preventDefault();const rect=viewport.getBoundingClientRect();
    const delta=event.deltaY*(event.deltaMode===1?16:event.deltaMode===2?viewport.clientHeight:1);
    zoomAt(event.clientX-rect.left,event.clientY-rect.top,Math.max(.4,Math.min(4,scale*Math.exp(-Math.max(-200,Math.min(200,delta))*.002))));
  },{passive:false});
  reset.onclick=()=>{x=0;y=64;scale=1;paint();};
  document.addEventListener('keydown',event=>{if(event.code==='Space'&&!editing(event.target)){event.preventDefault();space=true;viewport.classList.add('pan-ready');}});
  document.addEventListener('keyup',event=>{if(event.code==='Space'){space=false;viewport.classList.remove('pan-ready');}});
  viewport.addEventListener('pointerdown',event=>{
    const interactive=event.target.closest('.picture-surface,.pin-bubble,button,a,input,textarea,select,.canvas-tools');
    const blank=!interactive;
    if(!(event.button===1||(event.button===0&&(space||hand||blank)))||editing(event.target)||event.target.closest('.canvas-tools'))return;
    if(!space&&event.target.closest('.ai-region-overlay.selecting'))return;
    event.preventDefault();event.stopImmediatePropagation();drag={id:event.pointerId,px:event.clientX,py:event.clientY,x,y};suppressClick=true;viewport.setPointerCapture(event.pointerId);viewport.classList.add('panning');
  },true);
  viewport.addEventListener('pointermove',event=>{if(!drag||drag.id!==event.pointerId)return;event.preventDefault();event.stopImmediatePropagation();x=drag.x+event.clientX-drag.px;y=drag.y+event.clientY-drag.py;paint();},true);
  function finish(event){if(!drag||drag.id!==event.pointerId)return;event.stopImmediatePropagation();drag=null;viewport.classList.remove('panning');if(viewport.hasPointerCapture(event.pointerId))viewport.releasePointerCapture(event.pointerId);setTimeout(()=>suppressClick=false,0);}
  viewport.addEventListener('pointerup',finish,true);viewport.addEventListener('pointercancel',finish,true);
  viewport.addEventListener('click',event=>{if(suppressClick){event.preventDefault();event.stopImmediatePropagation();}},true);
  window.addEventListener('blur',()=>{space=false;drag=null;viewport.classList.remove('pan-ready','panning');});

  paint();
})();
