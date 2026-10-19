exports.run=function(root){
  var s=require('sketch'),e=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/engine.js'),files=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/files.js');
  var d=new s.Document(),out=root+'/evidence',report={checks:[]};
  function check(name,pass){report.checks.push({name:name,pass:!!pass});if(!pass)throw new Error(name);}
  function rect(parent,name,x,y,w,h,color){return new s.ShapePath({parent:parent,name:name,frame:{x:x,y:y,width:w,height:h},style:{fills:[color],borders:[]}});}
  function exportTest(layer,name){s.export(layer,{output:out,filename:name+'.png',formats:'png',scales:'1',trimmed:false,overwriting:true});}
  try{
    var f=new s.Group.Frame({parent:d.selectedPage,name:'slice regression',frame:{x:0,y:0,width:300,height:200},style:{fills:['#0055ff']}});f.breaksMaskChain=true;
    var icon=new s.Group({parent:f,name:'icon/test',frame:{x:20,y:20,width:40,height:40},layers:[]});
    rect(icon,'red',10,10,20,20,'#ff0000');
    var photo=new s.Image({parent:f,name:'photo/test',image:out+'/fixture.png',frame:{x:100,y:20,width:80,height:80}});
    var maskGroup=new s.Group({parent:f,name:'photo/masked',frame:{x:200,y:20,width:40,height:40},layers:[]});
    var mask=rect(maskGroup,'mask',0,0,40,40,'#ffffff');mask.masksSiblings=true;
    new s.Image({parent:maskGroup,name:'Image',image:out+'/fixture.png',frame:{x:0,y:0,width:80,height:80}});
    exportTest(f,'slices-before');
    var found=e.collect(d);check('three resources recognized',found.assets.length===3);
    var exportOriginal=s.export;s.export=function(){throw new Error('createSlices must not export files');};
    try{report.first=e.createSlices(d,found.assets,{scales:[1,2,3],svg:false,iconSize:0});}finally{s.export=exportOriginal;}
    check('created actual slices without exporting',report.first.created===3&&report.first.errors.length===0);
    check('native slice types and presets',report.first.sliceIds.every(function(id){var l=d.getLayerWithID(id);return l.type==='Slice'&&l.exportFormats.length===3&&Number(l.sketchObject.exportOptions().layerOptions())===2;}));
    exportTest(f,'slices-after');
    check('leaf placed in isolated group',photo.parent.id!==f.id&&photo.parent.layers.length===2);
    var again=e.collect(d);check('slice children do not change recognition',again.assets.length===3);
    var repeat=e.createSlices(d,again.assets,{scales:[1,2,3],svg:false,iconSize:0});check('repeated command does not duplicate slices',repeat.created===0&&repeat.updated===0&&repeat.unchanged===3);
    var byParent={};report.first.sliceIds.forEach(function(id){var l=d.getLayerWithID(id);byParent[l.parent.id]=l;});
    exportTest(byParent[icon.id],'slice-icon');exportTest(byParent[photo.parent.id],'slice-photo');exportTest(byParent[maskGroup.id],'slice-mask');
    icon.frame.width=48;
    var changed=e.createSlices(d,e.collect(d).assets,{scales:[2],svg:false,iconSize:0});
    check('refreshes bounds and selected scales',changed.created===0&&changed.updated===3&&byParent[icon.id].frame.width===48&&byParent[icon.id].exportFormats.length===1&&byParent[icon.id].exportFormats[0].size==='2x');
    var manual=new s.Slice({parent:f,name:'manual',frame:{x:0,y:150,width:20,height:20},exportFormats:[{fileFormat:'jpg',size:'1x'}]});
    e.createSlices(d,e.collect(d).assets,{scales:[2],svg:false,iconSize:0});check('manual slices preserved',manual.name==='manual'&&manual.exportFormats[0].fileFormat==='jpg');
    report.success=true;
  }catch(error){report.success=false;report.error=String(error)+'\n'+String(error.stack||'');}finally{
    files.writeFileSync(out+'/slices-report.json',JSON.stringify(report,null,2));d.close();console.log(JSON.stringify(report));
  }
};
