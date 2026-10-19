// Diverse independent fixtures; no access to the user's design document.
exports.run=function(root){
  var s=require('sketch'),e=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/engine.js'),fs=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/files.js');
  var d=new s.Document(),out=root+'/evidence',report={checks:[],cases:[]};
  function check(name,pass){report.checks.push({name:name,pass:!!pass});if(!pass)throw new Error(name);}
  function rect(p,name,x,y,w,h){return new s.ShapePath({parent:p,name:name,frame:{x:x,y:y,width:w,height:h},style:{fills:['#ffffff'],borders:[]}});}
  function text(p,name,x,y,size){return new s.Text({parent:p,name:name,text:name,frame:{x:x,y:y,width:80,height:20},style:{fontSize:size||16,textColor:'#202020'}});}
  function photo(p,name,x,y,w,h){return new s.Image({parent:p,name:name,frame:{x:x,y:y,width:w,height:h},image:out+'/fixture.png'});}
  function frame(name,w,h){return new s.Group.Frame({parent:d.selectedPage,name:name,frame:{x:0,y:0,width:w,height:h},style:{fills:['#f3f4f7']}});}
  function render(f,file){s.export(f,{output:out,filename:file+'.png',formats:'png',scales:'1',trimmed:false,overwriting:true});}
  function runCase(name,f,expected,verify){
    d.selectedLayers.layers=[f];
    var before=f.layers.length,start=Date.now();render(f,'layout-'+name+'-before');
    var r=e.organize(d);render(f,'layout-'+name+'-after');
    report.cases.push({name:name,before:before,after:f.layers.length,groups:r.groups,regions:r.regions,milliseconds:Date.now()-start});
    check(name+': expected region groups',r.regions.length===expected);
    if(verify)verify(r);
    var again=e.organize(d);check(name+': idempotent',!again.groups&&!again.renamed&&!again.removed&&!again.sorted);
  }
  try{
    var f=frame('single',375,812),bg=rect(f,'Rectangle 1',12,120,351,240),label=text(f,'账户信息',30,160,20),pic=photo(f,'photo',30,210,100,100);
    runCase('single',f,1,function(){check('single: all card content shares parent',bg.parent.id===label.parent.id&&pic.parent.id===label.parent.id);});
    f=frame('desktop',1040,800);var cards=[];
    for(var i=0;i<4;i++)cards.push({bg:rect(f,'Rectangle '+i,20+i*250,100,230,260)});
    for(i=0;i<4;i++){cards[i].label=text(f,'套餐 '+i,36+i*250,300,18);cards[i].image=photo(f,'photo '+i,36+i*250,116,198,160);}
    runCase('desktop',f,4,function(){check('desktop: each card owns its caption and image',cards.every(function(c){return c.bg.parent.id===c.label.parent.id&&c.image.parent.id===c.bg.parent.id;}));});
    f=frame('contacts',375,812);var contacts=[];
    for(i=0;i<4;i++)contacts.push({avatar:photo(f,'photo/avatar '+i,16,80+i*80,40,40)});
    for(i=0;i<4;i++){contacts[i].name=text(f,'联系人 '+i,68,80+i*80);contacts[i].subtitle=text(f,'最近上线',68,104+i*80,12);}
    d.selectedLayers.layers=[f];var created=e.createSlices(d,e.collect(d).assets,{scales:[1,2]});
    check('contacts: slices exist before organizing',created.created===4&&created.errors.length===0);
    runCase('contacts',f,4,function(){
      check('contacts: own avatar and labels share row',contacts.every(function(c){return c.avatar.parent.parent.id===c.name.parent.id&&c.subtitle.parent.id===c.name.parent.id;}));
      var again=e.createSlices(d,e.collect(d).assets,{scales:[1,2]});check('contacts: slice links unchanged after grouping',again.unchanged===4&&again.created===0&&again.updated===0);
    });
    f=frame('settings',375,812);var fields=[];
    for(i=0;i<4;i++)fields.push({label:text(f,'设置 '+i,16,80+i*60),value:text(f,'已开启',260,80+i*60)});
    runCase('settings',f,4,function(){check('settings: values paired with correct labels',fields.every(function(c){return c.label.parent.id===c.value.parent.id;}));});
    f=frame('toolbar',375,812);text(f,'工具操作',10,10,20);var buttons=[];
    for(i=0;i<4;i++){var icon=rect(f,'icon/tool '+i,20+i*80,90,24,24);icon.style.fills=['#6258f5'];buttons.push({icon:icon,label:text(f,'按钮',18+i*80,122,14)});}
    runCase('toolbar',f,4,function(){check('toolbar: one pair per button',buttons.every(function(c){return c.icon.parent.id===c.label.parent.id&&c.icon.parent.layers.length===2;}));});
    report.success=true;
  }catch(error){report.success=false;report.error=String(error)+'\n'+String(error.stack||'');}
  finally{fs.writeFileSync(out+'/layout-native-report.json',JSON.stringify(report,null,2));d.close();console.log(JSON.stringify(report));}
};
