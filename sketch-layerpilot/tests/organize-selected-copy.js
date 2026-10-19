exports.run=function(root,documentId,layerId){
  var s=require('sketch'),e=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/engine.js'),files=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/files.js');
  var source=s.getDocuments().find(function(d){return d.id===documentId;}),original=source.getLayerWithID(layerId),d=new s.Document(),out=root+'/evidence/private-v0.4.0',report={};
  files.mkdirSync(out);
  try{
    var sourceSnapshot=JSON.stringify(e.snapshot(original));
    s.export(original,{output:out,filename:'regions-original.png',formats:'png',scales:'1',overwriting:true,trimmed:false});
    var targetPage=d.selectedPage,symbolPage=new s.Page({parent:d,name:'验证所需组件'}),imported={};
    function preserveIds(a,b){b.sketchObject.setObjectID(a.id);if(a.layers)a.layers.forEach(function(c,i){preserveIds(c,b.layers[i]);});}
    function importSymbols(layer){
      if(layer.type==='SymbolInstance'&&layer.master&&!imported[layer.symbolId]){
        imported[layer.symbolId]=true;var master=layer.master,copy=s.fromNative(master.sketchObject.copy());
        preserveIds(master,copy);copy.sketchObject.setSymbolID(master.symbolId);copy.parent=symbolPage;importSymbols(master);
      }
      if(layer.layers)layer.layers.forEach(importSymbols);
    }
    importSymbols(original);
    var layer=s.fromNative(original.sketchObject.copy());layer.parent=targetPage;d.selectedPage=targetPage;d.selectedLayers.layers=[layer];
    function render(name){s.export(layer,{output:out,filename:name+'.png',formats:'png',scales:'1',overwriting:true,trimmed:false});}
    var resourcesBefore=e.collect(d).assets.map(function(a){return a.node.id;}).sort();
    render('regions-before');report.before=layer.layers.length;
    files.writeFileSync(out+'/regions-input.json',JSON.stringify(e.snapshot(layer),null,2));
    var started=Date.now();report.result=e.organize(d);report.organizeMilliseconds=Date.now()-started;report.after=layer.layers.length;
    render('regions-after');
    report.hierarchy=layer.layers.map(function(l){return {name:l.name,type:l.type,count:l.layers?l.layers.length:0};});
    files.writeFileSync(out+'/region-snapshot.json',JSON.stringify(e.snapshot(layer),null,2));
    report.repeat=e.organize(d);
    var found=e.collect(d);report.resourcesPreserved=JSON.stringify(resourcesBefore)===JSON.stringify(found.assets.map(function(a){return a.node.id;}).sort());
    report.slices=e.createSlices(d,found.assets,{scales:[1,2,3]});render('regions-sliced');
    report.sliceRepeat=e.createSlices(d,e.collect(d).assets,{scales:[1,2,3]});
    report.originalUntouched=sourceSnapshot===JSON.stringify(e.snapshot(original));
    report.success=report.originalUntouched&&report.resourcesPreserved&&report.slices.errors.length===0&&report.sliceRepeat.created===0;
    d.save(out+'/LayerPilot-Organized-Preview.sketch');
  }catch(error){report.success=false;report.error=String(error)+'\n'+String(error.stack||'');}finally{files.writeFileSync(out+'/regions-report.json',JSON.stringify(report,null,2));d.close();console.log(JSON.stringify(report));}
};
