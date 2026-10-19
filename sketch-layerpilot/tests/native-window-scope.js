exports.run=function(root){
 var s=require('sketch'),p=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/progress'),e=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/engine'),ui=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/dialogs'),files=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/files'),d=new s.Document(),other=new s.Document(),panel,result,timer,report={checks:[]};
 function windowID(w){return w?Number(w.windowNumber()):0;}
 function check(name,ok){report.checks.push({name:name,pass:!!ok});if(!ok)throw new Error(name);}
 try{
  var board=new s.Group.Frame({parent:d.selectedPage,name:'目标文档',frame:{x:0,y:0,width:500,height:500}});
  for(var i=0;i<240;i++)new s.ShapePath({parent:board,name:'icon/'+i,frame:{x:(i%10)*40,y:Math.floor(i/10)*40,width:12,height:12},style:{fills:['#000000'],borders:[]}});
  d.selectedLayers.layers=[board];
  var otherLayer=new s.Text({parent:other.selectedPage,text:'其他文档',frame:{x:0,y:0,width:100,height:20}}),actions=0,button=NSButton.alloc().initWithFrame(NSMakeRect(20,20,150,30));button.setTitle('其他窗口交互测试');button.setCOSJSTargetFunction(function(){actions++;otherLayer.name='已响应 '+actions;});other.sketchObject.windowForSheet().contentView().addSubview(button);
  var keyBefore=NSApplication.sharedApplication().keyWindow();panel=p.open('整理状态',d);
  check('progress has no document sheet or dimming',!d.sketchObject.windowForSheet().attachedSheet()&&!other.sketchObject.windowForSheet().attachedSheet());
  check('status is compact',Number(panel.window.frame().size.width)===320&&Number(panel.window.frame().size.height)===76);
  check('status does not steal keyboard focus',windowID(NSApplication.sharedApplication().keyWindow())===windowID(keyBefore));
  check('status belongs to target window',Number(panel.window.parentWindow().windowNumber())===Number(d.sketchObject.windowForSheet().windowNumber()));
  check('no application-wide modal window during work',!NSApplication.sharedApplication().modalWindow());
  timer=NSTimer.timerWithTimeInterval_target_selector_userInfo_repeats(.025,button,'performClick:',null,true);NSRunLoop.currentRunLoop().addTimer_forMode(timer,NSDefaultRunLoopMode);
  var work=e.organize(d,{group:false,rename:false,cleanup:false,sort:false,onProgress:panel.update});
  check('actions in another document run during organization',actions>2&&otherLayer.name==='已响应 '+actions);
  check('organization remains pinned to original document',work.groups===0&&board.layers.length===240&&d.selectedLayers.layers[0].id===board.id);
  timer.invalidate();timer=null;panel.close();panel=null;
  check('progress closes without a residual document lock',!d.sketchObject.windowForSheet().attachedSheet());
  panel=p.open('输入安全交接',d);
  var app=NSApplication.sharedApplication(),owner=d.sketchObject.windowForSheet();
  var key=NSEvent.keyEventWithType_location_modifierFlags_timestamp_windowNumber_context_characters_charactersIgnoringModifiers_isARepeat_keyCode(10,NSMakePoint(0,0),0,0,owner.windowNumber(),null,'x','x',false,7);
  panel.routeEvent(key);
  panel.update({stage:'正在验证分组',safe:false,force:true});
  var interrupted=false;try{panel.update({stage:'安全边界',force:true});}catch(error){interrupted=error.code==='LAYERPILOT_CANCELLED'&&error.interruptedByInput;}
  check('target typing requests safe cancellation',interrupted);
  check('input held during unfinished group',panel.metrics().pendingInput===1);
  panel.close();check('held input queue cleared on close',panel.metrics().pendingInput===0);panel=null;
  var replay=app.nextEventMatchingMask_untilDate_inMode_dequeue(1024,NSDate.dateWithTimeIntervalSinceNow(.01),NSDefaultRunLoopMode,true);
  // Drain any replayed fixture key; inactive applications may discard key events.
  if(replay)check('replayed event targets original document',String(replay.characters())==='x'&&Number(replay.windowNumber())===Number(owner.windowNumber()));
  check('child status window is removed',!owner.childWindows()||Number(owner.childWindows().count())===0);
  result=ui.showResult('完成','测试结果面板',[],d);
  check('completion does not lock the whole application',!!d.sketchObject.windowForSheet().attachedSheet()&&!NSApplication.sharedApplication().modalWindow());
  var count=actions;button.performClick(null);check('other document actions still work with result open',actions===count+1);
  result.panel.alert.buttons()[0].performClick(null);result=null;check('result button dismisses sheet',!d.sketchObject.windowForSheet().attachedSheet());
  report.success=true;report.otherWindowActions=actions;
 }catch(error){report.success=false;report.error=String(error)+' '+error.stack;}finally{if(timer)timer.invalidate();if(panel)panel.close();if(result)result.close();other.close();d.close();files.writeFileSync(root+'/evidence/window-scope-report.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));}
};
