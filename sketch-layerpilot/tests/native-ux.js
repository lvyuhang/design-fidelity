exports.run=function(root){
 var s=require('sketch'),e=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/engine'),p=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/progress'),ui=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/dialogs'),files=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/files'),d=new s.Document(),report={checks:[]},panel;
 function check(name,ok){report.checks.push({name:name,pass:!!ok});if(!ok)throw new Error(name);}
 try{
  var board=new s.Group.Frame({parent:d.selectedPage,name:'UX fixture',frame:{x:0,y:0,width:500,height:200}}),icons=[];
  for(var i=0;i<5;i++)icons.push(new s.ShapePath({parent:board,name:'icon/'+i,frame:{x:30+i*80,y:40,width:12,height:12},style:{fills:['#ff0000'],borders:[]}}));d.selectedLayers.layers=[board];
  var original=JSON.stringify(e.snapshot(board)),found,ticks=0;
  found=p.run('LayerPilot · 验证识别反馈',function(update){return e.collect(d,{onProgress:function(state){ticks++;update(state);}});});
  check('identification reports per-layer progress without document mutations',ticks>=6&&original===JSON.stringify(e.snapshot(board)));
  check('progress modal releases after success',!NSApplication.sharedApplication().modalWindow());
  var events=NSMutableArray.array(),timer=NSTimer.timerWithTimeInterval_target_selector_userInfo_repeats(.016,events,'addObject:',null,true),workBeats=0;
  NSRunLoop.currentRunLoop().addTimer_forMode(timer,NSDefaultRunLoopMode);
  try{p.run('验证真实事件循环刷新',function(update){var start=Date.now();while(Date.now()-start<350){var chunk=Date.now();while(Date.now()-chunk<5){}update({stage:'正在刷新'});}workBeats=Number(events.count());});}finally{timer.invalidate();events.removeAllObjects();}
  check('normal event loop runs native timer sources during CPU work',workBeats>=8);

  var guarded=p.run('验证重复启动保护',function(){try{p.run('不应启动',function(){});}catch(err){return err.code==='LAYERPILOT_BUSY';}});check('concurrent work is rejected without replacing active window',guarded);
  panel=p.open('LayerPilot · 验证停止');check('progress visible immediately',panel.window.isVisible());panel.stopButton.performClick(null);
  panel.update({stage:'正在核对画面',safe:false,force:true});var cancelled=false;try{panel.update({stage:'安全停止点',force:true});}catch(err){cancelled=err.code==='LAYERPILOT_CANCELLED';}panel.close();panel=null;
  check('stop is deferred until a safe checkpoint',cancelled&&!NSApplication.sharedApplication().modalWindow());
  try{p.run('验证异常清理',function(){throw new Error('test failure');});}catch(err){}
  var again=p.run('验证重新运行',function(update){update({stage:'完成'});return true;});check('error closes progress and releases running guard',again&&!NSApplication.sharedApplication().modalWindow());
  var partial;try{p.run('验证切片停止',function(update){return e.createSlices(d,found.assets,{onProgress:function(state){update(state);if(state.done===2)throw p.cancelled();}});});}catch(err){partial=err;}
  check('cancellation returns completed slice counts',partial&&partial.code==='LAYERPILOT_CANCELLED'&&partial.report.created===2&&s.find('Slice',board).length===2);
  check('cancellation restores original selection',d.selectedLayers.layers.length===1&&d.selectedLayers.layers[0].id===board.id);
  check('unprocessed source layers keep original parent',icons.slice(2).every(function(l){return l.parent.id===board.id;}));
  var finished=e.createSlices(d,e.collect(d).assets,{svg:true,scales:[]});check('SVG-only accepts no PNG scales and resumes without duplicates',finished.created===3&&finished.unchanged===2&&!finished.errors.length&&s.find('Slice',board).length===5);
  var settings=require('sketch/settings'),prefKey='layerpilot.ui.assets',oldPref=settings.settingForKey(prefKey),restored;
  try{settings.setSettingForKey(prefKey,{scales:[2],svg:false,iconSize:32});restored=ui.buildAssets({scope:'已保存设置',assets:found.assets}).read();}finally{settings.setSettingForKey(prefKey,oldPref===undefined?null:oldPref);}
  check('saved output preferences restore without persisting resource selection',restored.scales.length===1&&restored.scales[0]===2&&!restored.svg&&restored.iconSize===32&&restored.candidates.length===5);
  var panelUI=ui.buildAssets({scope:'UX fixture',assets:found.assets});panelUI.fields.none.performClick(null);check('select none prevents empty execution without closing settings',panelUI.read().candidates.length===0&&!panelUI.alert.buttons()[0].isEnabled());
  panelUI.fields.all.performClick(null);panelUI.fields.scales.forEach(function(b){b.setState(0);});panelUI.update();check('all restores selection and SVG-only validation accepts zero PNG scales',panelUI.read().candidates.length===5&&panelUI.alert.buttons()[0].isEnabled());
  panelUI.fields.svg.setState(0);panelUI.update();check('PNG validation explains missing scales in place',!panelUI.alert.buttons()[0].isEnabled()&&String(panelUI.validation.stringValue()).indexOf('PNG')>=0);
  panelUI.fields.scales[0].setState(1);panelUI.update();check('correcting scale keeps selections and re-enables action',panelUI.alert.buttons()[0].isEnabled()&&panelUI.read().candidates.length===5);
  var errors=Array.from({length:20},function(_,i){return {id:icons[0].id,name:'资源 '+i,error:'空间不足，请调整图层间距'};}),result=ui.buildResult('切片结果','20 项未处理',errors,d);check('full error list remains selectable and is not truncated at eight',result.full.indexOf('资源 19')>=0&&result.textView.isSelectable()&&Number(result.textView.frame().size.height)>190);
  ui.locate(d,[icons[4].id]);check('locate selects affected layer',d.selectedLayers.layers[0].id===icons[4].id);
  d.selectedLayers.layers=[board];var names=icons.map(function(l){return l.name;}),visits=0,organizeCancel;try{e.organize(d,{onProgress:function(){if(++visits===2)throw p.cancelled();}});}catch(err){organizeCancel=err;}check('organize cancellation carries report and preserves selection',organizeCancel&&organizeCancel.report&&d.selectedLayers.layers[0].id===board.id);
  report.success=true;
 }catch(err){report.success=false;report.error=String(err)+' '+err.stack;}finally{if(panel)panel.close();files.writeFileSync(root+'/evidence/ux-native-report.json',JSON.stringify(report,null,2));d.close();console.log(JSON.stringify(report));}
};
