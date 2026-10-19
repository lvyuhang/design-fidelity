exports.run=function(root){
 var s=require('sketch'),files=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/files'),d=new s.Document(),report={},panel;
 try{
  var board=new s.Group.Frame({parent:d.selectedPage,name:'刷新间隔测试',frame:{x:0,y:0,width:600,height:600}});
  for(var i=0;i<120;i++)new s.ShapePath({parent:board,name:'icon/'+i,frame:{x:(i%12)*40,y:Math.floor(i/12)*40,width:20,height:20},style:{fills:['#000000'],borders:[]}});
  d.selectedLayers.layers=[board];
  ['before','after'].forEach(function(label){
   var base=root+(label==='before'?'/evidence/development-baseline-0.5.2/LayerPilot.sketchplugin':'/LayerPilot.sketchplugin')+'/Contents/Sketch/lib/',e=require(base+'engine'),p=require(base+'progress');
   var start=Date.now(),last=start,maxGap=0,calls=0;
   panel=p.open('LayerPilot · 刷新间隔验证');
   var r=e.organize(d,{group:false,rename:false,cleanup:false,sort:false,onProgress:function(state){var now=Date.now();maxGap=Math.max(maxGap,now-last);last=now;calls++;panel.update(state);}});
   report[label]={elapsedMs:Date.now()-start,maxCallbackGapMs:maxGap,callbacks:calls,mutations:r.groups+r.sorted+r.renamed+r.removed,window:panel.metrics?panel.metrics():null};panel.close();panel=null;
  });
  report.success=report.after.mutations===0&&report.before.mutations===0&&report.after.callbacks>report.before.callbacks&&report.after.maxCallbackGapMs<report.before.maxCallbackGapMs;
 }catch(error){report.success=false;report.error=String(error)+' '+error.stack;}finally{if(panel)panel.close();d.close();files.writeFileSync(root+'/evidence/responsiveness-report.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));}
};
