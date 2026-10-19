
'use strict';
const aiState={tasks:new Map(),messages:new Map(),models:[],polling:false,applying:new Set(),dismissed:new Set(),collapsed:false,restoring:new Set(),restored:new Set()};
const aiPending=job=>!!job&&['queued','running','submitting'].includes(job.status);
window.syncAIUI=()=>{
  const available=!live.view&&!!state.run&&!state.design?.kind;
  const pending=aiPending(aiState.tasks.get(state.run?.id));
  $('ai-options').hidden=!available;
  $('ai-analyze').hidden=false;
  $('ai-model').disabled=$('ai-effort').disabled=$('ai-speed').disabled=pending;
  $('ai-analyze').disabled=!available||state.busy||pending||!aiState.models.length;
  $('ai-analyze').textContent='✦ 全图分析';
  const message=available?aiState.messages.get(state.run.id):null;
  $('ai-notice').hidden=!message||pending;$('ai-notice').textContent=message||'';
  window.syncAIRegion?.(available,pending);
  paintAIProgress();renderAITasks();
};
function aiNotice(id,message){
  aiState.messages.set(id,message);syncAIUI();
  setTimeout(()=>{if(aiState.messages.get(id)===message){aiState.messages.delete(id);syncAIUI();}},3000);
}
function adoptAIRun(run){
  state.runs=state.runs.filter(r=>r.id!==run.id);state.runs.push(run);
  state.runs.sort((a,b)=>b.created_at.localeCompare(a.created_at));
  if(state.run?.id===run.id){
    state.run=run;state.dirty=false;state.saveError='';
    if(!run.issues.some(i=>i.id===state.selected))state.selected=run.issues[0]?.id||null;
    rememberSelection();render();
  }else renderSlides();
}
async function startAIAnalysis(region=null,referenceRegion=null){
  if(state.busy||live.view||!state.run||aiPending(aiState.tasks.get(state.run.id)))return;
  const id=state.run.id,model=$('ai-model').value,effort=$('ai-effort').value,speed=$('ai-speed').value;
  aiState.dismissed.delete(id);
  aiState.tasks.set(id,{run_id:id,title:state.design?.name||state.run.title,status:'submitting',stage:'preparing',started_at:new Date().toISOString(),model});
  // Block editing only during the short save/reset request, not during analysis.
  state.busy=true;updateButtons();
  let job;
  try{
    await persist();
    const response=await api('/api/runs/'+id+'/ai',{model,effort,speed,region,reference_region:referenceRegion});
    const {run,...status}=response;job=status;aiState.tasks.set(id,job);
    adoptAIRun(run||await api('/api/runs/'+id));
  }catch(error){
    try{
      // A lost POST response must not roll back an analysis that actually started.
      const status=await api('/api/runs/'+id+'/ai');let run=await api('/api/runs/'+id);
      if((aiPending(status)||status.status==='done')&&run.ai_reanalysis?.attempt_id===status.attempt_id){job=status;aiState.tasks.set(id,status);adoptAIRun(run);}
      else{
        if(run.ai_reanalysis)run=await api('/api/runs/'+id+'/ai-restore',{attempt_id:run.ai_reanalysis.attempt_id});
        adoptAIRun(run);aiState.tasks.set(id,{...aiState.tasks.get(id),status:'error',error:error.message});aiNotice(id,error.message);
      }
    }catch(_){aiState.tasks.set(id,{...aiState.tasks.get(id),status:'error',error:error.message});aiNotice(id,error.message);}
  }finally{state.busy=false;updateButtons();}
  if(job?.status==='done')await applyAIResult(job);
}
$('ai-analyze').onclick=()=>window.chooseAIWhole?.();
$('ai-full-run').onclick=()=>startAIAnalysis();
async function restoreAIResult(job){
  const attempt=job.attempt_id,id=job.run_id;
  if(!job.replaces_ai||!attempt||aiState.restoring.has(attempt)||aiState.restored.has(attempt))return;
  const current=state.run?.id===id;
  if(state.busy)return;
  aiState.restoring.add(attempt);
  state.busy=true;updateButtons();
  try{
    if(current)await persist();
    const run=await api('/api/runs/'+id+'/ai-restore',{attempt_id:attempt});
    adoptAIRun(run);aiState.restored.add(attempt);
    aiNotice(id,job.same_screen===false?(job.summary||'页面不匹配，已恢复上一轮标注'):(job.error||'分析失败，已恢复上一轮标注'));
  }catch(error){aiNotice(id,error.message);}
  finally{aiState.restoring.delete(attempt);state.busy=false;updateButtons();}
}
async function applyAIResult(job){
  const id=job.run_id;
  if(state.busy||state.run?.id!==id||live.view||aiState.applying.has(id))return;
  if(job.replaces_ai){
    if(state.run.ai_result_attempt===job.attempt_id&&!state.run.ai_reanalysis)return;
    if(state.run.ai_reanalysis?.attempt_id!==job.attempt_id)return;
  }
  if(!job.same_screen){await restoreAIResult(job);return;}
  aiState.applying.add(id);state.busy=true;updateButtons();
  try{
    const ids=new Set([...(state.run.ai_applied_ids||[]),...state.run.issues.map(issue=>issue.id)]);
    const added=job.issues.filter(issue=>!ids.has(issue.id)).slice(0,Math.max(0,300-state.run.issues.length));
    const applied=[...new Set([...(state.run.ai_applied_ids||[]),...added.map(issue=>issue.id)])];
    if(JSON.stringify(applied)!==JSON.stringify(state.run.ai_applied_ids||[])){state.run.ai_applied_ids=applied;markDirty();}
    if(added.length){state.run.issues.push(...added);state.selected=added[0].id;rememberSelection();markDirty();renderPins();fillBubble();}
    if(job.replaces_ai){state.run.ai_result_attempt=job.attempt_id;markDirty();}
    await persist();
    if(state.run?.id===id&&!live.view)flashAIResults(added);
    aiNotice(id,`分析完成 · 共 ${job.issues.length} 条建议`+(aiElapsed(job)?` · 分析用时 ${aiElapsed(job)}`:''));
  }catch(error){aiNotice(id,error.message);}
  finally{aiState.applying.delete(id);state.busy=false;updateButtons();}
}
async function pollAITasks(){
  if(aiState.polling)return;aiState.polling=true;
  try{
    const result=await api('/api/ai/jobs');
    for(const job of result.jobs){
      const previous=aiState.tasks.get(job.run_id);aiState.tasks.set(job.run_id,job);
      const uncommitted=state.run?.id===job.run_id&&state.run.ai_reanalysis?.attempt_id===job.attempt_id;
      if(job.status==='done'&&(aiPending(previous)||uncommitted))await applyAIResult(job);
      if(job.status==='error')await restoreAIResult(job);
    }
    syncAIUI();
  }catch(error){/* Keep task cards on transient connection failures; retry next poll. */}
  finally{aiState.polling=false;}
}
function renderAITasks(){
  const dock=$('ai-task-dock');if(!dock)return;
  const tasks=[...aiState.tasks.values()].filter(j=>!aiState.dismissed.has(j.run_id));
  dock.hidden=!tasks.length;
  const active=tasks.filter(aiPending).length;
  $('ai-task-toggle').textContent=`✦ AI 任务 · ${active?active+' 个进行中':tasks.length+' 个已结束'} ${aiState.collapsed?'⌃':'⌄'}`;
  $('ai-task-toggle').setAttribute('aria-expanded',String(!aiState.collapsed));
  const list=$('ai-task-list');list.hidden=aiState.collapsed;
  // Preserve focused task controls while polling.
  const key=JSON.stringify(tasks.map(j=>[j.run_id,j.status,j.stage,j.finished_at,j.error,j.title,j.completed_regions?.length,j.issues?.length,state.runs.find(r=>r.id===j.run_id)?.created_at]));
  if(list.dataset.key===key)return;list.dataset.key=key;list.replaceChildren();
  for(const job of tasks){
    const row=document.createElement('div');row.className='ai-task-row';
    const button=document.createElement('button');button.className='ai-task-link';
    const title=document.createElement('strong');const record=state.runs.find(r=>r.id===job.run_id);
    const time=record?.created_at?new Date(record.created_at).toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit'}):'';
    title.textContent=(job.title||record?.title||'截图')+(time?' · '+time:'');
    const detail=document.createElement('small');
    detail.textContent=job.status==='done'?(job.same_screen?`已完成 · ${job.issues.length} 条建议 · ${aiElapsed(job)}`:'页面不匹配'):job.status==='error'?'分析失败 · '+job.error:job.status==='queued'?'排队中 · 最多 3 个同时分析':job.stage==='adjudicating'?'复核业务状态与样式证据':'分析中 · '+(job.model||'Codex');
    if(job.metrics)button.title=`图像准备 ${job.metrics.prepare_seconds??'—'}s · Codex 请求 ${job.metrics.codex_seconds??'—'}s · 重试 ${job.metrics.retry_count??0} 次 · ${job.metrics.image_count??'—'} 张图`;
    button.append(title,detail);button.onclick=()=>busy(async()=>{await openRun(job.run_id);if(job.status==='done')await applyAIResult(job);});row.append(button);
    if(!aiPending(job)){const close=document.createElement('button');close.className='ai-task-dismiss';close.textContent='×';close.setAttribute('aria-label','收起任务 '+title.textContent);close.onclick=()=>{aiState.dismissed.add(job.run_id);renderAITasks();};row.append(close);}
    list.append(row);
  }
}
const aiDock=document.createElement('aside');aiDock.id='ai-task-dock';aiDock.hidden=true;aiDock.setAttribute('aria-label','AI 后台任务');
aiDock.innerHTML='<button id="ai-task-toggle" aria-expanded="true"></button><div id="ai-task-list"></div>';document.body.append(aiDock);
$('ai-task-toggle').onclick=()=>{aiState.collapsed=!aiState.collapsed;renderAITasks();};
initAIProgress();syncAIUI();setInterval(pollAITasks,1800);pollAITasks();

function fillAIEfforts(){
  const model=aiState.models.find(m=>m.id===$('ai-model').value);
  const saved=localStorage.getItem('review-ai-effort');
  const labels={low:'低',medium:'中',high:'高',xhigh:'更高',max:'最高',ultra:'Ultra'};
  $('ai-effort').replaceChildren(...(model?.efforts||[]).map(v=>new Option('深度 · '+(labels[v]||v),v)));
  $('ai-effort').value=model?.efforts.includes(saved)?saved:model?.default_effort||'';
  if(localStorage.getItem('review-ai-speed-default')!=='fast-v1'){
    localStorage.setItem('review-ai-speed','fast');
    localStorage.setItem('review-ai-speed-default','fast-v1');
  }
  const speed=localStorage.getItem('review-ai-speed')||'fast';
  $('ai-speed').replaceChildren(...(model?.speeds||['standard']).map(s=>new Option(s==='fast'?'加速 · 更多额度':'标准速度',s)));
  $('ai-speed').value=model?.speeds?.includes(speed)?speed:'standard';
}
$('ai-model').onchange=()=>{localStorage.setItem('review-ai-model',$('ai-model').value);fillAIEfforts();};
$('ai-speed').onchange=()=>localStorage.setItem('review-ai-speed',$('ai-speed').value);
$('ai-effort').onchange=()=>localStorage.setItem('review-ai-effort',$('ai-effort').value);
api('/api/ai/models').then(result=>{
  aiState.models=result.models;
  $('ai-model').replaceChildren(...result.models.map(m=>new Option(m.name,m.id)));
  const saved=localStorage.getItem('review-ai-model');
  if(result.models.some(m=>m.id===saved))$('ai-model').value=saved;
  fillAIEfforts();syncAIUI();
}).catch(()=>{$('ai-analyze').title='无法读取本机模型列表，请刷新重试';});

function initAIProgress(){
  for(const id of ['reference-surface','shot-surface']){
    const overlay=document.createElement('div');overlay.className='ai-canvas-progress';overlay.hidden=true;
    overlay.setAttribute('aria-hidden','true');
    const label=document.createElement('span');label.className='ai-canvas-label';overlay.append(label);
    const regions=document.createElement('div');regions.className='ai-motion-regions';overlay.append(regions);
    $(id).append(overlay);
  }
  setInterval(()=>{paintAIProgress();renderAITasks();},1000);
}
function paintAIProgress(){
  const job=aiState.tasks.get(state.run?.id);
  const active=aiPending(job)&&!live.view;
  const stage=job?.stage||'preparing';
  const labels={queued:'等待分析空位',preparing:'准备组件与环境',comparing:job?.region?'选区组件对比':'分区组件比对',adjudicating:'业务与样式复核',validating:'校验候选坐标',applying:'保存问题标注'};
  const seconds=Math.max(0,Math.floor((Date.now()-Date.parse(job?.started_at||new Date()))/1000));
  for(const overlay of document.querySelectorAll('.ai-canvas-progress')){
    overlay.hidden=!active;
    overlay.dataset.stage=stage;
    overlay.querySelector('span').textContent=`✦ ${labels[stage]||'整理分析结果'}${stage==='comparing'&&job?.completed_regions?.length?' · '+job.completed_regions.length+'/3':''} · ${seconds}s`;
    const side=overlay.parentElement.id==='reference-surface'?'reference':'capture';
    const regions=aiMotionRegions(job,side),signature=JSON.stringify(regions),layer=overlay.querySelector('.ai-motion-regions');
    if(layer.dataset.signature!==signature){layer.dataset.signature=signature;layer.replaceChildren();for(const region of regions){const box=document.createElement('div');box.className='ai-motion-region';box.dataset.state=region.state;box.dataset.kind=region.kind;box.style.cssText=`--scan-delay:${region.delay||0}s;left:${region.x*100}%;top:${region.y*100}%;width:${region.width*100}%;height:${region.height*100}%`;const label=document.createElement('span');label.textContent=region.label;box.append(label);layer.append(box);}}
  }
}
function aiMotionRegions(job,side){
  if(!job||!aiPending(job)||job.stage==='queued')return [];
  const selected=side==='reference'?job.reference_region:job.region;
  const rect={...(selected||{x:0,y:0,width:1,height:1}),kind:selected?'local':'area'};
  if(job.stage!=='comparing')return [{...rect,state:job.stage==='preparing'?'locating':'reviewing',label:job.stage==='preparing'?'定位可比区域':job.stage==='adjudicating'?'复核差异':'整理结果'}];
  if(job.region)return [{...rect,state:'scanning',label:'选区比对中'}];
  const done=new Set(job.completed_regions||[]);
  return [['header',0,.36,'顶部'],['content',.30,.56,'内容'],['navigation',.82,.18,'底部']].map(([id,y,height,name])=>({x:0,y,width:1,height,kind:'area',delay:-y*3,state:done.has(id)?'done':'scanning',label:name+(done.has(id)?' · 已比对':' · 比对中')}));
}
function flashAIResults(issues){
  for(const issue of issues){
    const halo=document.createElement('span');halo.className='ai-result-halo';
    halo.style.left=(issue.rect.x/state.run.image_size[0]*100)+'%';
    halo.style.top=(issue.rect.y/state.run.image_size[1]*100)+'%';
    $('shot-surface').append(halo);setTimeout(()=>halo.remove(),2400);
  }
}

function aiElapsed(job){
  const duration=Date.parse(job.finished_at)-Date.parse(job.started_at);
  if(!Number.isFinite(duration)||duration<0)return '';
  const seconds=Math.max(1,Math.ceil(duration/1000));
  const minutes=Math.floor(seconds/60),remaining=seconds%60;
  return minutes?`${minutes} 分${remaining?` ${remaining} 秒`:''}`:`${seconds} 秒`;
}
