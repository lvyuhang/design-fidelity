exports.run=function(root){
  var s=require('sketch'),e=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/engine.js');
  var files=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/files.js');
  var dialogs=require(root+'/LayerPilot.sketchplugin/Contents/Sketch/lib/dialogs.js');
  var out=root+'/evidence',report={checks:[]},d=new s.Document();
  function check(name,pass){report.checks.push({name:name,pass:!!pass});if(!pass)throw new Error(name);}
  function rect(parent,name,x,y,w,h){return new s.ShapePath({parent:parent,name:name,frame:{x:x,y:y,width:w,height:h},style:{fills:['#ff6600'],borders:[]}});}
  function image(parent,x,y){return new s.Image({parent:parent,name:'Image',image:out+'/fixture.png',frame:{x:x,y:y,width:80,height:80}});}
  function select(layers){d.selectedLayers.layers=layers;}
  function capture(panel,name){
    panel.alert.layout();
    var view=panel.alert.window().contentView();
    view.displayIfNeeded();
    var rep=view.bitmapImageRepForCachingDisplayInRect(view.bounds());
    view.cacheDisplayInRect_toBitmapImageRep(view.bounds(),rep);
    rep.representationUsingType_properties(4,{}).writeToFile_atomically(out+'/'+name+'.png',true);
  }
  try {
    var clip=new s.Group.Frame({parent:d.selectedPage,name:'Group 1',frame:{x:0,y:0,width:40,height:40}});
    var clipped=image(clip,-20,-20);
    var found=e.collect(d);
    check('clipped image wrapper identified',found.assets.length===1&&found.assets[0].node.id===clip.id&&found.assets[0].kind==='image');
    report.crop=e.exportAssets(d,found.assets,{directory:out,scales:[1],mark:false});
    check('clipped wrapper exported',report.crop.files.length===1&&!report.crop.errors.length);
    select([clipped]);check('selected clipped child skipped',e.collect(d).assets.length===0);
    select([]);
    var mixed=new s.Group.Frame({parent:d.selectedPage,name:'card',frame:{x:100,y:0,width:60,height:60}});
    image(mixed,-20,-20);
    new s.Text({parent:mixed,name:'Text',text:'标题',frame:{x:1,y:1,width:40,height:15}});
    select([mixed]);check('clipped image in layout not exported unmasked',e.collect(d).assets.length===0);
    var maskGroup=new s.Group({parent:d.selectedPage,name:'Group 2',frame:{x:200,y:0,width:40,height:40},layers:[]});
    var mask=rect(maskGroup,'mask',0,0,40,40);mask.masksSiblings=true;var masked=image(maskGroup,0,0);
    select([maskGroup]);found=e.collect(d);
    check('mask group exported as whole',found.assets.length===1&&found.assets[0].node.id===maskGroup.id);
    report.mask=e.exportAssets(d,found.assets,{directory:out,scales:[1],mark:false});
    var oldMaskOrder=maskGroup.layers.map(function(l){return l.id;}).join();
    e.organize(d);check('mask chain unchanged',maskGroup.layers.map(function(l){return l.id;}).join()===oldMaskOrder&&masked.parent.id===maskGroup.id);
    var stack=new s.Group.Frame({parent:d.selectedPage,name:'Stack',frame:{x:0,y:120,width:180,height:80},stackLayout:{direction:s.StackLayout.Direction.Row,gap:16}});
    var si=rect(stack,'icon/stack',0,0,24,24);rect(stack,'Rectangle',40,0,24,24);stack.stackLayout.apply();
    select([stack]);var before=JSON.stringify(stack.layers.map(function(l){return {id:l.id,name:l.name,frame:l.frame.toJSON()};}));
    e.organize(d);check('stack structure and geometry unchanged',before===JSON.stringify(stack.layers.map(function(l){return {id:l.id,name:l.name,frame:l.frame.toJSON()};})));
    check('icon within stack recognized',e.collect(d).assets.some(function(a){return a.node.id===si.id;}));
    var holder=new s.Group.Frame({parent:d.selectedPage,name:'selection test',frame:{x:0,y:240,width:300,height:200}});
    var a=rect(holder,'icon/a',0,0,20,20),b=rect(holder,'icon/b',24,0,20,20),untouched=rect(holder,'Rectangle 9',200,120,20,20);
    select([a,b]);e.organize(d);
    check('selection groups only selected siblings',a.parent.id===b.parent.id&&a.parent.id!==holder.id&&untouched.parent.id===holder.id&&untouched.name==='Rectangle 9');
    holder.hidden=true;select([a]);check('selected descendant of hidden ancestor skipped',e.collect(d).assets.length===0);holder.hidden=false;
    a.exportFormats=[{fileFormat:'jpg',size:'2x',suffix:'-original'}];
    var asset={node:e.snapshot(a),kind:'icon'};
    e.exportAssets(d,[asset],{scales:[1],mark:true});
    check('existing custom export preset preserved',a.exportFormats.length===2&&a.exportFormats[0].fileFormat==='jpg'&&a.exportFormats[0].suffix==='-original');
    var deleted=rect(holder,'icon/deleted',0,60,20,20),stale={node:e.snapshot(deleted),kind:'icon'};deleted.remove();
    var missing=e.exportAssets(d,[stale],{scales:[1],mark:true});check('stale candidate reports error',missing.errors.length===1&&missing.assets===0);
    var organizePanel=dialogs.buildOrganize('当前页面「产品设计」');
    check('organize dialog default controls',organizePanel.read().gap===16&&organizePanel.read().group);
    capture(organizePanel,'ui-organize');
    var assetsPanel=dialogs.buildAssets({scope:'选中的 1 个图层及其内容',assets:[{node:{id:'1',name:'icon/search'},kind:'icon'},{node:{id:'2',name:'头像 / 用户'},kind:'image'}]});
    check('slice dialog has no file export option',assetsPanel.read().candidates.length===2&&assetsPanel.read().scales.length===3&&!('exportFiles' in assetsPanel.read()));
    capture(assetsPanel,'ui-assets');
    report.success=true;
  }catch(error){report.success=false;report.error=String(error)+'\n'+String(error.stack||'');}finally{
    files.writeFileSync(out+'/native-edge-report.json',JSON.stringify(report,null,2));d.close();console.log(JSON.stringify(report));
  }
};
