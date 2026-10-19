exports.run=function(root){
 var s=require('sketch'),e=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/engine'),p=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/progress'),fs=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/files'),d=new s.Document(),report={checks:[]};
 function check(name,ok){report.checks.push({name:name,pass:!!ok});if(!ok)throw new Error(name);}
 function fixture(){var f=new s.Group.Frame({parent:d.selectedPage,name:'Visual fixture',frame:{x:0,y:0,width:400,height:400}});for(var i=0;i<2;i++){new s.ShapePath({parent:f,name:'Rectangle',frame:{x:i*200,y:80,width:180,height:220},style:{fills:['#ffffff'],borders:[]}});new s.Text({parent:f,text:'卡片 '+i,frame:{x:i*200+20,y:120,width:100,height:30}});}d.selectedLayers.layers=[f];return f;}
 try{
  var f=fixture(),events=[],budget=0,before=s.export(f,{output:false,formats:'png',scales:'1'});
  var r=p.run('归组可视化测试',function(update){return e.organize(d,{onProgress:function(state){if(state.visual){events.push(state);budget+=state.holdMs;check('selection matches '+state.visual,d.selectedLayers.layers.map(function(l){return l.id;}).join()===state.layerIds.join());if(state.visual==='grouped')check('completed group exists',d.getLayerWithID(state.layerIds[0]).layers.length>1);}update(state);}});},d);
  check('both member and committed group feedback',events.some(function(v){return v.visual==='members';})&&events.some(function(v){return v.visual==='grouped';})&&r.groups>0);
  check('visual hold budget bounded',budget<=2400);
  check('original selection restored',d.selectedLayers.layers.length===1&&d.selectedLayers.layers[0].id===f.id);
  check('render unchanged',before.equals(s.export(f,{output:false,formats:'png',scales:'1'})));
  f=fixture();var visuals=0;e.organize(d,{visualize:false,onProgress:function(v){if(v.visual)visuals++;}});check('visualization can be disabled',visuals===0);
  f=fixture();var stopped=false;try{e.organize(d,{onProgress:function(v){if(v.visual==='members')throw p.cancelled();}});}catch(error){stopped=error.code==='LAYERPILOT_CANCELLED'&&error.report.groups===0;}
  check('stop before grouping is safe',stopped&&f.layers.length===4&&d.selectedLayers.layers[0].id===f.id);
  report.success=true;
 }catch(error){report.success=false;report.error=String(error)+' '+error.stack;}finally{d.close();fs.writeFileSync(root+'/evidence/visual-native-report.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));}
};
