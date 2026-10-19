(()=>{
 const regions=new Map();let mode='full',selecting=false,start=null;
 const controls={};
 for(const [side,id] of [['reference','reference-surface'],['capture','shot-surface']]){
  const surface=$(id),overlay=document.createElement('div');overlay.className='ai-region-overlay';
  overlay.innerHTML=`<div class="ai-region-box"><span>${side==='reference'?'原稿对比范围':'截图分析范围'}</span></div>`;
  surface.append(overlay);const box=overlay.firstElementChild;
  for(const edge of ['nw','n','ne','e','se','s','sw','w']){const handle=document.createElement('i');handle.className='region-handle '+edge;handle.dataset.edge=edge;box.append(handle);}
  controls[side]={surface,overlay,box};
  const point=e=>{const r=surface.getBoundingClientRect();return{x:Math.max(0,Math.min(1,(e.clientX-r.left)/r.width)),y:Math.max(0,Math.min(1,(e.clientY-r.top)/r.height))};};
  overlay.onpointerdown=e=>{
   if(e.button!==0||mode!=='local'||aiPending(aiState.tasks.get(state.run?.id)))return;
   const pair=regions.get(state.run.id)||{},previous=pair[side],inside=e.target.closest('.ai-region-box');
   if(!selecting&&!inside)return;
   e.preventDefault();e.stopPropagation();start={...point(e),id:state.run.id,side,previous:previous?{...previous}:null,action:inside?(e.target.dataset.edge||'move'):'new'};overlay.setPointerCapture(e.pointerId);paint();
  };
  overlay.onpointermove=e=>{
   if(!start||start.side!==side)return;
   const p=point(e),pair=regions.get(start.id)||{},r=start.previous,dx=p.x-start.x,dy=p.y-start.y;
   if(start.action==='new')pair[side]={x:Math.min(p.x,start.x),y:Math.min(p.y,start.y),width:Math.abs(p.x-start.x),height:Math.abs(p.y-start.y)};
   else if(start.action==='move')pair[side]={...r,x:Math.max(0,Math.min(1-r.width,r.x+dx)),y:Math.max(0,Math.min(1-r.height,r.y+dy))};
   else{
    let l=r.x,t=r.y,right=r.x+r.width,bottom=r.y+r.height;const edge=start.action;
    if(edge.includes('w'))l=Math.max(0,Math.min(right-.01,r.x+dx));
    if(edge.includes('e'))right=Math.min(1,Math.max(l+.01,r.x+r.width+dx));
    if(edge.includes('n'))t=Math.max(0,Math.min(bottom-.01,r.y+dy));
    if(edge.includes('s'))bottom=Math.min(1,Math.max(t+.01,r.y+r.height+dy));
    pair[side]={x:l,y:t,width:right-l,height:bottom-t};
   }
   regions.set(start.id,pair);paint();
  };
  function finish(e,cancel){if(!start||start.side!==side)return;const pair=regions.get(start.id)||{},r=pair[side];if(cancel||!r||r.width<.01||r.height<.01){if(start.previous)pair[side]=start.previous;else delete pair[side];}regions.set(start.id,pair);start=null;selecting=!(pair.capture&&pair.reference);if(overlay.hasPointerCapture(e.pointerId))overlay.releasePointerCapture(e.pointerId);paint();}
  overlay.onpointerup=e=>finish(e,false);overlay.onpointercancel=e=>finish(e,true);
 }
 $('ai-full-run').onclick=()=>{const pair=regions.get(state.run?.id)||{};if(mode==='full')startAIAnalysis();else if(mode==='local'&&pair.capture&&pair.reference)startAIAnalysis(pair.capture,pair.reference);};
 window.getAIRegion=()=>regions.get(state.run?.id)?.capture||null;
 function paint(){
  const available=!live.view&&!state.switching&&!!state.run,pending=aiPending(aiState.tasks.get(state.run?.id)),pair=regions.get(state.run?.id)||{};
  document.querySelector('.canvas-tools').hidden=!state.design;
  for(const id of ['ai-analyze','ai-region','manual-annotate'])$(id).hidden=!available;
  for(const [side,{overlay,box}] of Object.entries(controls)){const r=pair[side];overlay.hidden=!available||mode!=='local'||(!r&&!selecting);overlay.classList.toggle('selecting',selecting&&!pending);overlay.classList.toggle('editable',!pending&&mode==='local');box.hidden=!r;if(r)Object.assign(box.style,{left:r.x*100+'%',top:r.y*100+'%',width:r.width*100+'%',height:r.height*100+'%'});}
  window.manualAnnotationEnabled=available&&mode==='manual';
  $('manual-annotate').disabled=!available;
  $('manual-annotate').setAttribute('aria-pressed',String(mode==='manual'));
  $('pin-layer').classList.toggle('manual-mode',window.manualAnnotationEnabled);
  $('pin-layer').setAttribute('aria-label',window.manualAnnotationEnabled?'截图标注区：点击添加问题':'截图标注区：查看已有问题');
  renderStatus();
  $('ai-analyze').setAttribute('aria-pressed',String(mode==='full'));$('ai-region').setAttribute('aria-pressed',String(mode==='local'));
  $('ai-region').textContent='▧ 局部框选';$('ai-full-run').hidden=!available||!['full','local'].includes(mode);$('ai-full-run').disabled=!available||pending||state.busy||!aiState.models.length||(mode==='local'&&(!pair.reference||!pair.capture||!!start));const rerun=!!state.run?.ai_result_attempt||!!state.run?.ai_applied_ids?.length||state.run?.issues.some(i=>i.id.startsWith('ai-')||i.node_label==='Codex 视觉分析');$('ai-full-run').textContent=pending?'分析中…':rerun?'重新分析':'开始分析';$('ai-full-run').title=rerun?'清除上一轮 AI 标注，保留手动标注，重新分析':'分析当前截图';
  $('region-actions').hidden=!available||mode!=='local';$('region-hint').textContent=!pair.reference?'框选左侧原稿':!pair.capture?'框选右侧截图':'两侧范围已选定';

 }
 window.syncAIRegion=(available,pending)=>{if(!available||pending)selecting=false;$('ai-region').hidden=false;$('ai-region').disabled=!available||pending;paint();};
 $('manual-annotate').onclick=()=>{window.setCanvasHand?.(false);mode='manual';selecting=false;paint();};
 window.chooseAIWhole=()=>{mode='full';selecting=false;window.setCanvasHand?.(false);paint();};
 $('ai-region').onclick=()=>{window.setCanvasHand?.(false);mode='local';selecting=true;paint();};
 window.cancelAISelection=()=>{selecting=false;mode='move';paint();};
 window.clearAIRegion=()=>{regions.delete(state.run?.id);mode='full';selecting=false;paint();};
 $('ai-region-clear').onclick=window.clearAIRegion;
 document.addEventListener('keydown',e=>{if(e.key==='Escape'){selecting=false;paint();}});
 syncAIUI();
})();
