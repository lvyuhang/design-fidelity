'use strict';
// A compact, nonmodal child panel shows status without dimming the document.
// Editing input is deferred until a safe stop; other windows and scrolling work.
var sketch=require('sketch');
var KEY='local.layerpilot.running.v1';
function cancelled(){var error=new Error('用户停止操作');error.code='LAYERPILOT_CANCELLED';return error;}
function field(text,y,size){var f=NSTextField.alloc().initWithFrame(NSMakeRect(14,y,236,20));f.setStringValue(text);f.setEditable(false);f.setSelectable(false);f.setBezeled(false);f.setDrawsBackground(false);f.setFont(NSFont.systemFontOfSize(size||12));return f;}
function open(title,document,passive){
 var app=NSApplication.sharedApplication(),window=NSPanel.alloc().initWithContentRect_styleMask_backing_defer(NSMakeRect(0,0,320,76),128,2,false),owner=document?document.sketchObject.windowForSheet():null,attached=false,pending=[],stopped=false,closed=false,start=Date.now(),last=0,lastStage='',latest={},pumps=0,maxGap=0,lastPump=Date.now();
 window.setTitle(title);window.setReleasedWhenClosed(false);
 var status=field('正在准备…',46,12),detail=field('正在读取当前选区',25,11);
 window.setHasShadow(true);window.setHidesOnDeactivate(true);window.setBecomesKeyOnlyIfNeeded(true);
 detail.setTextColor(NSColor.secondaryLabelColor());detail.cell().setLineBreakMode(4);
 window.contentView().setToolTip(passive?'整理分段执行；可浏览画布。修改当前文档时会停止自动整理。':'可滚动画布。点击或输入到当前文档时，将先安全停止处理。');
 var bar=NSProgressIndicator.alloc().initWithFrame(NSMakeRect(14,12,292,4));bar.setIndeterminate(true);bar.setUsesThreadedAnimation(true);
 var stop=NSButton.alloc().initWithFrame(NSMakeRect(252,29,58,30));stop.setTitle('停止');stop.setBezelStyle(1);stop.setKeyEquivalent('\u001b');stop.setCOSJSTargetFunction(function(){stopped=true;stop.setEnabled(false);status.setStringValue('正在安全停止…');window.displayIfNeeded();});
 [status,detail,bar,stop].forEach(function(v){window.contentView().addSubview(v);});
 function close(){if(closed)return;closed=true;try{if(attached)owner.removeChildWindow(window);}finally{bar.stopAnimation(null);window.orderOut(null);for(var i=pending.length-1;i>=0;i--)app.postEvent_atStart(pending[i],true);pending=[];}}
 function routeEvent(event){
  var kind=Number(event.type()),number=Number(event.windowNumber());
  var editing=[1,3,10,25].indexOf(kind)>=0;
  var inTarget=owner&&(number===Number(owner.windowNumber())||(!number&&app.keyWindow()&&Number(app.keyWindow().windowNumber())===Number(owner.windowNumber())));
  // Menu/utility clicks may issue editing actions too. Only a known other
  // document window and this status panel may bypass the safe-stop boundary.
  var independent=owner&&sketch.getDocuments().some(function(d){var w=d.sketchObject.windowForSheet();return Number(w.windowNumber())===number&&Number(w.windowNumber())!==Number(owner.windowNumber());});
  var uncertain=owner&&number!==Number(window.windowNumber())&&!independent;
  if(pending.length||(editing&&(inTarget||uncertain))){
   pending.push(event);stopped=true;stop.setEnabled(false);status.setStringValue('正在交还文档操作…');
  }else app.sendEvent(event);
 }
 function pump(milliseconds){
  if(passive){window.displayIfNeeded();return;}
  // Hold modifying input, including its matching up/drag events, until the
  // engine reaches a safe cancellation boundary. Never dispatch a partial edit
  // while a tentative group is waiting for its pixel verification.
  var now=Date.now();maxGap=Math.max(maxGap,now-lastPump);pumps++;
  window.displayIfNeeded();
  if(typeof CATransaction!=='undefined')CATransaction.flush();
  var until=Date.now()+milliseconds;
  do{
   var event=app.nextEventMatchingMask_untilDate_inMode_dequeue(NSEventMaskAny,NSDate.dateWithTimeIntervalSinceNow(Math.max(0,until-Date.now())/1000),NSDefaultRunLoopMode,true);
   if(event)routeEvent(event);
  }while(Date.now()<until);
  app.updateWindows();lastPump=Date.now();
 }
 function update(state){
  state=state||{};var now=Date.now();
  if(!state.heartbeat)latest=Object.assign({},state);
  if(!stopped&&(now-last>=50||state.force)){
   status.setStringValue(latest.stage||'正在处理…');detail.setStringValue(String(latest.name||'').slice(0,100));
   if(latest.total){bar.setIndeterminate(false);bar.setMinValue(0);bar.setMaxValue(latest.total);bar.setDoubleValue(latest.done||0);}else{bar.setIndeterminate(true);bar.startAnimation(null);}
   pump(state.visual?Math.max(0,Math.min(180,Number(state.holdMs)||0)):(state.force?24:8));last=Date.now();lastStage=latest.stage;
  }
  if(stopped){stop.setEnabled(false);status.setStringValue('正在安全停止…');window.displayIfNeeded();if(state.safe!==false)throw stopError();if(Date.now()-last>=50){pump(8);last=Date.now();}}
 }
 function stopError(){var error=cancelled();error.interruptedByInput=pending.length>0;return error;}
 function finish(){
  if(stopped)throw stopError();
  stop.setEnabled(false);status.setStringValue('处理结束');detail.setStringValue('正在打开下一步…');
  if(latest.total)bar.setDoubleValue(latest.total);
  // Hold an actual completion state, rather than flashing then abruptly closing.
  pump(Math.max(120,220-(Date.now()-start)));
  if(stopped)throw stopError();
 }

 try{if(owner&&owner.attachedSheet())throw new Error('当前文档有其他弹窗，请先关闭后重试。');bar.startAnimation(null);if(owner){var f=owner.frame();window.setFrameOrigin(NSMakePoint(f.origin.x+Math.max(8,f.size.width-336),f.origin.y+24));owner.addChildWindow_ordered(window,1);attached=true;window.orderFront(null);}else{window.center();window.orderFront(null);}update({stage:'正在准备…',force:true});}catch(e){close();throw e;}
 return {routeEvent:routeEvent,update:update,close:close,window:window,stopButton:stop,finish:finish,metrics:function(){return {pumps:pumps,maxPumpGapMs:maxGap,pendingInput:pending.length};},elapsed:function(){return (Date.now()-start)/1000;}};
}
function run(title,work,document){
 var dictionary=NSThread.mainThread().threadDictionary();
 if(dictionary.objectForKey(KEY)){var busy=new Error('已有任务正在运行，请等待完成或点击停止。');busy.code='LAYERPILOT_BUSY';throw busy;}
 dictionary.setObject_forKey(true,KEY);var panel;
 try{panel=open(title,document);var result=work(panel.update);panel.finish();return result;}finally{try{if(panel)panel.close();}finally{dictionary.removeObjectForKey(KEY);}}
}
exports.isRunning=function(){return !!NSThread.mainThread().threadDictionary().objectForKey(KEY);};
exports.open=open;exports.run=run;exports.cancelled=cancelled;

// Return from the plugin command, then execute one stable engine phase per tick.
// No nested AppKit event loop, event capture, or synthetic input replay here.
exports.runJob=function(title,createJob,document,done){
 var dictionary=NSThread.mainThread().threadDictionary();
 if(dictionary.objectForKey(KEY))throw new Error('已有任务正在运行');
 dictionary.setObject_forKey(true,KEY);
 var fiber=require('sketch/async').createFiber(),panel,job,timer,finished=false,page=document.selectedPage,checkpoint,model,maxStep=0,steps=0,history=document.sketchObject.historyMaker(),coalescing=false;
 fiber.onCleanup(function(){if(timer)clearTimeout(timer);try{if(job)job.stop();}finally{try{if(coalescing){history.finishCoalescingHistory();coalescing=false;}if(panel)panel.close();}finally{dictionary.removeObjectForKey(KEY);}}});
 function end(error,result){if(finished)return;finished=true;if(error&&job)error.report=job.report;var metrics={steps:steps,maxStepMs:maxStep};fiber.cleanup();done(error,result,metrics);}
 function fingerprint(){
  var parts=[];
  function visit(l){var f=l.frame;parts.push(l.id,l.name,f&&f.x,f&&f.y,f&&f.width,f&&f.height,l.hidden,l.locked,l.type==='Text'?l.text:'');if(l.style)parts.push(String(l.style.sketchObject.immutableModelObject().hash()));if(l.layers)l.layers.forEach(visit);}
  visit(page);return parts.join('|');
 }
 function step(){
  try{
   if(!sketch.getDocuments().some(function(d){return d.id===document.id;})){var closed=cancelled();closed.interruptedByInput=true;end(closed);return;}
   if(model&&!model.isEqual(page.sketchObject.immutableModelObject())&&checkpoint!==fingerprint()){var changed=cancelled();changed.interruptedByInput=true;end(changed);return;}
   panel.update({heartbeat:true});
   var start=Date.now(),next=job.next();maxStep=Math.max(maxStep,Date.now()-start);steps++;
   var after=page.sketchObject.immutableModelObject();if(!model||!model.isEqual(after))checkpoint=fingerprint();model=after;
   if(next.done){end(null,next.value);return;}
   timer=setTimeout(step,8);
  }catch(error){end(error);}
 }
 try{panel=open(title,document,true);job=createJob(panel.update);checkpoint=fingerprint();model=page.sketchObject.immutableModelObject();history.registerHistoryMomentTitle('LayerPilot 自动整理图层');history.startCoalescingHistory();coalescing=true;timer=setTimeout(step,8);}catch(error){end(error);}
 return {stop:function(){if(panel)panel.stopButton.performClick(null);}};
};
