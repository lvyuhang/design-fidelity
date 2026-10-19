// Each stage is a separate sketchtool invocation: Sketch commits history at command end.
function deps(root){return {s:require('sketch'),e:require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/engine.js'),fs:require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/files.js')};}
function state(root){return JSON.parse(String(NSString.stringWithContentsOfFile_encoding_error(root+'/evidence/undo-state.json',4,null)));}
function doc(s,id){return s.getDocuments().find(function(d){return d.id===id;});}
exports.prepare=function(root){
  var x=deps(root),d=new x.s.Document();
  var f=new x.s.Group.Frame({parent:d.selectedPage,name:'Undo fixture',frame:{x:0,y:0,width:400,height:400}});
  [0,200].forEach(function(left){new x.s.ShapePath({parent:f,name:'Rectangle',frame:{x:left,y:90,width:180,height:220},style:{fills:['#ffffff'],borders:[]}});});
  var a=new x.s.ShapePath({parent:f,name:'icon/a',frame:{x:20,y:120,width:20,height:20},style:{fills:['#ff0000'],borders:[]}});
  var b=new x.s.ShapePath({parent:f,name:'icon/b',frame:{x:44,y:120,width:20,height:20},style:{fills:['#00ff00'],borders:[]}});
  var t=new x.s.Text({parent:f,name:'Text 99',text:'撤销测试',frame:{x:210,y:200,width:120,height:20},style:{fontSize:20}});
  x.fs.writeFileSync(root+'/evidence/undo-state.json',JSON.stringify({document:d.id,frame:f.id,a:a.id,b:b.id,label:t.id}));
  d.sketchObject.historyMaker().registerHistoryMomentTitle('Create test fixture');
  d.sketchObject.historyMaker().makeHistoryIfNecessary();
  d.sketchObject.historyMaker().flush();
};
exports.apply=function(root){
  var x=deps(root),st=state(root),d=doc(x.s,st.document),progress=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/progress');
  var report=progress.run('验证整理进度与撤销',function(update){return x.e.organize(d,{onProgress:update});},d);
  st.renamed=d.getLayerWithID(st.label).name==='文本 / 撤销测试';st.grouped=report.regions.length===2;
  x.fs.writeFileSync(root+'/evidence/undo-state.json',JSON.stringify(st));d.sketchObject.historyMaker().makeHistoryIfNecessary();d.sketchObject.historyMaker().flush();
};
exports.verifyOrganize=function(root){
 var x=deps(root),st=state(root),d=doc(x.s,st.document),h=d.sketchObject.historyMaker();
 h.moveDocument_throughHistoryBackInTime(d.sketchObject.documentData(),true);
 st.organizeRestored=d.getLayerWithID(st.label).name==='Text 99'&&d.getLayerWithID(st.a).parent.id===st.frame&&d.getLayerWithID(st.b).parent.id===st.frame&&d.getLayerWithID(st.frame).layers.length===5;
 x.fs.writeFileSync(root+'/evidence/undo-state.json',JSON.stringify(st));
};
exports.applySlices=function(root){
 var x=deps(root),st=state(root),d=doc(x.s,st.document),progress=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/progress');d.selectedLayers.layers=[d.getLayerWithID(st.frame)];
 try{progress.run('验证停止与撤销',function(update){return x.e.createSlices(d,x.e.collect(d).assets,{scales:[1,2,3],onProgress:function(state){update(state);if(state.done===1)throw progress.cancelled();}});},d);}catch(error){if(error.code!=='LAYERPILOT_CANCELLED')throw error;st.slicesCreated=error.report.created;st.stopped=true;}
 x.fs.writeFileSync(root+'/evidence/undo-state.json',JSON.stringify(st));d.sketchObject.historyMaker().makeHistoryIfNecessary();d.sketchObject.historyMaker().flush();
};
exports.verify=function(root){
 var x=deps(root),st=state(root),d=doc(x.s,st.document),report={renamed:st.renamed,grouped:st.grouped,organizeRestoredInOneUndo:st.organizeRestored};
 try{
  var h=d.sketchObject.historyMaker();report.canUndo=Boolean(h.canMoveThroughHistoryBackInTime(true));h.moveDocument_throughHistoryBackInTime(d.sketchObject.documentData(),true);
  report.nameRestored=d.getLayerWithID(st.label).name==='Text 99';report.structureRestored=d.getLayerWithID(st.a).parent.id===st.frame&&d.getLayerWithID(st.b).parent.id===st.frame&&d.getLayerWithID(st.frame).layers.length===5;
  report.stopped=st.stopped;report.slicesRemoved=st.slicesCreated===1&&x.s.find('Slice',d).length===0;
  report.success=report.organizeRestoredInOneUndo&&report.stopped&&report.renamed&&report.grouped&&report.canUndo&&report.nameRestored&&report.structureRestored&&report.slicesRemoved;
 }catch(error){report.success=false;report.error=String(error);}finally{x.fs.writeFileSync(root+'/evidence/undo-report.json',JSON.stringify(report,null,2));d.close();console.log(JSON.stringify(report));}
};
