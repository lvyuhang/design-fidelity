'use strict';
const virtualSelectionKey='review-virtual-selection-v1';
function readVirtualSelection(){try{return JSON.parse(localStorage.getItem(virtualSelectionKey)||'{}');}catch(_){return {};}}
const savedVirtualSelection=readVirtualSelection();
const virtual={browse:['width','model'].includes(savedVirtualSelection.browse)?savedVirtualSelection.browse:'width',group:savedVirtualSelection.group||'all',modelGroup:savedVirtualSelection.modelGroup||'all',model:savedVirtualSelection.model||null,testWidth:Number(savedVirtualSelection.testWidth)||393,status:null,profile:savedVirtualSelection.profile||'width-360',selectionSaved:!!localStorage.getItem(virtualSelectionKey),uploading:false,starting:false,handled:null,pointer:null,poll:null};
function saveVirtualSelection(){localStorage.setItem(virtualSelectionKey,JSON.stringify({browse:virtual.browse,group:virtual.group,modelGroup:virtual.modelGroup,model:virtual.model,testWidth:virtual.testWidth,profile:virtual.profile}));virtual.selectionSaved=true;}
const virtualSwitchOverlay=document.createElement('div');
virtualSwitchOverlay.className='virtual-switch-loading';virtualSwitchOverlay.hidden=true;
virtualSwitchOverlay.setAttribute('role','status');virtualSwitchOverlay.innerHTML='<span class="virtual-switch-spinner" aria-hidden="true"></span><strong>正在切换设备…</strong><small>配置完成后自动恢复画面</small>';
$('device-body').append(virtualSwitchOverlay);
function setVirtualSwitching(value){virtual.switching=value;state.switching=value;virtualSwitchOverlay.hidden=!value;$('device-body').setAttribute('aria-busy',String(value));updateButtons();if(!value)renderViewer();}
window.virtualRuntime=()=>virtual.status?.active;
window.virtualSerial=()=>virtual.status?.active?.serial;
window.syncVirtualUI=()=>{
  if(virtual.switching){$('capture').disabled=true;$('preview-device-meta').disabled=true;}
  const remote=state.source==='virtual'&&(live.view||virtual.switching)&&(live.playing||virtual.switching)&&!!virtual.status?.active;
  $('virtual-controls').hidden=!remote;
  $('phone-image').classList.toggle('remote-control',remote);
  $('virtual-toggle').disabled=state.busy||virtual.switching;
  if(virtual.switching)return;
  const active=virtual.status?.active;
  if(state.source==='virtual'&&active){$('device-title').textContent='原生 Android '+(active.api_level===34?'14':'API '+active.api_level)+' · '+active.profile.name+' 屏幕';$('device-title').title='屏幕适配模板，不包含厂商品牌系统 · '+Math.round(active.width_dp)+' dp';}
  $('virtual-open-app').textContent='打开'+(active?.package?.label||'测试 App');
  const runtime=live.view?(state.source==='virtual'?active:null):state.run?.capture?.review_context?.runtime;
  const device=live.view?state.devices.find(d=>d.id===$('device').value):state.run?.capture?.device;
  const profile=runtime?.profile,hardware=profile?.hardware_reference;
  const size=live.view?live.frame?.image_size:state.run?.image_size;
  const dimensions=profile?.width&&profile?.height?`${profile.width} × ${profile.height} px`:size?`${size[0]} × ${size[1]} px`:'分辨率待连接';
  $('preview-device-name').textContent=profile?.name||(typeof device==='object'?device?.name:null)||'未连接设备';
  $('preview-device-specs').textContent=[hardware?.inches?`${hardware.inches} 英寸`:null,dimensions].filter(Boolean).join(' · ');
  $('preview-device-meta').title=[runtime?'原生 Android 屏幕模板':live.view?'当前真机画面':'截图时的设备参数',runtime?.width_dp?`逻辑宽度 ${Math.round(runtime.width_dp)} dp`:null,!profile&&size?'图像像素尺寸':null].filter(Boolean).join(' · ');
  $('preview-device-meta').disabled=!live.view||state.busy||!!virtual.switching;

};
function virtualProgress(text,error=false,transient=false){if(!transient)virtual.notice={text,error};$('virtual-progress').textContent=text;$('virtual-progress').parentElement.classList.toggle('error',error);}
function renderVirtual(){
  const data=virtual.status;if(!data)return;
  document.querySelector('.virtual-auto-hint').textContent=data.active?'选择设备后自动切换':'选择设备后启动预览';
  const running=data.job?.status==='running',locked=running||virtual.uploading||virtual.starting;
  $('virtual-setup').hidden=data.runtime_ready;
  $('virtual-start').disabled=locked||!data.runtime_ready||!$('virtual-package').value;
  $('virtual-start').textContent=data.active?(data.active.package?.id===$('virtual-package').value?'应用设备配置':'更换开发包并启动'):'启动预览';
  $('virtual-start').hidden=!!data.active&&data.active.package?.id===$('virtual-package').value&&data.active.state==='ready';
  $('virtual-upload').disabled=locked;$('apk-download').disabled=locked;
  $('virtual-install').disabled=locked||!$('virtual-license').checked||!data.supported;
  $('virtual-stop').hidden=!data.active;$('virtual-stop').disabled=locked;
  $('virtual-resume').hidden=!data.active;$('virtual-resume').disabled=locked;
  $('virtual-cancel').hidden=!running;
  const configLocked=virtual.starting||(running&&['start','stop'].includes(data.job.operation));
  for(const id of ['virtual-package','virtual-font','virtual-display','virtual-search','virtual-collect','virtual-density','virtual-navigation','virtual-cutout'])$(id).disabled=configLocked;
  renderDeviceCatalog(data,configLocked);
  const apk=data.packages.find(p=>p.id===$('virtual-package').value);
  $('apk-info').textContent=apk?[apk.label||apk.name,apk.version_name?'v'+apk.version_name:'',(apk.size/1048576).toFixed(1)+' MB',apk.abis.join(' / ')||'无原生架构限制'].filter(Boolean).join(' · '):'上传后会检查包名、版本和处理器架构。';
  if(!virtual.uploading){
    const job=data.job;
    if(!running&&virtual.notice)virtualProgress(virtual.notice.text,virtual.notice.error,true);
    if(job&&(!virtual.notice||running)){virtualProgress(job.status==='error'?job.error:job.status==='cancelled'?'任务已取消，可重新启动。':job.phase,job.status==='error',true);$('virtual-progress-bar').hidden=!running;if(job.progress===null)$('virtual-progress-bar').removeAttribute('value');else $('virtual-progress-bar').value=job.progress;}
    else $('virtual-progress-bar').hidden=true;
  }
  const active=data.active,g=active?.screen_geometry;
  $('virtual-geometry').textContent=g?`运行中：${active.profile.name} · 系统参考内容区 ${g.width_px} × ${g.height_px} px（${(g.width_px*160/active.density).toFixed(1)} × ${(g.height_px*160/active.density).toFixed(1)} dp）`:'';
  syncVirtualUI();
}
function catalogHTML(id,html){if(virtual[id]!==html){virtual[id]=html;$(id).innerHTML=html;}}
function profileGroup(p){const w=p.width_dp;return p.group||(w<375?'small':w<400?'medium':w<440?'large':w<600?'wide':w<800?'fold':'tablet');}
function selectedVirtualProfile(){
  if(virtual.browse==='model'){
    const m=virtual.status.models.find(m=>m.id===virtual.model);if(!m)return null;
    const density=Math.round(m.width*160/virtual.testWidth);
    return {...m,models:[m.name],density,width_dp:m.width*160/density,verification:'官方屏幕参数 · 测试密度',condition:'出厂 dp 尚未采集；当前宽度是自选测试值。'};
  }
  return virtual.status.profiles.find(p=>p.id===virtual.profile)||null;
}
function deviceSettingsKey(){return virtual.browse==='model'?'model:'+virtual.model:'profile:'+virtual.profile;}
function deviceSettingsBody(){return {...(virtual.browse==='model'?{model_id:virtual.model,test_width_dp:virtual.testWidth}:{profile_id:virtual.profile}),density_override:$('virtual-density').value?Number($('virtual-density').value):null,navigation:$('virtual-navigation').value,cutout:$('virtual-cutout').value,font_scale:Number($('virtual-font').value),display_scale:Number($('virtual-display').value)};}
function restoreDeviceSettings(data){
  const key=deviceSettingsKey();
  if(virtual.settingsKey===key)return;
  virtual.drafts||={};
  if(virtual.settingsKey)virtual.drafts[virtual.settingsKey]={...deviceSettingsBody(),test_width_dp:virtual.lastTestWidth??virtual.testWidth};
  const model=data.models.find(m=>m.id===virtual.model),profile=data.profiles.find(p=>p.id===virtual.profile);
  const active=data.active,activeKey=active?(active.profile.model_id?'model:'+active.profile.model_id:'profile:'+active.profile.id):null;
  const fromActive=key===activeKey?{...active,test_width_dp:active.profile.requested_width_dp}:null;
  const saved=virtual.drafts[key]||data.device_settings?.[key]||fromActive;
  const base=virtual.browse==='width'?profile:null;
  const values=saved||{font_scale:Number(base?.font_scale)||1,display_scale:1,navigation:base?.navigation||'gestural',cutout:'none'};
  const font=Number(values.font_scale)||1;
  if(![...$('virtual-font').options].some(o=>Number(o.value)===font))$('virtual-font').add(new Option('自定义 · '+Math.round(font*100)+'%',String(font)));
  $('virtual-font').value=String(font);$('virtual-display').value=String(values.display_scale||1);
  $('virtual-density').value=values.density_override||'';$('virtual-navigation').value=values.navigation||'threebutton';$('virtual-cutout').value=values.cutout||'none';
  if(virtual.browse==='model')virtual.testWidth=model.test_widths.includes(values.test_width_dp)?values.test_width_dp:model.default_test_width;
  virtual.settingsKey=key;virtual.lastTestWidth=virtual.testWidth;
}
function renderDeviceCatalog(data,locked){
  const modelMode=virtual.browse==='model',q=$('virtual-search').value.trim().toLowerCase();
  $('virtual-search').placeholder=modelMode?'搜索机型或品牌':'搜索宽度或参考机型';
  let hasMatches=true;
  document.querySelectorAll('[data-vbrowse]').forEach(b=>{b.setAttribute('aria-pressed',String(b.dataset.vbrowse===virtual.browse));b.disabled=locked;});
  $('virtual-profiles').hidden=modelMode;$('virtual-model-grid').hidden=!modelMode;$('virtual-brand').hidden=!modelMode;$('virtual-model-width-row').hidden=!modelMode;
  $('virtual-brand').disabled=locked;$('virtual-model-width').disabled=locked;
  const groups=modelMode?data.model_groups:[{id:'all',name:'全部'},...data.width_groups];
  const group=modelMode?virtual.modelGroup:virtual.group;
  catalogHTML('virtual-groups',groups.map(g=>`<button type="button" data-vgroup="${g.id}" title="${esc(g.name)}" aria-pressed="${group===g.id}" ${locked?'disabled':''}>${esc(g.name.split(' · ')[0])}</button>`).join(''));
  $('virtual-groups').querySelectorAll('[data-vgroup]').forEach(b=>b.onclick=()=>{if(modelMode)virtual.modelGroup=b.dataset.vgroup;else virtual.group=b.dataset.vgroup;saveVirtualSelection();renderVirtual();});
  if(modelMode){
    const brands=[...new Set(data.models.map(m=>m.brand))];
    catalogHTML('virtual-brand','<option value="">全部品牌</option>'+brands.map(b=>`<option value="${esc(b)}">${esc(b)}</option>`).join(''));
    if(!data.models.some(m=>m.id===virtual.model)){virtual.model=data.models[0]?.id;virtual.testWidth=data.models[0]?.default_test_width;saveVirtualSelection();}
    const items=data.models.filter(m=>(group==='all'||m.group===group)&&(!$('virtual-brand').value||m.brand===$('virtual-brand').value)&&[m.name,m.brand,m.inches,m.width,m.height].join(' ').toLowerCase().includes(q));
    if(!items.length){$('virtual-start').disabled=true;hasMatches=false;}
    restoreDeviceSettings(data);
    catalogHTML('virtual-model-grid',items.length?items.map(m=>`<button type="button" class="virtual-model-card ${m.id===virtual.model?'active':''}" data-model="${m.id}" aria-pressed="${m.id===virtual.model}" ${locked?'disabled':''}><span class="device-silhouette" style="aspect-ratio:${m.width}/${m.height}"></span><span><strong>${esc(m.name)}</strong><small>${m.inches}″ · ${m.width} × ${m.height}</small></span></button>`).join(''):'<p class="help catalog-empty">没有匹配的机型，请调整分类或搜索。</p>');
    $('virtual-model-grid').querySelectorAll('[data-model]').forEach(b=>b.onclick=()=>{virtual.model=b.dataset.model;saveVirtualSelection();renderVirtual();scheduleVirtualApply(true);});
    const model=data.models.find(m=>m.id===virtual.model);
    if(model){catalogHTML('virtual-model-width',model.test_widths.map(w=>`<option value="${w}">${w} dp</option>`).join(''));$('virtual-model-width').value=String(virtual.testWidth);}
    $('virtual-catalog-hint').textContent=`${items.length} / ${data.models.length} 款屏幕参考 · 按屏幕英寸分类，覆盖主要品牌，不代表销量排名。`;
  }else{
    if(!data.profiles.some(p=>p.id===virtual.profile)){virtual.profile=data.profiles.find(p=>p.id==='width-360')?.id||data.profiles[0]?.id;saveVirtualSelection();}
    const items=data.profiles.filter(p=>(group==='all'||profileGroup(p)===group)&&[p.name,Math.round(p.width_dp),...p.models].join(' ').toLowerCase().includes(q));
    if(!items.length){$('virtual-start').disabled=true;hasMatches=false;}
    restoreDeviceSettings(data);
    catalogHTML('virtual-profiles',items.length?items.map(p=>`<button type="button" class="virtual-profile ${p.id===virtual.profile?'active':''}" data-profile="${esc(p.id)}" aria-pressed="${p.id===virtual.profile}" ${locked?'disabled':''}><strong>${Math.round(p.width_dp)} <small>dp</small></strong><span>${esc(p.models.length?p.name:p.condition)}</span><small>${esc(p.verification||'真机采集')}</small></button>`).join(''):'<p class="help catalog-empty">此分类没有匹配的配置，可切换「按安卓机型」查找。</p>');
    $('virtual-profiles').querySelectorAll('[data-profile]').forEach(b=>b.onclick=()=>{virtual.profile=b.dataset.profile;saveVirtualSelection();renderVirtual();scheduleVirtualApply(true);});
    const g=data.width_groups.find(g=>g.id===group);
    $('virtual-catalog-hint').textContent=g?`${g.range} · ${g.hint}`:'按逻辑宽度分档；小屏 / 大屏表示布局空间，不等同于屏幕英寸。';
  }
  virtual.lastTestWidth=virtual.testWidth;
  $('save-device-settings').disabled=locked||!hasMatches;
  const measured=!modelMode&&data.profiles.find(p=>p.id===virtual.profile)?.verification==='真机采集';
  $('device-calibration-status').textContent=(measured?'真机屏幕参数已采集 · 系统占位待核验':modelMode?'官方屏幕参数 · 默认 DPI / 系统占位待采集':'适配测试配置')+(data.device_settings?.[deviceSettingsKey()]?' · 已保存独立设置':'');
  $('virtual-model-width-row').hidden=!modelMode||!hasMatches;
  if(!hasMatches){catalogHTML('virtual-models','');return;}
  const p=selectedVirtualProfile();
  if(p){
    const density=Math.round((Number($('virtual-density').value)||p.density)*Number($('virtual-display').value)),actual=p.width*160/density;
    const source=p.source?.startsWith('https://')?` · <a href="${esc(p.source)}" target="_blank" rel="noreferrer">${modelMode?'官方屏幕参数':'配置来源'} ↗</a>`:'';
    catalogHTML('virtual-models',`<div class="virtual-selected"><strong>${esc(p.name)}${modelMode?' · 屏幕测试':''}</strong><span>${actual.toFixed(2)} dp × ${(p.height*160/density).toFixed(2)} dp</span></div><div>${p.width} × ${p.height} px · ${density} dpi · ${esc(p.verification||'真机采集')}${source}</div>${!modelMode&&p.models.length>1?'<div class="model-chips">'+p.models.map(m=>'<span class="model-chip">'+esc(m)+'</span>').join('')+'</div>':''}<div class="muted">${esc(p.condition||'同宽设备的高度可能不同，以当前配置为准。')}</div>`);
  }
}
function populatePackages(preferred){const old=preferred||$('virtual-package').value;const signature=JSON.stringify(virtual.status.packages);if(signature!==virtual.packageSignature){virtual.packageSignature=signature;$('virtual-package').innerHTML=virtual.status.packages.length?virtual.status.packages.map(p=>`<option value="${esc(p.id)}">${esc(p.label||p.name)}${p.version_name?' · v'+esc(p.version_name):''}</option>`).join(''):'<option value="">尚未上传开发包</option>';}if(virtual.status.packages.some(p=>p.id===old))$('virtual-package').value=old;}
async function refreshVirtual(){const first=!virtual.status,previous=virtual.status?.active;virtual.status=await api('/api/virtual');if(first&&virtual.status.active){const a=virtual.status.active;if(!virtual.selectionSaved){virtual.profile=a.profile.id;virtual.group=profileGroup(a.profile);if(a.profile.model_id){virtual.browse='model';virtual.model=a.profile.model_id;virtual.testWidth=a.profile.requested_width_dp;}saveVirtualSelection();}if(![...$('virtual-font').options].some(o=>Number(o.value)===a.font_scale))$('virtual-font').add(new Option('自定义 · '+Math.round(a.font_scale*100)+'%',String(a.font_scale)));$('virtual-font').value=String(a.font_scale);$('virtual-display').value=String(a.display_scale);$('virtual-density').value=a.density_override||'';$('virtual-navigation').value=a.navigation||'threebutton';$('virtual-cutout').value=a.cutout||'none';populatePackages(a.package.id);}
if(first&&virtual.status.job&&virtual.status.job.status!=='running')virtual.handled=virtual.status.job.id;if(previous&&!virtual.status.active&&state.source==='virtual'&&live.playing){pauseLive('模拟器已停止，请重新启动。');releaseSession(live.session);live.session=null;live.frame=null;renderViewer();}populatePackages();renderVirtual();return virtual.status;}
window.openVirtual=async(deviceOnly=false)=>{
  $('virtual-dialog').classList.toggle('device-only',deviceOnly===true);
  $('virtual-title').textContent=deviceOnly===true?'设备与分辨率':'虚拟机';
  $('virtual-dialog').showModal();
  try{await refreshVirtual();}catch(e){virtualProgress(e.message,true);}
};
async function resumeVirtual(keepSettings=false){
  if(!virtual.status?.active)throw Error('请先启动模拟器。');
  await persist();leaveLive(true);state.source='virtual';state.captureDevice=virtual.status.active.serial;rememberCaptureSource();
  if(!keepSettings)$('virtual-dialog').close();await refreshDevices();$('device').value=virtual.status.active.serial;
  await startLive();syncVirtualUI();
}
async function virtualJob(operation,extra={},automatic=false){
  if(virtual.starting)return;virtual.notice=null;virtual.starting=true;renderVirtual();
  try{
    if(['start','stop'].includes(operation)){await persist();if(state.source==='virtual'){leaveLive(true);render();}}
    const job=await api('/api/virtual/jobs',{operation,...extra});virtual.status.job=job;virtual.automaticJob=automatic?job.id:null;virtual.handled=null;renderVirtual();
  }catch(e){virtualProgress(e.message,true);toast(e.message,true);if(automatic)setVirtualSwitching(false);}finally{virtual.starting=false;renderVirtual();}
}
async function pollVirtual(){
  try{
    if(state.token&&(state.source==='virtual'||$('virtual-dialog').open||virtual.status?.job?.status==='running'||virtual.status?.active)){
      const data=await refreshVirtual();const job=data.job;
      if(job&&job.status!=='running'&&virtual.handled!==job.id&&!state.busy&&!virtual.completing){
        virtual.handled=job.id;virtual.completing=true;
        if(job.status==='cancelled'){virtual.notice=null;renderVirtual();}
        const automatic=virtual.automaticJob===job.id;
        try{
          if(job.status==='done'&&job.operation==='start'){await resumeVirtual(automatic&&$('virtual-dialog').open);if(automatic)virtualProgress('已自动应用，预览已更新。');}
          if(job.status==='error'){toast(job.error,true);if(automatic&&data.active?.state==='ready')await resumeVirtual($('virtual-dialog').open);}
        }finally{virtual.completing=false;if(automatic){virtual.automaticJob=null;setVirtualSwitching(false);}}
        if(job.status==='done'&&job.operation==='download'){populatePackages(data.packages[0]?.id);renderVirtual();}
        if(job.status==='done'&&job.operation==='setup')toast('Android 环境已就绪，可以启动预览。');
      }
    }
  }catch(e){if($('virtual-dialog').open)virtualProgress(e.message,true);}
  finally{virtual.poll=setTimeout(pollVirtual,1500);}
}
async function uploadApk(file){
  if(!file||virtual.uploading||virtual.status?.job?.status==='running')return;
  if(!/\.apk$/i.test(file.name)||file.size>1024**3){virtualProgress('请选择不超过 1 GB 的 APK 文件。',true);return;}
  virtual.uploading=true;renderVirtual();virtualProgress('上传开发包…');
  try{
    const result=await new Promise((resolve,reject)=>{
      const xhr=new XMLHttpRequest();xhr.open('POST','/api/virtual/upload');xhr.setRequestHeader('X-Review-Token',state.token);xhr.setRequestHeader('X-File-Name',encodeURIComponent(file.name));xhr.setRequestHeader('Content-Type','application/vnd.android.package-archive');xhr.timeout=180000;
      xhr.upload.onprogress=e=>{if(e.lengthComputable){virtualProgress('上传开发包 · '+Math.round(e.loaded/e.total*100)+'%');$('virtual-progress-bar').hidden=false;$('virtual-progress-bar').value=e.loaded/e.total*100;}};
      xhr.onload=()=>{try{const data=JSON.parse(xhr.responseText);if(xhr.status>=400)reject(Error(data.error));else resolve(data);}catch(e){reject(e);}};
      xhr.onerror=()=>reject(Error('上传中断，请检查本地服务后重试。'));xhr.ontimeout=()=>reject(Error('上传超时，请重试。'));xhr.send(file);
    });
    await refreshVirtual();populatePackages(result.id);virtualProgress('开发包已准备好。');
  }catch(e){virtualProgress(e.message,true);}finally{virtual.uploading=false;$('apk-file').value='';renderVirtual();}
}
$('virtual-toggle').onclick=()=>busy(async()=>{
  if(live.view&&live.playing&&state.source==='virtual')return;
  await refreshVirtual();
  if(virtual.status?.active)await resumeVirtual();
  else await openVirtual();
});
$('preview-device-meta').onclick=()=>{
  if(!live.view)return;
  if(state.source==='virtual')openVirtual(true);
  else{$('settings-dialog').showModal();busy(refreshDevices);}
};
$('virtual-resume').onclick=()=>busy(resumeVirtual);
function scheduleVirtualApply(closePicker=false){
  clearTimeout(virtual.applyTimer);
  const active=virtual.status?.active;
  if(!active||active.state!=='ready'||active.package?.id!==$('virtual-package').value)return;
  const body=deviceSettingsBody(),p=active.profile;
  const sameDevice=body.model_id?body.model_id===p.model_id&&body.test_width_dp===p.requested_width_dp:body.profile_id===p.id;
  if(sameDevice&&['density_override','font_scale','display_scale','navigation','cutout'].every(k=>(body[k]??null)===(active[k]??null))){if(virtual.switching)setVirtualSwitching(false);if(closePicker)$('virtual-dialog').close();return;}
  if(!$('virtual-density').checkValidity()){if(virtual.switching)setVirtualSwitching(false);virtualProgress('逻辑密度需为 100–1000 的整数。',true);return;}
  virtualProgress('即将自动应用…');
  if(closePicker)$('virtual-dialog').close();
  setVirtualSwitching(true);
  virtual.applyTimer=setTimeout(()=>{
    if(state.busy||virtual.starting||virtual.status?.job?.status==='running'||virtual.status?.active?.package?.id!==$('virtual-package').value){setVirtualSwitching(false);return;}
    virtualJob('start',{package_id:$('virtual-package').value,...deviceSettingsBody()},true);
  },450);
}
$('virtual-package').onchange=renderVirtual;$('virtual-search').oninput=renderVirtual;
for(const id of ['virtual-display','virtual-font','virtual-navigation','virtual-cutout'])$(id).onchange=()=>{renderVirtual();scheduleVirtualApply();};
$('virtual-density').oninput=()=>{renderVirtual();scheduleVirtualApply();};
$('virtual-brand').onchange=renderVirtual;$('virtual-model-width').onchange=()=>{virtual.testWidth=Number($('virtual-model-width').value);saveVirtualSelection();renderVirtual();scheduleVirtualApply();};
document.querySelectorAll('[data-vbrowse]').forEach(b=>b.onclick=()=>{virtual.browse=b.dataset.vbrowse;$('virtual-search').value='';saveVirtualSelection();renderVirtual();});
$('virtual-license').onchange=renderVirtual;
$('virtual-install').onclick=()=>virtualJob('setup',{accept_license:$('virtual-license').checked});
$('virtual-start').onclick=()=>virtualJob('start',{package_id:$('virtual-package').value,...deviceSettingsBody()});
$('save-device-settings').onclick=async()=>{const button=$('save-device-settings');button.disabled=true;try{const result=await api('/api/virtual/settings',deviceSettingsBody());virtual.status.device_settings||={};virtual.status.device_settings[result.key]=result.settings;virtual.drafts||={};virtual.drafts[result.key]=result.settings;virtualProgress('已保存「'+selectedVirtualProfile().name+'」配置；下次选择时自动恢复。');renderVirtual();}catch(e){virtualProgress(e.message,true);}finally{button.disabled=false;}};
$('virtual-stop').onclick=()=>virtualJob('stop');
$('virtual-cancel').onclick=async()=>{try{await api('/api/virtual/cancel',{});virtualProgress('正在取消…');}catch(e){virtualProgress(e.message,true);}};
$('virtual-upload').onclick=()=>$('apk-file').click();$('apk-file').onchange=()=>uploadApk($('apk-file').files[0]);
$('virtual-upload').ondragover=e=>{e.preventDefault();$('virtual-upload').classList.add('dragover');};$('virtual-upload').ondragleave=()=>$('virtual-upload').classList.remove('dragover');$('virtual-upload').ondrop=e=>{e.preventDefault();$('virtual-upload').classList.remove('dragover');uploadApk(e.dataTransfer.files[0]);};
$('apk-download').onclick=()=>virtualJob('download',{url:$('apk-url').value.trim()});
$('virtual-collect').onclick=async()=>{try{const info=await api('/api/devices');const devices=info.devices.filter(d=>d.state==='device'&&d.kind!=='emulator');const device=devices.find(d=>d.id===$('device').value)||devices[0];if(!device)throw Error('请连接并授权一台 USB 安卓设备。');if(virtual.settingsKey){virtual.drafts||={};virtual.drafts[virtual.settingsKey]=deviceSettingsBody();}const item=await api('/api/virtual/collect',{device:device.id});virtual.settingsKey=null;virtual.profile=item.id;$('virtual-density').value='';$('virtual-display').value='1';const sampled=Number(item.font_scale);if(sampled>=.5&&sampled<=2){if(![...$('virtual-font').options].some(o=>Number(o.value)===sampled))$('virtual-font').add(new Option('真机字体 · '+Math.round(sampled*100)+'%',String(sampled)));$('virtual-font').value=String(sampled);}if(item.navigation)$('virtual-navigation').value=item.navigation;virtual.browse='width';virtual.group='all';$('virtual-search').value='';saveVirtualSelection();await refreshVirtual();virtualProgress('已采集 '+item.name+' 的当前显示配置。');}catch(e){virtualProgress(e.message,true);}};
let controlQueue=Promise.resolve();
window.flushVirtualControl=()=>controlQueue;
function sendControl(body){
  const serial=virtualSerial();
  if(state.source!=='virtual'||!live.view||!live.playing||virtual.switching)return Promise.resolve();
  controlQueue=controlQueue.then(()=>api('/api/virtual/control',{...body,serial})).catch(e=>toast(e.message,true));return controlQueue;
}
$('virtual-open-app').onclick=async()=>{const b=$('virtual-open-app');b.disabled=true;try{await sendControl({action:'launch_app'});}finally{b.disabled=false;}};
document.querySelectorAll('[data-vkey]').forEach(b=>b.onclick=()=>sendControl({action:'key',key:b.dataset.vkey}));
$('virtual-send').onclick=()=>{const text=$('virtual-text').value;if(text)sendControl({action:'text',text});$('virtual-text').value='';};$('virtual-text').onkeydown=e=>{if(e.key==='Enter'){$('virtual-send').click();e.preventDefault();}};
function remotePoint(e){const r=$('phone-image').getBoundingClientRect();return{x:Math.max(0,Math.min(1,(e.clientX-r.left)/r.width)),y:Math.max(0,Math.min(1,(e.clientY-r.top)/r.height))};}
$('phone-image').ondragstart=e=>{if(state.source==='virtual'&&live.view)e.preventDefault();};
$('phone-image').addEventListener('pointerdown',e=>{if(state.source!=='virtual'||!live.view||!live.playing||e.button!==0)return;e.preventDefault();virtual.pointer={...remotePoint(e),at:performance.now(),id:e.pointerId};$('phone-image').setPointerCapture(e.pointerId);});
$('phone-image').addEventListener('pointerup',e=>{const start=virtual.pointer;if(!start||e.pointerId!==start.id)return;virtual.pointer=null;if($('phone-image').hasPointerCapture(e.pointerId))$('phone-image').releasePointerCapture(e.pointerId);const end=remotePoint(e),duration=Math.min(1500,Math.round(performance.now()-start.at));sendControl(Math.hypot(end.x-start.x,end.y-start.y)<.015&&duration<450?{action:'tap',x:start.x,y:start.y}:{action:'swipe',x:start.x,y:start.y,x2:end.x,y2:end.y,duration});});
$('phone-image').addEventListener('pointercancel',()=>virtual.pointer=null);
pollVirtual();
