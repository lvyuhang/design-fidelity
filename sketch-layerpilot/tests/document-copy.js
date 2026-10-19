// Explicit source document ID; never edits the original design.
exports.run=function(root,documentId){
  var s=require('sketch'),e=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/engine.js'),fs=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/files.js');
  var source=s.getDocuments().find(function(d){return d.id===documentId;});
  if(!source)throw new Error('Source document is not open');
  var originals=Array.from(source.selectedPage.layers).filter(function(l){return l.isFrame&&!l.hidden;}).slice(0,2);
  var document=new s.Document(),out=root+'/evidence/private',report={};
  try {
    var copies=originals.map(function(l){var c=s.fromNative(l.sketchObject.copy());c.parent=document.selectedPage;return c;});
    copies.forEach(function(c,i){s.export(c,{output:out,filename:'board-'+i+'-before.png',formats:'png',scales:'1',trimmed:false,overwriting:true});});
    report.organize=e.organize(document);
    var candidates=e.collect(document);
    report.candidates=candidates.assets.length;
    report.slices=e.createSlices(document,candidates.assets,{scales:[1,2,3]});
    copies.forEach(function(c,i){s.export(c,{output:out,filename:'board-'+i+'-after.png',formats:'png',scales:'1',trimmed:false,overwriting:true});});
    report.success=report.candidates>0&&report.slices.created>0&&report.slices.errors.length===0;
  }catch(error){report.success=false;report.error=String(error)+'\n'+String(error.stack||'');}finally{
    fs.writeFileSync(out+'/document-copy-report.json',JSON.stringify(report,null,2));document.close();console.log(JSON.stringify(report));
  }
};
