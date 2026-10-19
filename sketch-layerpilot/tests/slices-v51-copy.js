exports.run=function(root,documentId,layerId){
var s=require('sketch'),e=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/engine.js'),files=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/files.js'),canvas=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/canvas.js');
var source=s.getDocuments().find(function(d){return d.id===documentId;}),original=source.getLayerWithID(layerId),d=new s.Document(),out=root+'/evidence/private-v0.5.1',report={checks:[]};files.mkdirSync(out);
function check(name,ok){report.checks.push({name:name,pass:!!ok});if(!ok)throw new Error(name);}
try{
 var before=JSON.stringify(e.snapshot(original)),page=d.selectedPage,symbolPage=new s.Page({parent:d,name:'验证所需组件'}),imported={};
 function preserve(a,b){b.sketchObject.setObjectID(a.id);if(a.layers)a.layers.forEach(function(c,i){preserve(c,b.layers[i]);});}
 function symbols(l){if(l.type==='SymbolInstance'&&l.master&&!imported[l.symbolId]){imported[l.symbolId]=true;var m=l.master,c=s.fromNative(m.sketchObject.copy());preserve(m,c);c.sketchObject.setSymbolID(m.symbolId);c.parent=symbolPage;symbols(m);}if(l.layers)l.layers.forEach(symbols);}
 symbols(original);var board=s.fromNative(original.sketchObject.copy());preserve(original,board);board.parent=page;d.selectedPage=page;
 function render(name){[1,2].forEach(function(scale){s.export(board,{output:out,filename:name+'-'+scale+'x.png',formats:'png',scales:String(scale),trimmed:false,overwriting:true});});}
 render('before');
 var heart=d.getLayerWithID('1A4677DC-5BAD-406C-96F9-B3129B3D50FF');d.selectedLayers.layers=[heart];
 var one=e.collect(d);check('selected existing slice resolves to source glyph',one.assets.length===1);
 report.selectedSlice=e.createSlices(d,one.assets);check('selected slice updated in place to 16',report.selectedSlice.updated===1&&report.selectedSlice.created===0&&heart.frame.width===16);
 var oversized=e.createSlices(d,e.collect(d).assets,{iconSize:24});check('selected heart rejects 24 because external label overlaps',oversized.errors.length===1&&heart.frame.width===16);
 d.selectedLayers.layers=[board];var found=e.collect(d);report.found=found.assets.length;report.slices=e.createSlices(d,found.assets);render('after');
 check('three crowded decorative or badge-adjacent resources are reported',report.slices.errors.length===3&&report.slices.errors.every(function(err){return /邻近文字/.test(err.error);}));
 var targets=['5D31FCDD-4AB5-423C-B24B-A11F87651C2D','3D3BFC62-7658-494E-90F1-D3CE2EA79792','1A4677DC-5BAD-406C-96F9-B3129B3D50FF'];
 targets.forEach(function(id,i){var sl=d.getLayerWithID(id);check('small glyph '+i+' uses 16 SVG',sl&&sl.frame.width===16&&sl.frame.height===16&&sl.exportFormats[0].fileFormat==='svg');['svg','png'].forEach(function(format){s.export(sl,{output:out,filename:['play-a','play-b','heart'][i]+'.'+format,formats:format,scales:'1',trimmed:false,overwriting:true});});});
 var text=d.getLayerWithID('27D2E7AE-C51D-435E-85B7-93BC12BFBB79'),hr=new s.Rectangle(heart.frame).changeBasis({from:heart.parent,to:page}),tr=new s.Rectangle(text.frame).changeBasis({from:text.parent,to:page});
 check('heart slice does not overlap 98 text',!canvas.overlap(hr,tr));
 report.sizes=s.find('Slice',board).map(function(sl){return {name:sl.name,size:sl.frame.width,format:sl.exportFormats[0].fileFormat};});
 report.repeat=e.createSlices(d,e.collect(d).assets);check('repeat produces no new slices or resizing',report.repeat.created===0&&report.repeat.updated===0&&report.repeat.errors.length===3&&report.repeat.unchanged===23);
 check('original document untouched',before===JSON.stringify(e.snapshot(original)));
 report.success=true;d.save(out+'/LayerPilot-0.5.1-切片示例.sketch');
}catch(error){report.success=false;report.error=String(error)+' '+error.stack;}finally{files.writeFileSync(out+'/report.json',JSON.stringify(report,null,2));d.close();console.log(JSON.stringify(report));}
};
