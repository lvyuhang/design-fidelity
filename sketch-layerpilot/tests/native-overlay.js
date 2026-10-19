exports.run=function(root){
 var s=require('sketch'),settings=require('sketch/settings'),e=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/engine'),fs=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/files'),d=new s.Document(),report={checks:[]};
 function check(name,pass){report.checks.push({name:name,pass:!!pass});if(!pass)throw new Error(name);}
 function rect(parent,name,x,y,w,h){return new s.ShapePath({parent:parent,name:name,frame:{x:x,y:y,width:w,height:h},style:{fills:['#ffffff'],borders:[]}});}
 function under(layer,parent){for(var a=layer.parent;a;a=a.parent)if(a.id===parent.id)return true;return false;}
 function label(parent,text,x,y){return new s.Text({parent:parent,name:text,text:text,frame:{x:x,y:y,width:26,height:18},style:{fontSize:12}});}
 try{
  var f=new s.Group.Frame({parent:d.selectedPage,frame:{x:0,y:0,width:375,height:812}}),card=rect(f,'card',190,615,177,190);label(f,'底层卡片',210,650);
  var dim=rect(f,'dim',0,0,375,812);dim.style.fills=['#88888888'];rect(f,'sheet',0,538,375,274);
  var a=rect(f,'all background',21,639,106,44);label(f,'全部',65,650);
  var maleBG=rect(f,'male background',136,639,106,44),maleIcon=rect(f,'icon/male',157,649,24,24);maleIcon.style.fills=['#0088ff'];
  var old=new s.Group({parent:f,name:'内容卡片 / 内容 · 男生',frame:{x:181,y:593,width:169,height:44}});settings.setLayerSettingForKey(old,'layerpilot.generated.v1',true);settings.setLayerSettingForKey(old,'layerpilot.region.v1',true);
  var femaleBG=rect(old,'female background',63,0,106,44),female=label(old,'女生',112,13),male=label(old,'男生',0,13);
  d.selectedLayers.layers=[f];var before=s.export(f,{output:false,formats:'png',scales:'1'}),result=e.organize(d);
  check('overlay isolated above underlying card',card.parent.id!==male.parent.id&&result.regions.some(function(r){return r.name==='弹窗区域';}));
  report.parents=[male,maleBG,maleIcon,female,femaleBG].map(function(l){return {name:l.name,parent:l.parent.name,parentId:l.parent.id};});report.regions=result.regions;
  check('male caption joins own surface and icon',under(maleBG,male.parent)&&under(maleIcon,male.parent));
  check('female remains with own surface',female.parent.id===femaleBG.parent.id&&female.parent.id!==male.parent.id);
  check('old wrong plugin group removed',!d.getLayerWithID(old.id));
  check('pixels unchanged',before.equals(s.export(f,{output:false,formats:'png',scales:'1'})));
  var again=e.organize(d);check('second run does not regroup',again.groups===0);report.success=true;
 }catch(error){report.success=false;report.error=String(error)+' '+error.stack;}finally{d.close();fs.writeFileSync(root+'/evidence/overlay-report.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));}
};
