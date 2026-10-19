exports.run=function(root,documentId,layerId,oldRoot){
  var s=require('sketch'),e=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/engine.js'),files=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/files.js');
  var source=s.getDocuments().find(function(d){return d.id===documentId;}),original=source.getLayerWithID(layerId),d=new s.Document(),out=root+'/evidence/private-v0.5.0'+(oldRoot?'-upgrade':''),report={};
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
    function render(name){s.export(layer,{output:out,filename:name+'.png',formats:'png',scales:'1',overwriting:true,trimmed:false});s.export(layer,{output:out,filename:name+'-2x.png',formats:'png',scales:'2',overwriting:true,trimmed:false});}
    var resourcesBefore=e.collect(d).assets.map(function(a){return a.node.id;}).sort();
    render('regions-before');report.before=layer.layers.length;
    var cardBackgrounds=[39,41,42,4,15].map(function(i){return layer.layers[i];});
    var tabs=[[20,23],[21,24],[22,25],[29,28],[31,27]].map(function(pair){return pair.map(function(i){return layer.layers[i];});});
    if(oldRoot){var oldEngine=require(oldRoot+'/Contents/Sketch/lib/engine');report.oldOrganize=oldEngine.organize(d);report.oldSlices=oldEngine.createSlices(d,oldEngine.collect(d).assets,{scales:[1,2,3]});d.selectedLayers.layers=[layer];}
    files.writeFileSync(out+'/regions-input.json',JSON.stringify(e.snapshot(layer),null,2));
    var started=Date.now();report.result=e.organize(d);report.organizeMilliseconds=Date.now()-started;report.after=layer.layers.length;
    render('regions-after');
    report.hierarchy=layer.layers.map(function(l){return {name:l.name,type:l.type,count:l.layers?l.layers.length:0};});
    files.writeFileSync(out+'/region-snapshot.json',JSON.stringify(e.snapshot(layer),null,2));
    report.completeCardBackgrounds=cardBackgrounds.every(function(bg){return bg.parent.id!==layer.id&&/^内容卡片/.test(bg.parent.name);});
    report.tabPairs=tabs.every(function(pair){for(var p=pair[0].parent;p&&p.id!==layer.id;p=p.parent){if(p.id===pair[1].parent.id)return true;}return false;});
    report.repeat=e.organize(d);
    var found=e.collect(d);report.resourcesBefore=resourcesBefore.length;report.resourcesAfter=found.assets.length;
    report.slices=e.createSlices(d,found.assets,{scales:[1,2,3]});
    var large=found.assets.filter(function(a){return report.slices.errors.some(function(err){return err.name===a.node.name;});});
    report.largeSlices=e.createSlices(d,large,{iconSize:32});render('regions-sliced');
    report.assets=found.assets.map(function(a){return {name:a.node.name,kind:a.kind,width:a.node.width,height:a.node.height};});
    report.slices.sliceIds.concat(report.largeSlices.sliceIds).forEach(function(id,i){var sl=d.getLayerWithID(id);if(sl.exportFormats[0].fileFormat==='svg')s.export(sl,{output:out,filename:'icon-'+i+'.svg',formats:'svg',overwriting:true,trimmed:false});});
    report.sliceRepeat=e.createSlices(d,e.collect(d).assets.filter(function(a){return !large.some(function(l){return l.node.id===a.node.id;});}),{scales:[1,2,3]});
    report.largeRepeat=e.createSlices(d,large,{iconSize:32});
    report.finalSliceCount=s.find('Slice',layer).length;
    report.originalUntouched=sourceSnapshot===JSON.stringify(e.snapshot(original));
    report.success=report.finalSliceCount===found.assets.length&&report.originalUntouched&&report.completeCardBackgrounds&&report.tabPairs&&report.largeSlices.errors.length===0&&report.sliceRepeat.errors.length===0&&report.sliceRepeat.created===0&&report.sliceRepeat.updated===0&&report.largeRepeat.created===0&&report.largeRepeat.updated===0&&report.largeRepeat.errors.length===0;
    d.save(out+'/LayerPilot-Organized-Preview.sketch');
  }catch(error){report.success=false;report.error=String(error)+'\n'+String(error.stack||'');}finally{files.writeFileSync(out+'/regions-report.json',JSON.stringify(report,null,2));d.close();console.log(JSON.stringify(report));}
};
