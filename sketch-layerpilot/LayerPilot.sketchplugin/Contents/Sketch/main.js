var sketch=require('sketch');
var engine=require('./lib/engine');
var dialogs=require('./lib/dialogs');
var progress=require('./lib/progress');
function documentOrMessage(){if(progress.isRunning()){sketch.UI.message('LayerPilot 正在处理文档，请等待完成或点击停止');return;}var doc=sketch.getSelectedDocument();if(!doc)sketch.UI.message('请先打开一个 Sketch 文档');return doc;}
function elapsed(start){return '\n用时 '+((Date.now()-start)/1000).toFixed(1)+' 秒';}
function failure(title,error,doc){console.error(error);if(error.code==='LAYERPILOT_BUSY'){sketch.UI.message(error.message);return;}try{dialogs.showResult(title,String(error.message||error)+'\n若已有变更，可用 ⌘Z 撤销。',[],doc);}catch(panelError){sketch.UI.message(title+'：'+String(error.message||error));}}
function organize(context){
 var doc=documentOrMessage();if(!doc)return;
 try{
  var options=dialogs.organize(engine.scope(doc).label);if(!options)return;var start=Date.now(),r,stopped=false;
  progress.runJob('LayerPilot · 整理图层',function(update){options.onProgress=update;return engine.organizeJob(doc,options);},doc,function(error,result){
  try{
  if(error&&error.code!=='LAYERPILOT_CANCELLED'){failure('整理未完成',error,doc);return;}
  if(error&&error.interruptedByInput){sketch.UI.message('已交还文档操作，自动整理已停止');return;}
  var r=result||(error&&error.report),stopped=!!error;
  if(!r){sketch.UI.message('已停止，尚未修改图层');return;}
  var changed=r.groups+r.renamed+r.removed+r.sorted;
  var details=r.containers.length?'\n\n'+r.containers.slice(0,4).map(function(c){return c.name+'：顶层 '+c.before+' → '+c.after+' 层';}).join('\n'):'';
  if(r.subtleShadows)details+='\n'+r.subtleShadows+' 个完整卡片合并产生极轻微阴影色差（最多 1 / 255）';
  if(r.regions.length){var counts={container:0,row:0,pair:0};r.regions.forEach(function(p){counts[p.kind||'container']++;});details+='\n区域 '+counts.container+' 组 · 列表项 '+counts.row+' 组 · 图标文字 '+counts.pair+' 组';}
  dialogs.showResult(stopped?'整理已停止':changed?'整理完成':'未产生图层变更','新建 '+r.groups+' 个分组 · 命名 '+r.renamed+' 层\n清理 '+r.removed+' 个空组 · 排序 '+r.sorted+' 处\n保留 '+r.protected+' 处受保护结构'+details+elapsed(start)+(changed?'\n\n'+(stopped?'已保留完成的部分。':'')+'使用 ⌘Z 撤销本次整理。':stopped?'\n尚未产生图层变更。':'\n\n选区可能已整理，或没有满足分组条件的同级元素。锁定层、组件源和 Stack 内部结构会保留。'),[],doc);
 }catch(error){failure('整理未完成',error,doc);}
 });
 }catch(error){failure('整理未完成',error,doc);}
}
function assets(context){
 var doc=documentOrMessage();if(!doc)return;
 try{
  var found,prepared;try{found=progress.run('LayerPilot · 识别资源',function(update){var result=engine.collect(doc,{onProgress:update});if(result.assets.length){update({stage:'正在准备资源列表',force:true});prepared=dialogs.buildAssets(result,update);}return result;},doc);}catch(error){if(error.code==='LAYERPILOT_CANCELLED'){sketch.UI.message('已停止识别，文档未修改');return;}throw error;}
  if(!found.assets.length){dialogs.showResult('没有识别到可切图资源',found.scope+'\n请选择包含图片或图标的区域。\n可将完整图标组命名为 icon/名称。\n隐藏、锁定图层和组件源会跳过。',[],doc);return;}
  var options=dialogs.assets(found,prepared);if(!options)return;var start=Date.now(),r,stopped=false;
  try{r=progress.run('LayerPilot · 自动切片',function(update){options.onProgress=update;return engine.createSlices(doc,options.candidates,options);},doc);}catch(error){if(error.code!=='LAYERPILOT_CANCELLED')throw error;r=error.report;stopped=true;if(error.interruptedByInput){sketch.UI.message('已停止自动处理，已完成的修改可用 ⌘Z 撤销');return;}}
  if(!r){sketch.UI.message('已停止，尚未修改切片');return;}
  var changed=r.created+r.updated+r.retired+r.presetsRetired,text='新建 '+r.created+' 个切片 · 更新 '+r.updated+' 个切片\n已有 '+r.unchanged+' 个切片无需变更';
  if(r.retired)text+='\n替换 '+r.retired+' 个旧版切片';
  if(r.presetsRetired)text+='\n停用 '+r.presetsRetired+' 处旧导出设置，避免蓝湖重复资源';
  if(stopped)text+='\n已处理 '+(r.sliceIds.length+r.errors.length)+' / '+options.candidates.length+' 项，其余尚未处理。';
  if(r.errors.length)text+='\n未处理 '+r.errors.length+' 项，原因见下方。已有切片保持原样。';
  if(changed)text+='\n\n'+(stopped?'已保留完成的部分。':'')+'请保存文档，再通过蓝湖插件上传。\n使用 ⌘Z 撤销本次修改。';
  else if(!r.errors.length&&!stopped)text+='\n\n切片已符合当前设置，无需重复创建。';
  dialogs.showResult(stopped?'切片已停止':r.errors.length?'切片处理结果':changed?'切片已就绪':'切片无需变更',text+elapsed(start),r.errors,doc);
 }catch(error){failure('切片未完成',error,doc);}
}
