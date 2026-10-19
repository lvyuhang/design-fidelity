// Run with sketchtool run-script "require('/absolute/path/tests/native.js').run()".
exports.run=function(root){
  var s=require('sketch'),e=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/engine.js'),files=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/files.js');
  var out=root+'/evidence';
  files.mkdirSync(out);
  var report={checks:[],version:'2026.1.1'};
  function check(name,condition){report.checks.push({name:name,pass:!!condition});if(!condition)throw new Error(name);}
  function rect(parent,name,x,y,w,h,color){return new s.ShapePath({parent:parent,name:name,frame:{x:x,y:y,width:w,height:h},style:{fills:[{color:color||'#ff6600'}],borders:[]}});}
  var d=new s.Document();
  try {
    d.selectedPage.name='LayerPilot 验证';
    var f=new s.Group.Frame({parent:d.selectedPage,name:'整理与切图测试',frame:{x:0,y:0,width:700,height:560},style:{fills:[{color:'#f4f5f8'}]}});
    // Imported/legacy artboards commonly set this flag. It must not block the page.
    f.breaksMaskChain=true;
    f.exportFormats=[{fileFormat:'png',size:'1x'}];
    rect(f,'Rectangle 1',24,24,280,150,'#ffffff');
    var t1=new s.Text({parent:f,name:'Text 1',text:'账户概览',frame:{x:44,y:44,width:180,height:28},style:{fontSize:20,textColor:'#172030'}});
    var icon=rect(f,'icon/account',44,98,24,24,'#5e5ce6');
    rect(f,'Rectangle 2',336,24,280,150,'#ffffff');
    new s.Text({parent:f,name:'Text 2',text:'订单管理',frame:{x:356,y:44,width:180,height:28},style:{fontSize:20,textColor:'#172030'}});
    rect(f,'icon/order',356,98,24,24,'#00a883');
    var empty=new s.Group({parent:f,name:'空组',layers:[]});
    var visibleEmpty=new s.Group.Frame({parent:f,name:'有背景的空容器',frame:{x:24,y:220,width:100,height:40},style:{fills:[{color:'#ccccff'}]}});
    // Overlapping shapes form a painter-order constraint.
    var back=rect(f,'overlap/back',450,240,70,70,'#ff3b30');
    var front=rect(f,'overlap/front',490,270,70,70,'#007aff');
    var locked=rect(f,'locked',600,240,24,24,'#222222');locked.locked=true;
    var initial={x:t1.frame.x,y:t1.frame.y};
    s.export(f,{output:out,filename:'before.png',formats:'png',scales:'1',trimmed:false,overwriting:true});
    var r=e.organize(d,{gap:16});report.organize=r;
    check('card groups created',r.groups>=2);
    check('empty plain group removed',!d.getLayerWithID(empty.id));
    check('styled empty frame preserved',!!d.getLayerWithID(visibleEmpty.id));
    check('business name preserved',icon.name==='icon/account');
    check('text default renamed',t1.name==='文本 / 账户概览');
    check('overlap order preserved',back.parent.id===front.parent.id&&back.index<front.index);
    var pos=new s.Rectangle(t1.frame).changeBasis({from:t1.parent,to:f});
    check('coordinates unchanged',Math.abs(pos.x-initial.x)<.01&&Math.abs(pos.y-initial.y)<.01);
    s.export(f,{output:out,filename:'after.png',formats:'png',scales:'1',trimmed:false,overwriting:true});
    var r2=e.organize(d,{gap:16});report.secondRun=r2;
    check('organizer idempotent',r2.groups===0&&r2.renamed===0&&r2.removed===0&&r2.sorted===0);
    var found=e.collect(d);report.candidates=found.assets.map(function(a){return {id:a.node.id,name:a.node.name,kind:a.kind};});
    check('only two named icons identified',found.assets.length===2);
    var exported=e.exportAssets(d,found.assets,{directory:out,scales:[1,2,3],mark:true});report.exports=exported;
    check('six PNG files exported',exported.files.length===6&&exported.errors.length===0);
    var repeat=e.exportAssets(d,found.assets,{scales:[1,2,3],mark:true});
    check('export presets do not duplicate',repeat.marked===0&&icon.exportFormats.length===3);
    var svg=e.exportAssets(d,e.collect(d).assets,{directory:out,scales:[1],svg:true,mark:false});report.svg=svg;
    check('marked icons remain eligible for SVG',svg.files.length===2&&svg.errors.length===0&&svg.files.every(function(f){return f.format==='svg';}));
    d.save(out+'/LayerPilot-Demo.sketch');
    report.success=true;
  }catch(error){report.success=false;report.error=String(error)+'\n'+String(error.stack||'');}finally{
    files.writeFileSync(out+'/native-report.json',JSON.stringify(report,null,2));
    d.close();console.log(JSON.stringify(report));
  }
};
