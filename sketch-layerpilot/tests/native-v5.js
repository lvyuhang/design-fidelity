exports.run=function(root){
var s=require('sketch'),settings=require('sketch/settings'),e=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/engine'),fs=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/files'),d=new s.Document(),out=root+'/evidence',report={checks:[]};
function check(name,ok){report.checks.push({name:name,pass:!!ok});if(!ok)throw new Error(name);}
function rect(parent,name,x,y,w,h,color){return new s.ShapePath({parent:parent,name:name,frame:{x:x,y:y,width:w,height:h},style:{fills:[color||'#000000'],borders:[]}});}
function render(layer,name,format){s.export(layer,{output:out,filename:name+'.'+(format||'png'),formats:format||'png',scales:'1',trimmed:false,overwriting:true});}
try{
 var f=new s.Group.Frame({parent:d.selectedPage,name:'v5',frame:{x:0,y:0,width:375,height:812},style:{fills:['#f0f0f0']}});d.selectedLayers.layers=[f];
 var nav=new s.Group({parent:f,name:'底部导航',frame:{x:12,y:735,width:351,height:56},layers:[]});settings.setLayerSettingForKey(nav,'layerpilot.generated.v1',true);settings.setLayerSettingForKey(nav,'layerpilot.region.v1',true);
 rect(nav,'background',0,0,351,56,'#ffffff');var items=[];
 for(var i=0;i<5;i++){var icon=rect(nav,'icon/tab '+i,22+i*65,6,18,18),label=new s.Text({parent:nav,name:'Tab '+i,text:'菜单',frame:{x:18+i*65,y:30,width:26,height:14},style:{fontSize:12,textColor:'#000000'}});items.push({icon:icon,label:label});}
 var button=new s.Group({parent:f,name:'icon/notification button',frame:{x:40,y:80,width:36,height:36},layers:[]});var bg=rect(button,'white circle',0,0,36,36,'#ffffff');bg.shapeType=s.ShapePath.ShapeType.Oval;
 var glyph=new s.Group({parent:button,name:'icon/bell',frame:{x:12,y:10,width:12,height:16},layers:[]});rect(glyph,'glyph',0,0,12,16,'#111111');
 button.exportFormats=[{fileFormat:'png',size:'2x'}];
 var old=new s.Slice({parent:button,name:'old button',frame:{x:0,y:0,width:36,height:36}});settings.setLayerSettingForKey(old,'layerpilot.sliceSource.v1',button.id);
 var manual=new s.Slice({parent:button,name:'manual',frame:{x:0,y:0,width:36,height:36},exportFormats:[{fileFormat:'jpg',size:'1x'}]});
 render(f,'v5-before');var r=e.organize(d);
 check('refines previous generated navigation into five icon-label groups',items.every(function(p){return p.icon.parent.id===p.label.parent.id&&p.icon.parent.id!==nav.id;}));
 var again=e.organize(d);check('recursive grouping is idempotent',!again.groups&&!again.renamed&&!again.sorted);
 var found=e.collect(d);check('button source is glyph, not white surface',found.assets.some(function(a){return a.node.id===glyph.id;})&&!found.assets.some(function(a){return a.node.id===button.id||a.node.id===bg.id;}));
 var savedExport=s.export;s.export=function(){throw new Error('Slices must not export files');};var slices;try{slices=e.createSlices(d,found.assets);}finally{s.export=savedExport;}
 check('default slices complete with SVG presets',slices.errors.length===0&&slices.created===6&&slices.retired===1);
 check('old button export preset retired without removing manual slice',button.exportFormats.length===0&&slices.presetsRetired===1);
 check('manual slice unchanged',d.getLayerWithID(manual.id)&&manual.exportFormats[0].fileFormat==='jpg');
 check('all SVG canvases are exactly 24 square and untrimmed',slices.sliceIds.every(function(id){var sl=d.getLayerWithID(id);return sl.frame.width===24&&sl.frame.height===24&&sl.exportFormats[0].fileFormat==='svg'&&!sl.sketchObject.exportOptions().shouldTrim();}));
 render(f,'v5-after');var gs=d.getLayerWithID(slices.sliceIds.find(function(id){return d.getLayerWithID(id).parent.id===glyph.id;}));render(gs,'v5-glyph');render(gs,'v5-glyph','svg');
 check('background remains in design outside glyph slice',bg.parent.id===button.id&&gs.parent.id===glyph.id);
 var repeat=e.createSlices(d,e.collect(d).assets);check('repeat does not grow canvases or duplicate',repeat.created===0&&repeat.updated===0&&repeat.unchanged===6&&!repeat.errors.length);
 var resized=e.createSlices(d,e.collect(d).assets,{iconSize:32});report.resized=resized;check('canvas change updates clear glyph and refuses five text collisions',resized.updated===1&&resized.created===0&&resized.errors.length===5);
 var tooSmall=e.createSlices(d,e.collect(d).assets,{iconSize:16});check('oversized glyphs rejected without scaling drawing',tooSmall.errors.length===5&&items.every(function(p){return p.icon.frame.width===18;}));
 var quote=new s.Group({parent:f,name:'quote glyph',frame:{x:160,y:120,width:18,height:15},layers:[]});var leaf=rect(quote,'icon/quote',0,0,18,15,'#000000');var nested=new s.Slice({parent:quote,name:'old nested',frame:{x:0,y:0,width:18,height:15}});settings.setLayerSettingForKey(nested,'layerpilot.sliceSource.v1',leaf.id);
 d.selectedLayers.layers=[quote];var replacement=e.createSlices(d,e.collect(d).assets);check('one-child icon upgrade removes redundant nested auto slice',replacement.created===1&&replacement.retired===1&&s.find('Slice',quote).length===1);
 report.success=true;
}catch(error){report.success=false;report.error=String(error)+' '+error.stack;}finally{fs.writeFileSync(out+'/v5-native-report.json',JSON.stringify(report,null,2));d.close();console.log(JSON.stringify(report));}
};
