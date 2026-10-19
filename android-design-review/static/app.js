'use strict';
const $=id=>document.getElementById(id);
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const state={source:'physical',token:'',catalog:null,projects:[],projectPreview:null,projectJob:null,projectInspecting:false,designs:[],runs:[],devices:[],design:null,nodes:[],run:null,selected:null,busy:false,dirty:false,edit:0,saveError:'',selections:new Map()};
const live={view:true,playing:false,session:null,frame:null,epoch:0,timer:null,error:'',samples:[],lastPresented:0};
let toastTimer,saveTimer,savePromise=null,slideSignature='',resumeOnVisible=false;
const bubbles=new Map();let bubbleRun=null,bubbleMeasure=null;
const dateLabel=value=>new Date(value).toLocaleString('zh-CN',{timeZone:'Asia/Shanghai',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false});
function userMessage(message){return String(message);}
function toast(message,error=false){$('toast').textContent=userMessage(message);$('toast').classList.toggle('error',error);$('toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').hidden=true,error?8000:3000);}
async function api(path,body,retrySession=true){let response;try{response=await fetch(path,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json','X-Review-Token':state.token},body:JSON.stringify(body)});}catch(_){throw Error('本地服务连接已中断，请重新打开「设计验收」客户端。');}let data;try{data=await response.json();}catch(_){throw Error(response.ok?'服务返回了无法识别的数据。':`请求失败（${response.status}）`);}if(response.status===403&&body!==undefined&&retrySession&&data.error==='会话已失效，请刷新工作台'){const session=await api('/api/bootstrap');state.token=session.token;return api(path,body,false);}if(!response.ok)throw Error(data.error||'请求失败');return data;}
async function busy(action){if(state.busy||state.switching)return;state.busy=true;updateButtons();try{return await action();}catch(error){toast(error.message,true);}finally{state.busy=false;updateButtons();}}
function currentDesignRuns(){return state.runs.filter(run=>run.design_id===state.design?.id);}
function ready(){return state.devices.some(d=>d.id===$('device').value&&d.state==='device');}
function rememberCaptureSource(){localStorage.setItem('review-capture-source',JSON.stringify({source:state.source,device:state.captureDevice||$('device').value}));}
function rememberLocation(){if(!state.catalog||!state.design)return;localStorage.setItem('review-design-'+state.catalog.id,state.design.id);localStorage.setItem('review-location-'+state.catalog.id,JSON.stringify({design:state.design.id,run:state.run?.design_id===state.design.id?state.run.id:null}));}
function restoreCaptureSource(){try{const saved=JSON.parse(localStorage.getItem('review-capture-source'));if(saved&&['physical','virtual'].includes(saved.source)){state.source=saved.source;state.captureDevice=saved.device||'';}}catch(_){}}
restoreCaptureSource();
function updateButtons(){
  const raster=!!state.design&&!state.design.kind,choices=navigationChoices(),position=choices.findIndex(d=>d.id===state.design?.id);
  $('live-toggle').disabled=(state.busy||state.switching)||!state.design;$('review-toggle').disabled=(state.busy||state.switching)||(!state.run&&!currentDesignRuns().length);
  for(const [id,selected] of [['live-toggle',live.view&&state.source==='physical'],['virtual-toggle',live.view&&state.source==='virtual'],['review-toggle',!live.view]]){$(id).classList.toggle('active',selected);$(id).setAttribute('aria-pressed',String(selected));}
  $('capture').disabled=(state.busy||state.switching)||!raster||!ready();$('capture').textContent=(state.busy||state.switching)?'处理中…':'截图';
  $('capture').title=!ready()?'请连接并授权安卓设备':'采集手机当前画面，新增一条截图记录';
  $('connect-preview').disabled=(state.busy||state.switching)||live.playing;$('connect-preview').textContent=live.playing?'连接中…':live.error?'重新连接':'连接设备';
  $('export').disabled=(state.busy||state.switching)||live.view||!state.run;$('live-pause').disabled=(state.busy||state.switching);$('live-pause').hidden=!live.view;$('live-pause').textContent=(live.playing||state.switching)?'暂停':live.error?'重新连接':'继续预览';
  for(const id of ['refresh-devices','design','demo','import-design','project-select','add-project','open-settings'])$(id).disabled=(state.busy||state.switching);
  $('inspect-project').disabled=(state.busy||state.switching)||state.projectInspecting||!!state.projectJob||!$('project-url').value.trim();
  $('inspect-project').textContent=state.projectInspecting?'检查中…':'检查';
  $('inspect-project').classList.toggle('is-loading',state.projectInspecting);
  $('associate-project').disabled=(state.busy||state.switching)||!!state.projectJob||!state.projectPreview;
  $('associate-project').textContent=state.projectJob?'正在同步…':'同步项目';
  $('device').disabled=(state.busy||state.switching)||live.playing;
  $('upload').disabled=(state.busy||state.switching)||!raster;
  document.querySelectorAll('.pin-bubble textarea,.pin-bubble button').forEach(element=>element.disabled=(state.busy||state.switching));
  document.querySelectorAll('[data-run],.pin,[data-design-key],[data-group]').forEach(button=>button.disabled=(state.busy||state.switching));
  $('save-warning').hidden=!state.saveError;
  $('save-warning-text').textContent=state.saveError?'标注尚未保存，请保留当前页面。'+state.saveError:'';
  $('retry-save').disabled=(state.busy||state.switching)||!!savePromise;
  window.syncVirtualUI?.();
  window.syncAIUI?.();
}
async function bootstrap(preferredProject){const b=await api('/api/bootstrap');state.token=b.token;state.projects=b.projects||(b.catalog?[b.catalog]:[]);state.designs=b.designs;state.runs=b.runs;const wanted=preferredProject||state.catalog?.id||localStorage.getItem('review-project');state.catalog=state.projects.find(p=>p.id===wanted)||state.projects[0]||null;if(state.catalog)localStorage.setItem('review-project',state.catalog.id);populateDesignChoices();renderSlides();}
function projectForDesign(key){return state.projects.find(project=>project.items.some(item=>item.design_key===key));}
function setCatalog(project){state.catalog=project;localStorage.setItem('review-project',project.id);populateDesignChoices();}
async function refreshDevices(){const old=state.captureDevice||$('device').value,info=await api('/api/devices');info.devices=info.devices.filter(d=>state.source==='virtual'?d.id===(window.virtualSerial?.()||state.captureDevice):d.kind!=='emulator');state.devices=info.devices;$('device').innerHTML=info.devices.length?info.devices.map(d=>`<option value="${esc(d.id)}">${esc(d.name)} · ${d.kind==='emulator'?'模拟器':'USB'}${d.state==='device'?'':' · '+esc(d.state)}</option>`).join(''):'<option value="">未发现设备</option>';if(info.devices.some(d=>d.id===old))$('device').value=old;else if(!old&&info.devices.some(d=>d.state==='device'))$('device').value=info.devices.find(d=>d.state==='device').id;else $('device').value='';displayDevice(info);updateButtons();}
function displayDevice(info={available:true}){const d=state.devices.find(d=>d.id===$('device').value);$('device-title').textContent=d?.name||(info.available?'连接设备':'ADB 未安装');$('device-subtitle').textContent=ready()?'设备已连接':d?.state==='unauthorized'?'请在手机上允许 USB 调试':'模拟器 / USB 真机';$('device-dot').classList.toggle('online',ready());$('device-help').textContent=ready()?'实时同步整台手机画面，可在手机上自由切换页面和应用。':'连接并解锁手机，允许 USB 调试后刷新。';}
function markDirty(){state.dirty=true;state.edit++;updateButtons();renderSlides();clearTimeout(saveTimer);saveTimer=setTimeout(()=>persist().catch(error=>toast(error.message,true)),700);}
async function persist(){
  clearTimeout(saveTimer);if(savePromise)return savePromise;if(!state.run||!state.dirty)return;
  // Serialize saves. Typing during an in-flight save is sent in the next revision.
  savePromise=(async()=>{while(state.run&&state.dirty){const run=state.run,edit=state.edit;const body=JSON.parse(JSON.stringify({revision:run.revision,calibration:run.calibration,threshold:run.threshold,issues:run.issues,ai_applied_ids:run.ai_applied_ids||[],ai_result_attempt:run.ai_result_attempt||'',exclusions:run.exclusions,title:run.title}));const result=await api('/api/runs/'+run.id,body);if(state.run?.id!==run.id)throw Error('记录已切换，保存状态需要重新确认。');state.run.revision=result.revision;state.run.updated_at=result.updated_at;state.run.ai_reanalysis=result.ai_reanalysis;state.run.ai_result_attempt=result.ai_result_attempt;state.dirty=state.edit!==edit;state.saveError='';rememberRun();}})();updateButtons();
  try{await savePromise;}catch(error){state.saveError=error.message;throw error;}finally{savePromise=null;updateButtons();}
}
function rememberRun(){if(!state.run)return;state.runs=state.runs.filter(r=>r.id!==state.run.id);state.runs.push(state.run);state.runs.sort((a,b)=>b.created_at.localeCompare(a.created_at));renderSlides();}
function rememberSelection(){if(state.run)state.selections.set(state.run.id,state.selected);}
function inferCaptureSource(run){if(localStorage.getItem('review-capture-source'))return;const device=run.capture?.device;if(!device?.id)return;state.source=device.kind==='emulator'?'virtual':'physical';state.captureDevice=device.id;rememberCaptureSource();}
async function openRun(key){await persist();const run=await api('/api/runs/'+encodeURIComponent(key)),project=projectForDesign(run.design_id);if(project&&project.id!==state.catalog?.id)setCatalog(project);await loadDesign(run.design_id);inferCaptureSource(run);rememberSelection();leaveLive();state.run=run;state.dirty=false;state.saveError='';state.selected=state.selections.has(key)?state.selections.get(key):run.issues[0]?.id||null;rememberLocation();history.replaceState(null,'','#run='+run.id);render();revealSlide();}
async function selectDesign(key){if(key===state.design?.id)return;await persist();rememberSelection();const latest=state.runs.find(r=>r.design_id===key);const run=latest?await api('/api/runs/'+latest.id):null;await loadDesign(key);if(state.catalog)localStorage.setItem('review-design-'+state.catalog.id,key);state.run=run;state.dirty=false;state.saveError='';state.selected=run?(state.selections.has(run.id)?state.selections.get(run.id):run.issues[0]?.id||null):null;rememberLocation();history.replaceState(null,'',run?'#run='+run.id:'#design='+encodeURIComponent(key));if(!live.view&&!run){live.view=true;render();if(ready())await startLive();}else render();revealSlide();}
async function selectProject(key){
  const project=state.projects.find(item=>item.id===key),previous=state.catalog,previousDesign=state.design?.id;
  if(!project||project.id===previous?.id)return;
  try{
    await persist();rememberSelection();rememberLocation();setCatalog(project);
    const remembered=localStorage.getItem('review-design-'+project.id),choices=designChoices().filter(item=>!item.extra),target=choices.find(item=>item.id===remembered)||choices.find(item=>item.kind==='design')||choices[0];
    let saved;try{saved=JSON.parse(localStorage.getItem('review-location-'+project.id));}catch(_){}
    if(target){const record=state.runs.find(r=>r.id===saved?.run&&r.design_id===target.id);if(record)await openRun(record.id);else await selectDesign(target.id);}
    $('design-search').value='';renderDesignBrowser();$('design-grid').scrollTop=0;
  }catch(error){if(previous&&state.design?.id===previousDesign){setCatalog(previous);$('design').value=previousDesign;}renderDesignBrowser();throw error;}
}
async function acceptRun(run){
  // Prepare the new scene before committing it; a failed image/design request must
  // not pair the old rendered annotations with a newly assigned record.
  const image=new Image();image.src=run.original_url;await image.decode();
  await loadDesign(run.design_id);rememberSelection();leaveLive();
  bubbles.clear();bubbleRun=null;$('bubble-layer').replaceChildren();$('pin-layer').replaceChildren();$('bubble-lines').replaceChildren();
  state.run=run;state.dirty=false;state.saveError='';state.selected=null;
  rememberRun();rememberLocation();history.replaceState(null,'','#run='+run.id);$('settings-dialog').close();render();revealSlide();
}
function render(){if(state.switching){updateButtons();return;}if(!state.design)return;rememberLocation();const d=state.design;$('reference-meta').textContent=d.kind?'交互说明':'固定原稿';$('reference-caption').textContent=d.name;$('reference-image').hidden=!!d.kind;$('reference-note').hidden=!d.kind;if(d.kind)$('reference-note').innerHTML=sourceNote();else setImage($('reference-image'),`/files/designs/${d.id}/reference.png`);$('open-original').hidden=live.view||!state.run;if(state.run)$('open-original').href=state.run.original_url;renderViewer();renderSlides();fillBubble();renderStatus();updateButtons();}
function setImage(image,src){if(image.getAttribute('src')!==src)image.src=src;}
function renderViewer(){
  // Keep the previous frame and geometry until a device switch has a decoded frame.
  if(state.switching)return;
  if(!state.design)return;const c=state.design.canvas||{width:375,height:812},size=live.view?(live.frame?.image_size||[1080,2412]):state.run?.image_size||[1080,2412];
  syncAnnotationPane();
  const left=$('reference-body'),right=$('device-body');
  const usable=element=>{const css=getComputedStyle(element);return{width:element.clientWidth-parseFloat(css.paddingLeft)-parseFloat(css.paddingRight),height:element.clientHeight-parseFloat(css.paddingTop)-parseFloat(css.paddingBottom)};};
  const a=usable(left),b=usable(right);
  const runtime=live.view?(state.source==='virtual'?window.virtualRuntime?.():null):state.run?.capture?.review_context?.runtime;
  const captured=state.run?.capture;
  const rawDensity=!live.view?captured?.display_density:null;
  const densities=rawDensity?.match(/density:\s*(\d+)/g),density=runtime?.density||(densities?.length?Number(densities.at(-1).match(/\d+/)[0]):null);
  const nativeWidth=runtime?.profile?.width||(!live.view?size[0]:null);
  const deviceWidth=density&&nativeWidth?nativeWidth*160/density:null;
  const logicalWidth=deviceWidth||c.width,logicalHeight=runtime?.profile?.height&&deviceWidth?runtime.profile.height*160/density:logicalWidth*size[1]/size[0];
  const zoom=Math.max(.001,Math.min(900/Math.max(c.height,logicalHeight),a.height/c.height,b.height/logicalHeight,a.width/c.width,b.width/logicalWidth));
  const refWidth=c.width*zoom,refHeight=c.height*zoom,shotWidth=logicalWidth*zoom,shotHeight=logicalHeight*zoom;
  $('annotation-pane').style.transform=`translateX(${-Math.max(0,b.width-shotWidth)}px)`;
  $('reference-pane').style.setProperty('--picture-width',`${refWidth}px`);$('device-pane').style.setProperty('--picture-width',`${shotWidth}px`);
  $('reference-surface').style.cssText=`width:${refWidth}px;height:${refHeight}px`;$('shot-surface').style.cssText=`width:${shotWidth}px;height:${shotHeight}px`;
  $('reference-meta').textContent=deviceWidth?'统一逻辑缩放':'等宽对照 · 密度未知';
  $('reference-meta').title=deviceWidth?`原稿 ${c.width} × ${c.height} 设计单位；设备 ${logicalWidth.toFixed(2)} × ${logicalHeight.toFixed(2)} dp。按 1 设计单位对应 1 dp 展示。`:'缺少设备密度，暂按同宽展示，不能据此判定绝对控件尺寸。';
  const src=live.view?live.frame?.preview_url:state.run?.original_url;$('phone-image').hidden=!src;$('phone-placeholder').hidden=!!src;if(src)setImage($('phone-image'),src);$('phone-image').alt=live.view?'手机实时预览':'当前截图，可点击打点标注';
  if(!src){$('phone-placeholder').querySelector('strong').textContent=live.playing?'正在连接手机…':'等待手机画面';$('phone-placeholder').querySelector('small').textContent=live.error||(state.source==='virtual'?'点击「虚拟机」上传开发包并选择设备。':'保持手机解锁，点击「实机」同步当前屏幕。');}
  $('pin-layer').hidden=live.view||!state.run;renderPins();fillBubble();
}
function issuePosition(issue){const r=issue.rect;if(issue.coordinate_space==='image')return {x:r.x,y:r.y,width:r.width,height:r.height};const c=state.run.calibration,scale=state.design.canvas.width*c.scale_percent/100/state.run.image_size[0];return{x:(r.x-c.offset_x)/scale,y:(r.y-c.offset_y)/scale,width:r.width/scale,height:r.height/scale};}
function orderedIssues(){return state.run.issues.sort((a,b)=>{const pa=issuePosition(a),pb=issuePosition(b);return pa.y-pb.y||pa.x-pb.x;});}
function renderPins(){
  const layer=$('pin-layer');if(state.capturing||live.view||!state.run){layer.innerHTML='';fillBubble();return;}
  const [w,h]=state.run.image_size;
  layer.innerHTML=orderedIssues().map((issue,index)=>{const p=issuePosition(issue),x=p.x/w*100,y=p.y/h*100;return `${issue.annotation_type==='point'?'':`<div class="legacy-box" data-box="${esc(issue.id)}" style="left:${x}%;top:${y}%;width:${p.width/w*100}%;height:${p.height/h*100}%"></div>`}<button class="pin ${issue.review_kind==='state_hint'?'state-hint':''} ${state.selected===issue.id?'active':''}" data-pin="${esc(issue.id)}" aria-label="问题 ${index+1}：${esc(issue.title)}" title="拖动调整标记位置" style="left:${x}%;top:${y}%">${index+1}</button>`;}).join('');
  layer.querySelectorAll('[data-pin]').forEach(button=>{
    const issue=state.run.issues.find(item=>item.id===button.dataset.pin);
    const activate=()=>{state.selected=issue.id;rememberSelection();layer.querySelectorAll('.pin').forEach(pin=>pin.classList.toggle('active',pin===button));fillBubble();bubbles.get(issue.id)?.scrollIntoView({block:'nearest',behavior:'smooth'});};
    button.onpointerenter=()=>{hoveredIssue=issue.id;positionBubble();};
    button.onpointerleave=()=>{hoveredIssue=null;positionBubble();};
    button.onclick=event=>{event.stopPropagation();if(!state.busy)activate();};
    button.onpointerdown=event=>{
      if(state.busy||event.button!==0)return;
      event.preventDefault();event.stopPropagation();activate();button.focus();
      const start={x:event.clientX,y:event.clientY,point:issuePosition(issue),rect:{...issue.rect}},bounds=$('shot-surface').getBoundingClientRect();
      let moved=false;button.classList.add('dragging');button.setPointerCapture(event.pointerId);
      button.onpointermove=move=>{const dx=move.clientX-start.x,dy=move.clientY-start.y;if(!moved&&Math.hypot(dx,dy)<3)return;moved=true;movePin(issue,start.point.x+dx/bounds.width*w,start.point.y+dy/bounds.height*h,button);};
      const finish=cancel=>{button.onpointermove=null;button.onpointerup=null;button.onpointercancel=null;button.onlostpointercapture=null;button.classList.remove('dragging');if(button.hasPointerCapture(event.pointerId))button.releasePointerCapture(event.pointerId);if(moved){if(cancel){issue.rect=start.rect;paintPin(issue,button);}else markDirty();}};
      button.onpointerup=()=>finish(false);button.onpointercancel=()=>finish(true);button.onlostpointercapture=()=>finish(false);
    };
    button.onkeydown=event=>{const delta={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]}[event.key];if(!delta||state.busy)return;event.preventDefault();event.stopPropagation();activate();const p=issuePosition(issue),surface=$('shot-surface'),step=event.shiftKey?10:1;movePin(issue,p.x+delta[0]*step*w/surface.clientWidth,p.y+delta[1]*step*h/surface.clientHeight,button);markDirty();};
  });
}
function movePin(issue,x,y,button){
  const [w,h]=state.run.image_size;let width=w,height=h;
  if(issue.coordinate_space!=='image'){const c=state.run.calibration,scale=state.design.canvas.width*c.scale_percent/100/w;x=x*scale+c.offset_x;y=y*scale+c.offset_y;width=state.design.canvas.width;height=state.design.canvas.height;}
  issue.rect.x=Math.max(0,Math.min(width-issue.rect.width,x));issue.rect.y=Math.max(0,Math.min(height-issue.rect.height,y));
  paintPin(issue,button);
}
function paintPin(issue,button){
  const p=issuePosition(issue),[w,h]=state.run.image_size;
  button.style.left=p.x/w*100+'%';button.style.top=p.y/h*100+'%';
  const box=[...$('pin-layer').querySelectorAll('[data-box]')].find(item=>item.dataset.box===issue.id);if(box){box.style.left=button.style.left;box.style.top=button.style.top;}
  positionBubble();
}
function addPin(clientX,clientY){if(!window.manualAnnotationEnabled||live.view||!state.run||state.busy)return;const bounds=$('shot-surface').getBoundingClientRect(),[w,h]=state.run.image_size;const x=Math.max(0,Math.min(w-1,(clientX-bounds.left)/bounds.width*w)),y=Math.max(0,Math.min(h-1,(clientY-bounds.top)/bounds.height*h));const issue={id:crypto.randomUUID(),annotation_type:'point',coordinate_space:'image',rect:{x:+x.toFixed(2),y:+y.toFixed(2),width:1,height:1},title:'待填写的问题',note:'',priority:'P2',status:'待确认',node_id:'',node_label:''};state.run.issues.push(issue);state.selected=issue.id;rememberSelection();markDirty();renderViewer();bubbles.get(issue.id)?.querySelector('textarea').focus();}
// Keep each editor mounted while typing, saving, selecting pins, or resizing.
function selectPin(id){state.selected=id;rememberSelection();renderPins();fillBubble();}
let bubbleTextMirror;
let hoveredIssue=null;
function fitBubbleText(input){
  if(input.dataset.composing==='true')return;
  const style=getComputedStyle(input),bubble=input.closest('.pin-bubble');
  bubble.style.width='100%';
  if(!bubbleTextMirror){bubbleTextMirror=document.createElement('div');bubbleTextMirror.setAttribute('aria-hidden','true');document.body.append(bubbleTextMirror);}
  Object.assign(bubbleTextMirror.style,{position:'fixed',left:'-10000px',top:'0',visibility:'hidden',pointerEvents:'none',boxSizing:'border-box',width:input.clientWidth+'px',font:style.font,letterSpacing:style.letterSpacing,lineHeight:style.lineHeight,padding:style.padding,whiteSpace:'pre-wrap',overflowWrap:'break-word',wordBreak:style.wordBreak});
  bubbleTextMirror.textContent=(input.value||input.placeholder||' ')+(input.value.endsWith('\n')?'\u200b':'');
  const height=Math.max(24,Math.min(180,Math.ceil(bubbleTextMirror.getBoundingClientRect().height)));
  if(input.style.height!==height+'px')input.style.height=height+'px';
  input.style.overflowY=height>=180?'auto':'hidden';
}
function syncAnnotationPane(){const visible=!state.capturing&&!live.view&&!!state.run?.issues.length;$('annotation-pane').hidden=!visible;document.querySelector('.main').classList.toggle('with-annotations',visible);}
function fillBubble(){
  syncAnnotationPane();
  const hidden=state.capturing||live.view||!state.run;
  $('bubble-layer').hidden=hidden;$('bubble-lines').toggleAttribute('hidden',hidden);
  if(hidden){$('bubble-lines').replaceChildren();return;}
  if(bubbleRun!==state.run){bubbles.clear();$('bubble-layer').replaceChildren();bubbleRun=state.run;}
  const ids=new Set(state.run.issues.map(issue=>issue.id));
  for(const [id,bubble] of bubbles)if(!ids.has(id)){bubble.remove();bubbles.delete(id);}
  orderedIssues().forEach((issue,index)=>{
    let bubble=bubbles.get(issue.id);
    if(!bubble){
      bubble=document.createElement('section');bubble.className='pin-bubble';bubble.dataset.issue=issue.id;
      bubble.innerHTML='<button class="bubble-drag" type="button" title="定位标记"></button><textarea rows="1" maxlength="4000" placeholder="描述这里的问题…"></textarea><button class="delete-pin" type="button">删除</button>';
      bubbles.set(issue.id,bubble);$('bubble-layer').append(bubble);
      const input=bubble.querySelector('textarea'),handle=bubble.querySelector('.bubble-drag');
      input.onfocus=()=>selectPin(issue.id);
      input.oninput=()=>{issue.note=input.value;issue.title=issue.note.trim().slice(0,200)||'待填写的问题';fitBubbleText(input);markDirty();const pin=[...$('pin-layer').querySelectorAll('[data-pin]')].find(p=>p.dataset.pin===issue.id);if(pin)pin.setAttribute('aria-label','问题 '+pin.textContent+'：'+issue.title);positionBubble();};
      input.oncompositionstart=()=>{input.dataset.composing='true';};
      input.oncompositionend=()=>{delete input.dataset.composing;fitBubbleText(input);positionBubble();};
      input.onblur=()=>{delete input.dataset.composing;fitBubbleText(input);positionBubble();persist().catch(error=>toast(error.message,true));};
      bubble.querySelector('.delete-pin').onclick=()=>busy(async()=>{state.run.issues=state.run.issues.filter(item=>item.id!==issue.id);if(state.selected===issue.id)state.selected=null;rememberSelection();markDirty();renderViewer();await persist();});
      handle.onclick=()=>selectPin(issue.id);
      bubble.onclick=()=>{if(state.selected!==issue.id)selectPin(issue.id);};
      bubble.onpointerenter=()=>{hoveredIssue=issue.id;positionBubble();};
      bubble.onpointerleave=()=>{hoveredIssue=null;positionBubble();};
    }
    bubble.classList.toggle('active',state.selected===issue.id);
    bubble.classList.toggle('state-hint',issue.review_kind==='state_hint');
    bubble.title=issue.review_kind==='state_hint'?'待核对：可能由页面状态差异引起':'';
    bubble.setAttribute('aria-label',`问题 ${index+1} 气泡`);
    bubble.querySelector('.bubble-drag').setAttribute('aria-label',`定位问题 ${index+1}`);
    bubble.querySelector('.bubble-drag').textContent=index+1;
    bubble.style.order=String(index);
    bubble.querySelector('.delete-pin').setAttribute('aria-label',`删除问题 ${index+1}`);
    const input=bubble.querySelector('textarea');input.setAttribute('aria-label',`问题 ${index+1} 描述`);
    if(document.activeElement!==input)input.value=issue.note||(issue.title==='待填写的问题'?'':issue.title);
    fitBubbleText(input);
  });
  $('annotation-count').textContent=state.run.issues.length;
  positionBubble();updateButtons();
}
function bubbleAnchor(issue){const p=issuePosition(issue),[w,h]=state.run.image_size,surface=$('shot-surface');return{x:surface.offsetLeft+p.x/w*surface.clientWidth,y:surface.offsetTop+p.y/h*surface.clientHeight};}
function clampBubble(bubble,left,top){const body=$('device-body');return{left:Math.max(4,Math.min(left,body.clientWidth-bubble.offsetWidth-4)),top:Math.max(4,Math.min(top,body.clientHeight-bubble.offsetHeight-4))};}
function moveBubble(issue,bubble,left,top){const point=clampBubble(bubble,left,top),anchor=bubbleAnchor(issue),surface=$('shot-surface');issue.bubble_offset={x:(point.left-anchor.x)/surface.clientWidth,y:(point.top-anchor.y)/surface.clientHeight};positionBubble();}
// Keep the numbered marker and an 8px gap clear, even after edge clamping.
function avoidBubbleAnchor(point,anchor,width,height,bounds){
  const gap=20;
  const overlaps=p=>p.left<anchor.x+gap&&p.left+width>anchor.x-gap&&p.top<anchor.y+gap&&p.top+height>anchor.y-gap;
  if(!overlaps(point))return point;
  const clamp=p=>({left:Math.max(4,Math.min(p.left,bounds.width-width-4)),top:Math.max(4,Math.min(p.top,bounds.height-height-4))});
  const candidates=[{left:anchor.x+gap,top:point.top},{left:anchor.x-gap-width,top:point.top},{left:point.left,top:anchor.y+gap},{left:point.left,top:anchor.y-gap-height}].map(clamp).filter(p=>!overlaps(p));
  candidates.sort((a,b)=>Math.hypot(a.left-point.left,a.top-point.top)-Math.hypot(b.left-point.left,b.top-point.top));
  return candidates[0]||{left:point.left,top:anchor.y+gap};
}
function positionBubble(){
  const svg=$('bubble-lines');
  if(live.view||!state.run){svg.replaceChildren();svg.setAttribute('hidden','');return;}
  svg.removeAttribute('hidden');
  const scale=window.reviewZoomScale||1;
  const listElement=$('bubble-layer'),bodyRect=$('device-body').getBoundingClientRect(),listRect=listElement.getBoundingClientRect();
  const items=orderedIssues().map((item,index)=>{
    const card=bubbles.get(item.id);if(!card)return null;
    const number=index+1;
    card.style.order=String(index);
    card.setAttribute('aria-label',`问题 ${number} 气泡`);
    card.querySelector('.bubble-drag').textContent=number;
    card.querySelector('.bubble-drag').setAttribute('aria-label',`定位问题 ${number}`);
    card.querySelector('textarea').setAttribute('aria-label',`问题 ${number} 描述`);
    card.querySelector('.delete-pin').setAttribute('aria-label',`删除问题 ${number}`);
    const pin=[...$('pin-layer').querySelectorAll('[data-pin]')].find(pin=>pin.dataset.pin===item.id);
    if(pin){pin.textContent=number;pin.setAttribute('aria-label',`问题 ${number}：${item.title}`);}
    return {card,height:card.offsetHeight,target:bubbleAnchor(item).y+(bodyRect.top-listRect.top)/scale-card.offsetHeight/2};
  }).filter(Boolean);
  // Fit near the anchor's horizontal level, separating only colliding cards.
  let bottom=4;
  items.forEach(item=>{item.top=Math.max(bottom,item.target);bottom=item.top+item.height+12;});
  const total=items.reduce((sum,item)=>sum+item.height+12,4);
  let ceiling=Math.max(Math.min(listElement.clientHeight-16,$('shot-surface').clientHeight),total-12);
  for(let i=items.length-1;i>=0;i--){const item=items[i];item.top=Math.min(item.top,ceiling-item.height);ceiling=item.top-12;}
  bottom=4;
  items.forEach(item=>{item.card.style.marginTop=Math.max(0,item.top-bottom)+'px';bottom=item.top+item.height+12;});
  const id=hoveredIssue||state.selected,issue=state.run.issues.find(item=>item.id===id),bubble=bubbles.get(id);
  document.querySelectorAll('.pin').forEach(pin=>pin.classList.toggle('linked',pin.dataset.pin===id));
  bubbles.forEach((card,key)=>card.classList.toggle('linked',key===id));
  if(!issue||!bubble){svg.replaceChildren();return;}
  const anchor=bubbleAnchor(issue),body=$('device-body').getBoundingClientRect(),card=bubble.getBoundingClientRect(),list=$('bubble-layer').getBoundingClientRect();
  if(card.bottom<=list.top||card.top>=list.bottom){svg.replaceChildren();return;}
  const endX=(card.left-body.left)/scale,endY=(Math.max(list.top+8*scale,Math.min(list.bottom-8*scale,Math.max(card.top+12*scale,Math.min(card.bottom-12*scale,body.top+anchor.y*scale))))-body.top)/scale;
  svg.innerHTML=`<line class="${issue.review_kind==='state_hint'?'state-hint':''}" x1="${anchor.x}" y1="${anchor.y}" x2="${endX}" y2="${endY}"/>`;
}
$('bubble-layer').addEventListener('scroll',positionBubble);
function renderStatus(){if(state.switching)return;if(live.view){$('view-status').textContent=live.playing?(live.frame?'● 高清实时':'连接中…'):live.error||'预览已暂停';const rate=live.samples.length?(1000/(live.samples.reduce((a,b)=>a+b,0)/live.samples.length)).toFixed(1)+' 帧/秒 · ':'';$('view-detail').textContent=live.frame?rate+live.frame.image_size.join(' × '):'';}else{$('view-status').textContent=window.manualAnnotationEnabled?'点击截图任意位置，添加问题':'选择「手动标注」后点击截图添加问题';$('view-detail').textContent=state.run?[dateLabel(state.run.created_at),state.run.capture?.review_context?.runtime?.width_dp?state.run.capture.review_context.runtime.width_dp+' dp · 字体 '+Math.round(state.run.capture.review_context.runtime.font_scale*100)+'%':''].filter(Boolean).join(' · '):'';}}
function designChoices(){
  const project=(state.catalog?.items||[]).filter(item=>item.kind!=='note').map(item=>({...item,id:item.design_key}));
  const keys=new Set(state.projects.flatMap(catalog=>[...catalog.items.map(item=>item.design_key),...(catalog.excluded_design_keys||[])]));
  return [...project,...state.designs.filter(d=>!keys.has(d.id)).map(d=>({...d,kind:'design',extra:true}))];
}
function navigationChoices(){const all=designChoices(),current=all.find(d=>d.id===state.design?.id);return all.filter(d=>!!d.extra===!!current?.extra);}
function populateDesignChoices(){
  const choices=designChoices(),option=d=>`<option value="${esc(d.id)}">${esc(d.index?d.index+'. ':'')}${esc(d.name)}${d.kind==='note'?' · 说明':''}</option>`;
  const project=choices.filter(d=>!d.extra),extras=choices.filter(d=>d.extra);
  $('design').innerHTML=(project.length?`<optgroup label="${esc(state.catalog?.project_name||'蓝湖项目')}">${project.map(option).join('')}</optgroup>`:'')+(extras.length?`<optgroup label="其他导入 / 历史样例">${extras.map(option).join('')}</optgroup>`:'');
  $('project-select').innerHTML=state.projects.map(item=>`<option value="${esc(item.id)}">${esc(item.project_name)} · ${item.total_designs} 页</option>`).join('');if(state.catalog)$('project-select').value=state.catalog.id;
  $('project-page-count').textContent=project.length||choices.length;renderDesignBrowser();
}
async function loadDesign(key){
  const entry=designChoices().find(d=>d.id===key);
  if(entry&&entry.kind!=='design'){
    state.design={...entry,project:state.catalog.project_name,source_url:state.catalog.source_url};state.nodes=[];
  }else{
    const data=await api('/api/designs/'+encodeURIComponent(key));state.design=data.design;state.nodes=data.nodes;
  }
  $('design').value=key;const d=state.design,note=!!d.kind;
  $('project-name').textContent=d.project;
  $('design-size').textContent=note?(d.kind==='note'?'蓝湖交互说明':'原稿暂不可用'):`${d.canvas.width} × ${d.canvas.height} · 设计画布`;
  $('design-nodes').textContent=note?'按源条目原文展示':`${d.node_count} 个节点${d.complete_nodes?' · 已取齐':' · 部分范围'}`;
  $('version').textContent=note?'项目原文':'版本 '+d.version.slice(0,8);$('design-thumb').hidden=note;
  if(!note)$('design-thumb').src=`/files/designs/${key}/thumbnail.png`;
  const source=d.source_url&&/^https:\/\/lanhuapp\.com\//.test(d.source_url)?d.source_url:null;
  $('design-link').hidden=!source;if(source)$('design-link').href=source;
}
function sourceNote(){
  const d=state.design;
  return `<article class="source-note"><span class="eyebrow">${d.kind==='note'?'蓝湖 · 交互说明':'蓝湖 · 原稿暂不可用'}</span><h2>${esc(d.name)}</h2><div>${esc(d.kind==='note'?d.body:d.error)}</div><p>此条目没有可用的设计原图，不参与像素差异分析。</p></article>`;
}
function renderDesignBrowser(){
  const query=$('design-search').value.trim().toLocaleLowerCase(),all=designChoices(),choices=state.catalog?all.filter(d=>!d.extra):all;
  const groupSelect=$('catalog-group'),previous=groupSelect.dataset.project===state.catalog?.id?groupSelect.dataset.value:'';
  const groups=[...new Set(choices.flatMap(d=>d.sectors?.length?d.sectors:['未分组']))];
  groupSelect.dataset.value=groups.includes(previous)?previous:'';groupSelect.dataset.project=state.catalog?.id||'';
  const scroll=groupSelect.scrollLeft;
  groupSelect.innerHTML=['',...groups].map(g=>`<button type="button" class="catalog-group-tab" data-group="${esc(g)}" aria-pressed="${g===groupSelect.dataset.value}">${esc(g||'全部')}<span>${g?choices.filter(d=>(d.sectors?.length?d.sectors:['未分组']).includes(g)).length:choices.length}</span></button>`).join('');
  groupSelect.scrollLeft=scroll;
  groupSelect.querySelectorAll('[data-group]').forEach(button=>button.onclick=()=>{if(state.busy||state.switching)return;if($('design-browser').open&&groupSelect.dataset.value===button.dataset.group){$('design-browser').close();return;}groupSelect.dataset.value=button.dataset.group;$('design-search').value='';renderDesignBrowser();$('design-browser').show();$('design-grid').scrollTop=0;const selected=groupSelect.querySelector('[aria-pressed="true"]');selected.focus({preventScroll:true});selected.scrollIntoView({block:'nearest',inline:'nearest'});});
  const visible=choices.filter(d=>(!groupSelect.dataset.value||(d.sectors?.length?d.sectors:['未分组']).includes(groupSelect.dataset.value))).filter(d=>(d.name+' '+(d.source_name||'')).toLocaleLowerCase().includes(query));
  $('catalog-title').textContent=groupSelect.dataset.value||'全部设计图';
  $('catalog-project').textContent=state.catalog?.project_name||'已导入设计';
  if(state.catalog)$('project-select').value=state.catalog.id;
  $('catalog-count').textContent=`${visible.length} / ${choices.length} 个条目`;
  $('design-grid').innerHTML=visible.length?'<div class="masonry-items">'+visible.map(d=>`<button class="design-tile ${d.id===state.design?.id?'selected':''}" data-design-key="${esc(d.id)}" aria-pressed="${d.id===state.design?.id}"><div class="design-tile-preview">${d.kind==='design'?`<img src="/files/designs/${esc(d.id)}/reference.png" alt="${esc(d.name)}设计图" width="${Math.round(d.width||187.5)}" height="${Math.round(d.height||406)}" loading="lazy" decoding="async">`:`<div class="note-thumb"><span>≡</span><p>${esc(d.name)}</p><small>${d.kind==='note'?'交互说明':'暂不可用'}</small></div>`}</div><div class="design-tile-caption"><strong>${d.index?String(d.index).padStart(2,'0')+' · ':''}${esc(d.name)}</strong><span>${d.extra?'其他导入 / 历史样例':d.kind==='note'?'文字说明':d.kind==='design'?'设计原图':'待补充原稿'}${d.id===state.design?.id?' · 当前':''}</span></div></button>`).join('')+'</div>':'<div class="catalog-empty">没有匹配的页面，试试其他名称。</div>';
  const masonry=$('design-grid').querySelector('.masonry-items');
  if(masonry){const count=window.innerWidth<=500?1:window.innerWidth<=800?2:window.innerWidth<=1100?3:4,tiles=[...masonry.children],heights=Array(count).fill(0),columns=Array.from({length:count},()=>{const col=document.createElement('div');col.className='masonry-column';return col;});tiles.forEach((tile,index)=>{const column=heights.indexOf(Math.min(...heights));columns[column].append(tile);heights[column]+=(visible[index].height/visible[index].width||2.16)+.15;});masonry.replaceChildren(...columns);}
  $('design-grid').querySelectorAll('[data-design-key]').forEach(button=>button.onclick=()=>busy(async()=>{await selectDesign(button.dataset.designKey);$('design-browser').close();}));
}


function releaseSession(session,keepalive=false){
  if(!session)return;
  fetch('/api/preview/stop',{method:'POST',headers:{'Content-Type':'application/json','X-Review-Token':state.token},body:JSON.stringify({session_id:session}),keepalive}).catch(()=>{});
}
function pauseLive(message='',keepSession=false){resumeOnVisible=false;live.playing=false;live.epoch++;live.streamAbort?.abort();live.streamAbort=null;clearTimeout(live.timer);live.error=userMessage(message);if(!keepSession){releaseSession(live.session);live.session=null;}renderStatus();updateButtons();}
function leaveLive(keepView=false){pauseLive();releaseSession(live.session);live.session=null;live.frame=null;live.view=keepView;live.error='';}
async function startLive(){await persist();await refreshDevices();rememberSelection();leaveLive(true);live.playing=true;live.samples=[];live.lastPresented=0;const epoch=live.epoch;render();try{if(!ready())throw Error('未发现已授权的设备，请连接手机并允许 USB 调试。');const packet=await api('/api/preview/start',{device:$('device').value});if(epoch!==live.epoch||document.hidden){releaseSession(packet.session_id);if(epoch===live.epoch){pauseLive('工作台已隐藏，预览已暂停。');resumeOnVisible=true;}return;}live.session=packet.session_id;await presentLive(packet,epoch);scheduleLive(epoch);}catch(error){if(epoch===live.epoch){pauseLive(error.message);renderViewer();}throw error;}}
async function presentLive(packet,epoch){const decoded=new Image();decoded.src=packet.preview_url;await decoded.decode();if(!live.playing||epoch!==live.epoch)return;const stamp=performance.now();if(live.lastPresented){live.samples.push(stamp-live.lastPresented);if(live.samples.length>8)live.samples.shift();}live.lastPresented=stamp;const changed=!live.frame||live.frame.image_size.join()!==packet.image_size.join();live.frame=packet;if(changed)renderViewer();else setImage($('phone-image'),packet.preview_url);renderStatus();updateButtons();}
async function scheduleLive(epoch){
  const controller=new AbortController();live.streamAbort=controller;
  let pending=null,presenting=false,buffer='';
  const drain=async()=>{
    if(presenting)return;presenting=true;
    try{while(pending&&live.playing&&epoch===live.epoch){const packet=pending;pending=null;await presentLive(packet,epoch);}}
    catch(error){if(epoch===live.epoch)pauseLive(error.message);}
    finally{presenting=false;}
  };
  try{
    const response=await fetch('/api/preview/stream',{method:'POST',headers:{'Content-Type':'application/json','X-Review-Token':state.token},body:JSON.stringify({session_id:live.session}),signal:controller.signal});
    if(!response.ok){const failure=await response.json();throw Error(failure.error||'预览连接失败');}
    const reader=response.body.getReader(),decoder=new TextDecoder();
    while(live.playing&&epoch===live.epoch){
      const {value,done}=await reader.read();if(done)throw Error('预览连接已断开，请重新连接。');
      buffer+=decoder.decode(value,{stream:true});let newline;
      while((newline=buffer.indexOf('\n'))>=0){const line=buffer.slice(0,newline);buffer=buffer.slice(newline+1);if(!line)continue;const packet=JSON.parse(line);if(packet.error)throw Error(packet.error);pending=packet;}
      // One pending frame only: slow rendering never builds a playback backlog.
      void drain();
    }
  }catch(error){if(epoch===live.epoch&&error.name!=='AbortError'){pauseLive(error.message);toast(error.message,true);}}
}

async function captureScreen(){
  if(state.source==='virtual')await window.flushVirtualControl?.();
  await persist();
  // Saved screenshots use fresh lossless ADB pixels, independent of video frames
  // or preview sessions that may have paused/expired while the tab was hidden.
  state.capturing=true;$('capture-loading').hidden=false;renderPins();
  try{await refreshDevices();if(!ready())throw Error('设备未就绪，请检查手机连接和 USB 调试授权。');if(live.view)pauseLive();const run=await api('/api/capture',{design_id:state.design.id,device:$('device').value,title:state.design.name+' · 截图'});await acceptRun(run);toast('已新增截图，可选择「手动标注」添加问题。');}
  catch(error){if(live.view)pauseLive('截图未完成，可重试截图或继续预览。');throw error;}
  finally{state.capturing=false;$('capture-loading').hidden=true;renderViewer();}
}
function renderSlides(){
  const records=currentDesignRuns().map(r=>r.id===state.run?.id?state.run:r);$('slide-count').textContent=records.length;
  const signature=JSON.stringify([state.design?.id,records.map(r=>[r.id,r.title,r.created_at,r.kind,r.issues.length])]);const list=$('screenshot-list');
  if(signature!==slideSignature){slideSignature=signature;const scroll=list.scrollTop;list.innerHTML=records.length?records.map((r,index)=>{const label=`第 ${index+1} 张 · ${r.title} · ${dateLabel(r.created_at)} · ${r.issues.length} 个标注`;return `<div role="listitem"><button class="screenshot-slide" data-run="${esc(r.id)}" aria-label="${esc(label)}" title="${esc(label)}"><div class="slide-preview"><span class="slide-number">${index+1}</span><img loading="lazy" src="/files/runs/${esc(r.id)}/thumbnail.png" alt="${esc(r.title)}截图缩略图"></div><strong>${esc(r.title)}</strong><div class="slide-meta"><time>${esc(dateLabel(r.created_at))}</time><span>${r.issues.length} 个标注</span></div>${r.kind==='demo'?'<small class="slide-demo">历史样例</small>':''}</button></div>`;}).join(''):'<p class="rail-empty">当前原稿暂无截图<br>点击顶部「截图」新增记录</p>';list.scrollTop=scroll;list.querySelectorAll('[data-run]').forEach(button=>{button.onclick=()=>busy(async()=>{if(live.view||state.run?.id!==button.dataset.run)await openRun(button.dataset.run);});button.onkeydown=event=>{const buttons=[...list.querySelectorAll('[data-run]')],index=buttons.indexOf(button);const target=event.key==='ArrowDown'?buttons[index+1]:event.key==='ArrowUp'?buttons[index-1]:event.key==='Home'?buttons[0]:event.key==='End'?buttons[buttons.length-1]:null;if(target){event.preventDefault();target.focus();target.click();}};});}
  list.querySelectorAll('[data-run]').forEach(button=>{const selected=!live.view&&button.dataset.run===state.run?.id;button.classList.toggle('active',selected);button.disabled=state.busy||state.switching;if(selected)button.setAttribute('aria-current','true');else button.removeAttribute('aria-current');});
}
function revealSlide(){requestAnimationFrame(()=>$('screenshot-list').querySelector('[aria-current="true"]')?.scrollIntoView({block:'nearest',inline:'nearest'}));}
function readFile(file){return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=()=>reject(Error('无法读取文件'));reader.readAsDataURL(file);});}
const wait=milliseconds=>new Promise(resolve=>setTimeout(resolve,milliseconds));
function renderProjectJob(job){
  const p=job.progress||{},done=Number(p.completed||0),total=Number(p.total||0),position=total?`${done} / ${total}`:`已恢复 ${done} 页`;
  const detail=[p.name,p.phase,p.tile&&p.tiles?`分块 ${p.tile}/${p.tiles}`:''].filter(Boolean).join(' · ');
  $('project-progress').classList.toggle('error',job.status==='error');
  $('project-progress').textContent=job.status==='error'?job.error:`后台同步 ${position}${detail?' · '+detail:''}。可以关闭窗口继续验收。`;
}
async function applyAssociatedProject(catalog,previousProject,previousDesign){
  if($('project-dialog').open)$('project-dialog').close();
  await bootstrap(catalog.id);const choices=designChoices().filter(item=>!item.extra);
  if(catalog.id===previousProject&&choices.some(item=>item.id===previousDesign)){await loadDesign(previousDesign);render();}
  else{const target=choices.find(item=>item.kind==='design')||choices[0];if(target){try{await selectDesign(target.id);}catch(error){if(state.design?.id!==target.id)throw error;}}}
}
async function watchProjectJob(job,previousProject,previousDesign){
  state.projectJob=job.id||'finishing';if(job.id)localStorage.setItem('review-project-job',job.id);updateButtons();
  try{
    while(job.status==='queued'||job.status==='running'){
      renderProjectJob(job);await wait(900);job=await api('/api/projects/jobs/'+encodeURIComponent(job.id));
    }
    renderProjectJob(job);
    if(job.status==='error')throw Error(job.error||'蓝湖项目同步失败');
    if(!job.catalog)throw Error('蓝湖项目同步完成，但没有返回项目目录');
    await applyAssociatedProject(job.catalog,previousProject,previousDesign);
    toast(job.progress?.completed?'蓝湖项目已关联。':'项目已经关联，无需重复添加。');
  }catch(error){$('project-progress').classList.add('error');$('project-progress').textContent=error.message;toast(error.message,true);}
  finally{localStorage.removeItem('review-project-job');state.projectJob=null;updateButtons();}
}
async function startProjectAssociation(){
  if(state.projectJob)return;
  if(!state.projectPreview){toast('请先检查蓝湖项目连接。',true);return;}
  const previousProject=state.catalog?.id,previousDesign=state.design?.id;
  state.projectJob='starting';$('project-progress').classList.remove('error');$('project-progress').textContent='正在创建后台同步任务…';updateButtons();
  try{const job=await api('/api/projects',{url:state.projectPreview.source_url});await watchProjectJob(job,previousProject,previousDesign);}
  catch(error){state.projectJob=null;$('project-progress').classList.add('error');$('project-progress').textContent=error.message;toast(error.message,true);updateButtons();}
}
$('capture').onclick=()=>busy(captureScreen);
$('live-toggle').onclick=()=>busy(async()=>{if(live.view&&live.playing&&state.source==='physical')return;await persist();leaveLive();state.source='physical';state.captureDevice='';$('device').value='';rememberCaptureSource();await startLive();rememberCaptureSource();});
$('review-toggle').onclick=()=>busy(async()=>{if(!state.run){const latest=currentDesignRuns()[0];if(latest)await openRun(latest.id);return;}await persist();leaveLive();render();revealSlide();});
$('live-pause').onclick=()=>{if(live.playing)pauseLive();else busy(startLive);};
$('pin-layer').onclick=event=>{if(event.target===$('pin-layer'))addPin(event.clientX,event.clientY);};
$('pin-layer').onkeydown=event=>{if(event.target===$('pin-layer')&&['Enter',' '].includes(event.key)){event.preventDefault();const r=$('shot-surface').getBoundingClientRect();addPin(r.x+r.width/2,r.y+r.height/2);}};
$('open-settings').onclick=()=>{if(state.source==='virtual'){window.openVirtual();return;}$('settings-dialog').showModal();busy(refreshDevices);};$('refresh-devices').onclick=()=>busy(refreshDevices);
$('toggle-screenshot-rail').onclick=()=>{
  const rail=$('screenshot-rail'),button=$('toggle-screenshot-rail'),sidebar=$('review-sidebar');
  sidebar.classList.toggle('is-collapsed');
  const collapsed=sidebar.classList.contains('is-collapsed');
  rail.toggleAttribute('inert',collapsed);
  rail.setAttribute('aria-hidden',String(collapsed));
  button.setAttribute('aria-expanded',String(!collapsed));
  button.title=collapsed?'展开截图记录':'收起截图记录';
  button.setAttribute('aria-label',button.title);
  if(!collapsed)setTimeout(revealSlide,220);
};
$('retry-save').onclick=()=>busy(persist);
$('connect-preview').onclick=()=>state.source==='virtual'?window.openVirtual():busy(startLive);
function connectionChanged(){state.captureDevice=$('device').value;rememberCaptureSource();if(live.view){pauseLive('连接设置已变更，请重新连接。');releaseSession(live.session);live.session=null;live.frame=null;renderViewer();renderStatus();}displayDevice();updateButtons();}
$('device').onchange=connectionChanged;
$('design').onchange=()=>busy(()=>selectDesign($('design').value));
$('demo').onclick=()=>busy(async()=>{await persist();await acceptRun(await api('/api/demo',{}));});
$('upload').onclick=()=>$('image-file').click();$('image-file').onchange=()=>busy(async()=>{const file=$('image-file').files[0];if(!file)return;await persist();await acceptRun(await api('/api/import',{design_id:state.design.id,image:await readFile(file),title:state.design.name+' · '+file.name}));$('image-file').value='';toast('截图已加入右侧记录。');});
$('export').onclick=()=>busy(async()=>{await persist();const response=await fetch('/api/runs/'+state.run.id+'/export');if(!response.ok){const error=await response.json();throw Error(error.error);}const url=URL.createObjectURL(await response.blob());const a=document.createElement('a');a.href=url;a.download='design-review-'+state.run.id.slice(0,8)+'.zip';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),10000);});
function openDesignBrowser(){$('design-search').value='';renderDesignBrowser();$('design-browser').show();$('design-search').focus();};$('design-search').oninput=renderDesignBrowser;$('close-design-browser').onclick=()=>$('design-browser').close();
$('project-select').onchange=()=>busy(()=>selectProject($('project-select').value));
$('add-project').onclick=()=>{$('design-browser').close();if(!state.projectJob){state.projectPreview=null;state.projectInspecting=false;$('project-form').reset();$('project-preview').hidden=true;$('project-progress').textContent='';$('project-progress').classList.remove('error');}$('project-dialog').showModal();updateButtons();if(!state.projectJob)$('project-url').focus();};
let projectPreviewVersion=0;
$('project-dialog').addEventListener('close',()=>{projectPreviewVersion++;state.projectInspecting=false;state.projectPreview=null;});
$('project-url').oninput=()=>{projectPreviewVersion++;state.projectInspecting=false;state.projectPreview=null;$('project-preview').hidden=true;$('project-progress').textContent='';updateButtons();};
$('inspect-project').onclick=async()=>{const version=++projectPreviewVersion,url=$('project-url').value.trim();state.projectPreview=null;state.projectInspecting=true;$('project-preview').hidden=true;$('project-progress').classList.remove('error');$('project-progress').textContent='正在连接蓝湖…';updateButtons();try{const preview=await api('/api/projects/preview',{url});if(version!==projectPreviewVersion)return;state.projectPreview=preview;$('project-url').value=preview.source_url;$('project-preview-name').textContent=preview.project_name;$('project-preview-count').textContent=preview.total_designs+' 页';$('project-preview').hidden=false;$('project-progress').textContent='';}catch(error){if(version!==projectPreviewVersion)return;$('project-progress').textContent=error.message;$('project-progress').classList.add('error');toast(error.message,true);}finally{if(version===projectPreviewVersion)state.projectInspecting=false;updateButtons();}};
$('project-form').onsubmit=event=>{event.preventDefault();if(!state.projectPreview){if(!$('inspect-project').disabled)$('inspect-project').click();return;}startProjectAssociation();};
$('import-design').onclick=()=>{$('settings-dialog').close();$('baseline-dialog').showModal();};$('close-dialog').onclick=()=>$('baseline-dialog').close();
$('baseline-form').onsubmit=event=>{event.preventDefault();busy(async()=>{await persist();const snapshot=JSON.parse(await $('baseline-json').files[0].text());const design=await api('/api/designs',{snapshot,image:await readFile($('baseline-image').files[0]),name:$('baseline-name').value});$('baseline-dialog').close();await bootstrap();await selectDesign(design.id);});};
document.querySelectorAll('[data-close]').forEach(button=>button.onclick=()=>$(button.dataset.close).close());
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&$('design-browser').open){$('design-browser').close();return;}if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='k'&&!document.querySelector('dialog[open]')){event.preventDefault();if(!state.busy)openDesignBrowser();}if((event.ctrlKey||event.metaKey)&&event.key==='s'){event.preventDefault();busy(persist);}if(event.key==='Escape'&&document.activeElement?.closest('.pin-bubble')&&!document.querySelector('dialog[open]')){document.activeElement.blur();persist().catch(error=>toast(error.message,true));}});
document.addEventListener('visibilitychange',()=>{if(document.hidden){if(live.playing){pauseLive('工作台已隐藏，预览已暂停。');resumeOnVisible=true;}persist().catch(error=>toast(error.message,true));}else if(resumeOnVisible&&live.view){const resume=()=>{if(document.hidden||!resumeOnVisible||!live.view)return;if(state.busy){setTimeout(resume,150);return;}resumeOnVisible=false;busy(startLive);};resume();}});
window.addEventListener('beforeunload',event=>{if(state.dirty){event.preventDefault();event.returnValue='';}});window.addEventListener('pagehide',()=>{pauseLive('',true);releaseSession(live.session,true);live.session=null;});
new ResizeObserver(renderViewer).observe($('device-body'));
(async()=>{try{await bootstrap();const params=new URLSearchParams(location.hash.slice(1)),key=params.get('run'),designKey=params.get('design');const run=state.runs.find(r=>r.id===key)||state.runs.find(r=>r.kind!=='demo')||state.runs[0];if(designKey){const project=projectForDesign(designKey);if(project&&project.id!==state.catalog?.id)setCatalog(project);}if(designKey&&designChoices().some(d=>d.id===designKey)){await loadDesign(designKey);const latest=state.runs.find(r=>r.design_id===designKey);if(latest)await openRun(latest.id);else render();}else if(run)await openRun(run.id);else{const target=designChoices().find(item=>!item.extra&&item.kind==='design')||designChoices()[0];if(target){await loadDesign(target.id);render();}}await refreshDevices();if(live.view&&ready())await busy(startLive);const savedJob=localStorage.getItem('review-project-job');if(savedJob)watchProjectJob({id:savedJob,status:'running',progress:{phase:'恢复同步状态'}});}catch(error){toast(error.message,true);}})();

window.addEventListener('resize',()=>{if($('design-browser').open)renderDesignBrowser();});
