exports.run=function(root,label){
 var p=require(root+(label==='before'?'/evidence/development-baseline-0.5.2/progress.js':'/LayerPilot.sketchplugin/Contents/Sketch/lib/progress.js')),fs=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/files'),events=NSMutableArray.array(),timer=NSTimer.timerWithTimeInterval_target_selector_userInfo_repeats(.016,events,'addObject:',null,true);
 NSRunLoop.currentRunLoop().addTimer_forMode(timer,NSDefaultRunLoopMode);
 var report={label:label};
 try{p.run('LayerPilot · 渲染时序诊断',function(update){var start=Date.now();while(Date.now()-start<900){var slice=Date.now();while(Date.now()-slice<5){}update({stage:'时序诊断',name:'900ms 可分段工作'});}report.elapsed=Date.now()-start;report.beatsDuringWork=Number(events.count());});report.beats=Number(events.count());report.success=true;}catch(error){report.success=false;report.error=String(error)+' '+error.stack;}finally{timer.invalidate();events.removeAllObjects();fs.writeFileSync(root+'/evidence/progress-heartbeat-'+label+'.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));}
};
