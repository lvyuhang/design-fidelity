'use strict';
var sketch=require('sketch');
var settings=require('sketch/settings');
var core=require('./core');
var regions=require('./regions');
var layout=require('./layout');
var glyphs=require('./glyphs');
var pixels=require('./pixels');
var canvas=require('./canvas');
var fs=require('./files');
var GENERATED='layerpilot.generated.v1',feedback=null,lastFeedback=0,snapshotCache=null;
function pulse(){if(feedback&&Date.now()-lastFeedback>=32){lastFeedback=Date.now();feedback();}}
function withFeedback(options,report,work){var previous=feedback,previousCache=snapshotCache;snapshotCache=options._snapshotCache||null;feedback=options.onProgress?function(){emit(options,{heartbeat:true,safe:false},report);}:null;try{return work();}finally{feedback=previous;snapshotCache=previousCache;}}
function setting(layer,key){
  var value=settings.layerSettingForKey(layer,key);if(value!==undefined&&value!==null)return value;
  // Preserve linkage when a document moves between the installed plugin and
  // a locally generated preview. Only LayerPilot's own namespaced keys are read.
  var namespaces=['local.layerpilot.sketch','com.bohemiancoding.sketch.runscriptidentifier'];
  for(var i=0;i<namespaces.length;i++){try{var raw=__command.valueForKey_onLayer_forPluginIdentifier(key,layer.sketchObject,namespaces[i]);if(raw!==undefined&&raw!==null)return JSON.parse(raw);}catch(e){}}
}

function children(layer) {return layer.layers?Array.from(layer.layers):[];}
function active(a) {return Array.from(a||[]).some(function(x){return x.enabled!==false;});}
function snapshot(layer,onVisit) {
  pulse();
  if(typeof onVisit!=='function')onVisit=null;
  if(onVisit)onVisit(layer);
  var model=snapshotCache&&!onVisit?layer.sketchObject.immutableModelObject():null,cached=model&&snapshotCache[layer.id];
  if(cached&&cached.model.isEqual(model))return cached.node;
  var f=layer.frame||{},s=layer.style,t=layer.transform||{};
  var cs=children(layer).map(function(c){return snapshot(c,onVisit);});
  var risk=!!(t.rotation||t.flippedHorizontally||t.flippedVertically);
  if(s) risk=risk||s.opacity!==1||(s.blendingMode&&s.blendingMode!=='Normal')||active(s.shadows)||active(s.innerShadows)||active(s.borders)||active(s.blurs)||(s.blur&&s.blur.enabled);
  risk=!!risk||cs.some(function(c){return c.risk||c.mask||c.breakMask;});
  if(layer.type==='Group'&&!layer.isFrame) risk=risk||cs.some(function(c){return c.x<-.1||c.y<-.1||c.x+c.width>f.width+.1||c.y+c.height>f.height+.1;});
  var points=layer.type==='ShapePath'?Array.from(layer.points||[]):[];
  var round=layer.shapeType==='Oval'||(points.length>=4&&points.length<=5&&points.every(function(p){var v=p.point;return [[.5,0],[0,.5],[.5,1],[1,.5]].some(function(q){return Math.abs(v.x-q[0])<.001&&Math.abs(v.y-q[1])<.001;})&&p.pointType!=='Straight';}));
  var surface=layer.type==='ShapePath'&&(round||layer.shapeType==='Rectangle')&&s&&active(s.fills)&&!active(s.borders)&&!t.rotation;
  var imageFill=s&&Array.from(s.fills||[]).some(function(fill){return fill.enabled!==false&&fill.fillType==='Pattern';});
  var compositing=!!(s&&s.blendingMode&&s.blendingMode!=='Normal')||cs.some(function(c){return c.compositing;});
  if(s)['fills','borders','shadows','innerShadows'].forEach(function(key){if(Array.from(s[key]||[]).some(function(v){return v.enabled!==false&&v.blendingMode&&v.blendingMode!=='Normal';}))compositing=true;});
  var pad=0;
  if(s){
    Array.from(s.borders||[]).forEach(function(b){if(b.enabled!==false)pad=Math.max(pad,Number(b.thickness)||0);});
    Array.from(s.shadows||[]).forEach(function(b){if(b.enabled!==false)pad=Math.max(pad,Math.abs(Number(b.x)||0)+Math.abs(Number(b.y)||0)+4*(Number(b.blur)||0)+Math.abs(Number(b.spread)||0));});
    Array.from(s.blurs||[]).concat(s.blur?[s.blur]:[]).forEach(function(b){if(b.enabled!==false){pad=Math.max(pad,4*(Number(b.radius)||0));if(/background|glass/i.test(String(b.type||b.blurType)))compositing=true;}});
  }
  var local={x:0,y:0,width:f.width||0,height:f.height||0};
  if(!layer.clipsContents&&!cs.some(function(c){return c.mask;})){
    var bounds=[local].concat(cs.filter(function(c){return !c.hidden&&c.type!=='Slice';}).map(function(c){return c.paintBounds;}));
    local=core.union(bounds);
  }
  var angle=(Number(t.rotation)||0)*Math.PI/180,co=Math.cos(angle),si=Math.sin(angle),cx=(f.width||0)/2,cy=(f.height||0)/2;
  var points=[[local.x-pad,local.y-pad],[local.x+local.width+pad,local.y-pad],[local.x-pad,local.y+local.height+pad],[local.x+local.width+pad,local.y+local.height+pad]].map(function(p){var x=(p[0]-cx)*(t.flippedHorizontally?-1:1),y=(p[1]-cy)*(t.flippedVertically?-1:1);return {x:(f.x||0)+cx+x*co-y*si,y:(f.y||0)+cy+x*si+y*co};});
  var paintBounds={x:Math.min.apply(null,points.map(function(p){return p.x;})),y:Math.min.apply(null,points.map(function(p){return p.y;}))};
  paintBounds.width=Math.max.apply(null,points.map(function(p){return p.x;}))-paintBounds.x;paintBounds.height=Math.max.apply(null,points.map(function(p){return p.y;}))-paintBounds.y;
  var node={id:layer.id,name:layer.name,type:layer.type,x:f.x,y:f.y,width:f.width,height:f.height,
    text:layer.type==='Text'?layer.text:'',fontSize:layer.type==='Text'&&s?s.fontSize:0,shapeType:layer.shapeType,painted:!!(s&&(active(s.fills)||active(s.borders))),hidden:layer.hidden,locked:layer.locked,
    isFrame:!!layer.isFrame,isGraphic:!!layer.isGraphicFrame,stack:!!(layer.stackLayout||layer.smartLayout),
    clipsContents:!!layer.clipsContents,cornerRadius:s&&s.corners?Math.max.apply(null,[0].concat(Array.from(s.corners.radii||[]))):0,
    generated:!!setting(layer,GENERATED),mask:!!layer.masksSiblings,breakMask:!!layer.breaksMaskChain,
    sliceWrapper:!!setting(layer,'layerpilot.sliceWrapper.v1'),
    region:!!setting(layer,'layerpilot.region.v1'),supersedes:setting(layer,'layerpilot.glyphSources.v1')||[],compositing:compositing,paintBounds:paintBounds,
    exportable:!!(layer.exportFormats&&layer.exportFormats.length),flow:!!(layer.flow&&layer.flow.targetId),
    customPath:layer.type==='ShapePath'&&(layer.shapeType==='Custom'||layer.edited),
    buttonSurface:!!(surface&&!imageFill&&!compositing||setting(layer,'layerpilot.sliceWrapper.v1')&&cs.filter(function(c){return c.type!=='Slice';}).length===1&&cs.some(function(c){return c.buttonSurface;})),glyph:!!setting(layer,'layerpilot.glyph.v1'),imageFill:!!imageFill,risk:!!(risk||compositing),children:cs};
  if(model)snapshotCache[layer.id]={model:model,node:node};
  return node;
}
function selectedRoots(document) {
  var selection=Array.from(document.selectedLayers.layers).map(function(l){if(l.type==='Slice'){var id=setting(l,'layerpilot.sliceSource.v1');return id&&document.getLayerWithID(id)||l;}return l;}).filter(function(l){return l.parent&&document.getLayerWithID(l.id);}),ids={};
  selection.forEach(function(l){ids[l.id]=true;});
  return selection.filter(function(l){for(var a=l.parent;a&&a.type!=='Document';a=a.parent)if(ids[a.id])return false;return true;});
}
function ancestorBlocked(layer,structural) {
  for(var a=layer;a&&a.type!=='Document';a=a.parent) {
    if(a.hidden||a.locked||a.type==='SymbolMaster') return true;
    if(structural&&(a.stackLayout||a.smartLayout)) return true;
  }
  return false;
}
function scope(document) {
  var roots=selectedRoots(document);
  return {roots:roots.length?roots:[document.selectedPage],selected:roots.length>0,label:roots.length?'选中的 '+roots.length+' 个图层及其内容':'当前页面「'+document.selectedPage.name+'」'};
}
function withUndo(document,label,fn) {
  var manager=document.sketchObject.undoManager();
  // Modern Sketch uses command-level history and may expose no NSUndoManager.
  // Let Sketch record the synchronous plugin command in that case.
  if(!manager) {
    var native=document.sketchObject;
    var history=typeof native.historyMaker==='function'?native.historyMaker():null;
    if(history)history.registerHistoryMomentTitle(label);
    return fn();
  }
  manager.beginUndoGrouping();
  try {return fn();} finally {manager.setActionName(label);manager.endUndoGrouping();}
}
// The recursive pruning workflow is adapted from Automate-Sketch's
// Layer/Remove_Empty_Groups.js (MIT, Ashung Hung). The original native class
// checks and children iterator are replaced with public DOM APIs and guards.
function removable(layer,n) {
  var s=layer.style;
  return n.type==='Group'&&!n.isFrame&&!n.stack&&!n.risk&&!n.mask&&!n.breakMask&&!n.exportable&&!n.flow&&!n.children.length&&
    !layer.sharedStyleId&&!(s&&(active(s.fills)||active(s.borders)||active(s.shadows)||active(s.innerShadows)));
}

// Ambiguous shadows are checked locally at 1x and 2x. Export is memory-only:
// neither a network request nor a user asset export. Visible changes roll back.
function renderProof(layer){
  var root=layer;
  for(var p=layer;p&&p.type!=='Page'&&p.type!=='Document';p=p.parent){root=p;if(p.isFrame||p.type==='Artboard')break;}
  if(!root.frame||root.frame.width*root.frame.height>3000000)return null;
  try{return [1,2].map(function(scale){pulse();return sketch.export(root,{output:false,formats:'png',scales:String(scale),trimmed:false}).toNSData();});}catch(e){return null;}
}
function compareProof(a,b,allowSubtle){
  if(!a||!b||a.length!==b.length)return {ok:false};
  var subtle=false,changed=0;
  try {
    for(var k=0;k<a.length;k++){
      pulse();
      if(a[k].isEqualToData(b[k]))continue;
      if(!allowSubtle)return {ok:false};
      function decode(data){var rep=NSBitmapImageRep.imageRepWithData(data),tiff=rep.TIFFRepresentationUsingCompression_factor(1,1);var binary=String(NSString.alloc().initWithData_encoding(tiff,NSISOLatin1StringEncoding)),bytes=new Uint8Array(binary.length);for(var i=0;i<binary.length;i++){if((i&65535)===0)pulse();bytes[i]=binary.charCodeAt(i);}return pixels.decode(bytes);}
      var result=pixels.compare(decode(a[k]),decode(b[k]),pulse);if(!result.ok)return result;
      subtle=subtle||result.subtle;changed+=result.changed;
    }
    return {ok:true,subtle:subtle,changed:changed};
  }catch(e){return {ok:false,error:String(e)+" "+e.stack};}
}

function emit(options,state,report){if(options&&options.onProgress)try{options.onProgress(state);}catch(error){error.report=report;throw error;}}
function restoreSelection(document,selected){document.selectedLayers.layers=selected.filter(function(l){return !!document.getLayerWithID(l.id);});}
function organizeJob(document,options) {
  var opts=Object.assign({rename:true,cleanup:true,sort:true,group:true,visualize:true,regions:true,gap:16,allowSubtleShadows:true},options||{});
  if(!Number.isFinite(opts.gap)||opts.gap<0||opts.gap>64)throw new Error('分组间距必须在 0–64 px 之间');
  opts._snapshotCache={};
  var selected=Array.from(document.selectedLayers.layers),visited=0;
  var target=scope(document),report={renamed:0,removed:0,groups:0,sorted:0,protected:0,subtleShadows:0,regions:[],containers:[]};
  // Temporary native selection outlines: never move artwork or add document layers.
  // Bound the added presentation time independently of the number of groups.
  var visualBudget=2400;
  function showGrouping(layers,complete){
    if(!opts.visualize||!opts.onProgress||visualBudget<=0)return;
    var hold=Math.min(visualBudget,complete?180:120);visualBudget-=hold;
    document.selectedLayers.layers=layers;
    emit(opts,{stage:complete?'已归组':'正在圈选归组元素',name:complete?layers[0].name:layers.length+' 个元素 → 新分组',force:true,holdMs:hold,visual:complete?'grouped':'members',layerIds:layers.map(function(l){return l.id;})},report);
  }
  function renameContents(layer){
    if(!opts.rename||ancestorBlocked(layer,true)||layer.type==='SymbolInstance'||layer.type==='Slice')return;
    var n=snapshot(layer),name=core.rename(n);
    if(name&&name!==layer.name){layer.name=name;report.renamed++;}
    if(core.resourceKind(n)||n.stack)return;
    children(layer).forEach(renameContents);
  }
  function joinGlyphs(parent){
    if(!opts.group||!parent.layers||ancestorBlocked(parent,true))return;
    var n=snapshot(parent);
    if(n.stack||n.sliceWrapper||core.resourceKind(n))return;
    glyphs.clusters(n.children,core.resourceKind).clusters.forEach(function(parts){
      var now=snapshot(parent),ids=parts.map(function(p){return p.id;}),slot=regions.insertion(now.children,ids);if(slot===null)return;
      var layers=children(parent).filter(function(l){return ids.indexOf(l.id)>=0;});
      showGrouping(layers,false);
      var sources=[];function remember(l){sources.push(l.id);children(l).forEach(remember);}layers.forEach(remember);
      var g=new sketch.Group({parent:parent,name:'图标',frame:{x:0,y:0,width:1,height:1},layers:[]});g.index=slot;
      layers.forEach(function(l){var f=new sketch.Rectangle(l.frame);l.parent=g;l.frame=f;});g.adjustToFit();settings.setLayerSettingForKey(g,'layerpilot.glyph.v1',true);settings.setLayerSettingForKey(g,'layerpilot.glyphSources.v1',sources);report.groups++;showGrouping([g],true);
    });
  }
  function structureRegions(parent){
    if(!opts.group||!opts.regions||ancestorBlocked(parent,true))return;
    var before=children(parent).length,regionCount=report.regions.length;
    var current=snapshot(parent),live={};children(parent).forEach(function(l){live[l.id]=l;});
    regions.plans(current,opts).forEach(function(plan){
      emit(opts,{stage:'正在归拢区域',name:parent.name+' · '+plan.name},report);
      var slot=regions.insertion(current.children,plan.ids);
      if(slot===null&&plan.verifyPixels)slot=regions.insertion(current.children.map(function(n){return Object.assign({},n,{paintBounds:n});}),plan.ids);
      if(slot===null)return;
      var verify=plan.verifyPixels&&regions.insertion(current.children,plan.ids)===null;
      if(verify)emit(opts,{stage:'正在核对画面一致性',name:parent.name+' · 1x / 2x 渲染'},report);
      var baseline=verify?renderProof(parent):null;
      if(verify&&!baseline){report.protected++;return;}
      var layers=plan.ids.map(function(id){return live[id];});
      if(layers.some(function(l){return !l||!l.parent||l.parent.id!==parent.id;}))return;
      showGrouping(layers,false);
      layers.forEach(renameContents);
      layers.sort(function(a,b){return a.index-b.index;});
      var originalOrder=children(parent);
      var saved=layers.map(function(l){return {layer:l,frame:new sketch.Rectangle(l.frame)};});
      var g=new sketch.Group({parent:parent,name:plan.name,frame:{x:0,y:0,width:1,height:1},layers:[]});g.index=slot;
      settings.setLayerSettingForKey(g,GENERATED,true);settings.setLayerSettingForKey(g,'layerpilot.region.v1',true);
      saved.forEach(function(item){item.layer.parent=g;item.layer.frame=new sketch.Rectangle(item.frame);});
      g.adjustToFit();
      var proof=verify?compareProof(baseline,renderProof(parent),opts.allowSubtleShadows):{ok:true};
      if(verify&&!proof.ok){
        var tried={},plain=current.children.map(function(n){return Object.assign({},n,{paintBounds:n});}),choices=[];tried[slot]=true;
        current.children.forEach(function(n,i){if(plan.ids.indexOf(n.id)<0&&current.children.some(function(m){return plan.ids.indexOf(m.id)>=0&&core.intersects(m.paintBounds||m,n.paintBounds||n);})){
          [i+1,i].forEach(function(preferred){var at=regions.insertion(plain,plan.ids,preferred);if(at!==null&&!tried[at]){tried[at]=true;choices.push(at);}});
        }});
        for(var trial=0;trial<Math.min(12,choices.length)&&!proof.ok;trial++){
          emit(opts,{stage:'正在核对画面一致性',name:parent.name+' · 尝试 '+(trial+1)+' / '+Math.min(12,choices.length),safe:false},report);
          var at=choices[trial];g.index=current.children.slice(0,at).filter(function(n){return plan.ids.indexOf(n.id)<0;}).length;
          proof=compareProof(baseline,renderProof(parent),opts.allowSubtleShadows);
        }
      }
      if(!proof.ok){
        saved.forEach(function(item){item.layer.parent=parent;item.layer.frame=item.frame;});g.remove();originalOrder.forEach(function(l,i){l.index=i;});report.protected++;return;
      }
      if(proof.subtle)report.subtleShadows++;
      report.groups++;report.regions.push({name:plan.name,layers:layers.length,kind:plan.kind,reason:plan.reason});
      if(plan.overlay){
        function unwrapOwned(parent){
          children(parent).forEach(function(child){
            if(!setting(child,GENERATED)||!setting(child,'layerpilot.region.v1'))return;
            var t=child.transform,style=child.style;
            if(child.isFrame||child.stackLayout||child.masksSiblings||t.rotation||t.flippedHorizontally||t.flippedVertically||style.opacity!==1||active(style.fills)||active(style.borders)||active(style.shadows)||active(style.innerShadows))return;
            unwrapOwned(child);
            var x=child.frame.x,y=child.frame.y,at=child.index;
            children(child).forEach(function(l,i){var f=new sketch.Rectangle(l.frame);f.x+=x;f.y+=y;l.parent=parent;l.frame=f;l.index=at+i;});child.remove();
          });
        }
        unwrapOwned(g);
      }
      showGrouping([g],true);
      var inserted=snapshot(g),positions={};children(parent).forEach(function(l,i){positions[l.id]=i;});
      current.children=current.children.filter(function(n){return plan.ids.indexOf(n.id)<0;}).concat(inserted).sort(function(a,b){return positions[a.id]-positions[b.id];});
    });
    if(report.regions.length>regionCount)report.containers.push({id:parent.id,name:parent.name,before:before,after:children(parent).length});
  }
  function structure(parent,allowed) {
    if(!parent||!parent.layers||ancestorBlocked(parent,true)||parent.type==='SymbolInstance'||parent.type==='SymbolMaster')return;
    var n=snapshot(parent);
    if(n.stack)return;
    if(allowed)n=Object.assign({},n,{children:n.children.map(function(c){return Object.assign({},c,{locked:c.locked||!allowed[c.id]});})});
    if(opts.sort) {
      var order=core.sortedOrder(n.children),original=n.children.map(function(c){return c.id;});
      if(order.join()!==original.join()) {
        order.forEach(function(id,i){document.getLayerWithID(id).index=i;});report.sorted++;
      }
    }
    n=snapshot(parent);
    if(allowed)n=Object.assign({},n,{children:n.children.map(function(c){return Object.assign({},c,{locked:c.locked||!allowed[c.id]});})});
    var created=[];
    if(opts.group) core.planGroups(n,opts.gap).forEach(function(ids){
      var layers=ids.map(function(id){return document.getLayerWithID(id);});
      if(layers.some(function(l){return !l||!l.parent||l.parent.id!==parent.id;}))return;
      showGrouping(layers,false);
      var index=layers[0].index;
      var saved=layers.map(function(l){return {layer:l,frame:{x:l.frame.x,y:l.frame.y,width:l.frame.width,height:l.frame.height}};});
      var g=new sketch.Group({parent:parent,name:core.groupName(layers.map(snapshot)),frame:{x:0,y:0,width:1,height:1},layers:[]});
      settings.setLayerSettingForKey(g,GENERATED,true);
      g.index=index;
      saved.forEach(function(item){item.layer.parent=g;item.layer.frame=new sketch.Rectangle(item.frame);});
      g.adjustToFit();created.push(g.id);report.groups++;showGrouping([g],true);
    });
    // New group bounds change the sort keys; settle the order in this run.
    if(opts.sort&&created.length) {
      var after=snapshot(parent);
      if(allowed)after=Object.assign({},after,{children:after.children.map(function(c){return Object.assign({},c,{locked:c.locked||(!allowed[c.id]&&created.indexOf(c.id)<0)});})});
      var finalOrder=core.sortedOrder(after.children);
      if(finalOrder.join()!==after.children.map(function(c){return c.id;}).join()) {
        finalOrder.forEach(function(id,i){document.getLayerWithID(id).index=i;});
        if(!order||order.join()===original.join())report.sorted++;
      }
    }
  }
  function* visit(layer) {
    yield;
    if(!document.getLayerWithID(layer.id))return;
    emit(opts,{stage:'正在整理图层',name:layer.name+' · 已检查 '+(++visited)+' 层'},report);
    if(ancestorBlocked(layer,true)||layer.type==='SymbolInstance'||layer.type==='Slice') {report.protected++;return;}
    var n=snapshot(layer);
    if(n.generated){
      if(opts.rename&&n.region&&/^内容卡片 \/ \d+(?: \/ (?:内容|背景))?$/.test(n.name)){var heading=layout.title(n.children);if(heading){layer.name=n.name+' · '+heading;report.renamed++;}}
      if(!n.region)return;
    }
    if(opts.rename) {var name=core.rename(n);if(name&&name!==layer.name){layer.name=name;report.renamed++;}}
    // Export presets on a full screen must not prevent organizing its contents.
    if(!n.region&&core.resourceKind(n)&&!n.isFrame&&n.type!=='Artboard')return;
    if(n.stack){report.protected++;return;}
    yield;
    joinGlyphs(layer);
    yield;
    structureRegions(layer);
    for(var child of children(layer))yield* visit(child);
    yield;
    n=snapshot(layer);
    if(opts.cleanup&&removable(layer,n)) {layer.remove();report.removed++;return;}
    structure(layer);
    report.containers.forEach(function(c){if(c.id===layer.id)c.after=children(layer).length;});
  }
  function* work(){
   try{
    for(var root of target.roots)yield* visit(root);
    if(target.selected){
     var parents={},allowed={};
     target.roots.forEach(function(l){var live=document.getLayerWithID(l.id);if(live&&live.parent){parents[live.parent.id]=live.parent;allowed[live.id]=true;}});
     for(var id of Object.keys(parents)){yield;structure(parents[id],allowed);}
    }
    emit(opts,{stage:'整理完成',name:'正在汇总结果'},report);
    return report;
   }finally{restoreSelection(document,selected);}
  }
  var iterator=work();
  return {report:report,next:function(){return withFeedback(opts,report,function(){return iterator.next();});},stop:function(){return iterator.return();}};
}
function organize(document,options){
 return withUndo(document,'LayerPilot 自动整理图层',function(){var job=organizeJob(document,options);try{var next;do{next=job.next();}while(!next.done);return next.value;}finally{job.stop();}});
}
exports.organizeJob=organizeJob;

function collect(document,options) {
  var target=scope(document),nodes=[],protectedCount=0,visited=0;
  target.roots.forEach(function(layer){
    if(ancestorBlocked(layer,false)){protectedCount++;return;}
    var n=snapshot(layer,function(l){emit(options,{stage:'正在识别图标和图片',name:l.name+' · 已检查 '+(++visited)+' 层'});});
    for(var a=layer;a&&a.parent&&a.parent.type!=='Document';a=a.parent) {
      var siblings=children(a.parent),flags=core.maskedSiblings(siblings.map(function(c){return {mask:!!c.masksSiblings,breakMask:!!c.breaksMaskChain};}));
      var position=siblings.findIndex(function(c){return c.id===a.id;});
      if(position>=0&&flags[position]){n.ancestorMask=true;break;}
      if(a.parent.clipsContents) {
        var rect=new sketch.Rectangle(layer.frame).changeBasis({from:layer.parent,to:a.parent});
        if(core.cropRisk(snapshot(a.parent),rect)){n.ancestorMask=true;break;}
      }
    }
    nodes.push(n);
  });
  emit(options,{stage:'正在分析资源边界',name:'已读取 '+visited+' 层'});
  var result=core.discover(nodes);result.skipped+=protectedCount;result.scope=target.label;return result;
}
function formatsFor(asset,options) {
  var format=options.svg&&asset.kind==='icon'?'svg':'png';
  return format==='svg'?[{fileFormat:'svg',size:'1x',suffix:''}]:options.scales.map(function(scale){return {fileFormat:'png',size:scale+'x',suffix:scale===1?'':'@'+scale+'x'};});
}
function mergeFormats(layer,formats) {
  var existing=Array.from(layer.exportFormats||[]).map(function(f){return {fileFormat:f.fileFormat,size:f.size,prefix:f.prefix||'',suffix:f.suffix||''};});
  var added=0;
  formats.forEach(function(f){if(!existing.some(function(e){return e.fileFormat===f.fileFormat&&e.size===f.size&&e.suffix===f.suffix&&!e.prefix;})){existing.push(f);added++;}});
  if(added)layer.exportFormats=existing;
  return added;
}
function exportAssets(document,candidates,options) {
  var opts=Object.assign({scales:[1,2,3],svg:false,mark:true,directory:null},options||{});
  if(!opts.scales.length||opts.scales.some(function(s){return [1,2,3].indexOf(s)<0;}))throw new Error('请选择 1x、2x 或 3x');
  var report={assets:0,files:[],errors:[],marked:0,directory:null};
  if(opts.directory) {
    var stamp=new Date().toISOString().replace(/[:.]/g,'-');
    var dir=opts.directory.replace(/\/$/,'')+'/LayerPilot-'+stamp;
    var i=1,base=dir;while(fs.existsSync(dir)){dir=base+'-'+i;i++;}
    fs.mkdirSync(dir);report.directory=dir;
  }
  return withUndo(document,'LayerPilot 自动切图',function(){
    candidates.forEach(function(asset){
      var layer=document.getLayerWithID(asset.node.id);
      if(!layer||ancestorBlocked(layer,false)){report.errors.push({id:asset.node.id,name:asset.node.name,error:'图层已移除、隐藏或锁定'});return;}
      var fmts=formatsFor(asset,opts),before=report.files.length;
      try {
        if(report.directory) fmts.forEach(function(fmt){
          var filename=core.filename(layer.name,layer.id)+fmt.suffix+'.'+fmt.fileFormat;
          // One layer, one scale per request: deterministic filenames and no overwrite.
          sketch.export(layer,{output:report.directory,formats:fmt.fileFormat,scales:String(parseFloat(fmt.size)),filename:filename,
            trimmed:false,overwriting:false,'group-contents-only':true});
          var file=report.directory+'/'+filename;
          if(!fs.existsSync(file)||fs.statSync(file).size===0)throw new Error('Sketch 未生成文件：'+filename);
          report.files.push({layerId:layer.id,name:layer.name,file:filename,scale:parseFloat(fmt.size),format:fmt.fileFormat});
        });
        if(opts.mark)report.marked+=mergeFormats(layer,fmts);
        report.assets++;
      } catch(error){report.errors.push({name:layer.name,error:String(error.message||error),exported:report.files.length-before});}
    });
    if(report.directory)fs.writeFileSync(report.directory+'/assets.json',JSON.stringify({plugin:'LayerPilot',version:'0.5.4',files:report.files,errors:report.errors},null,2));
    return report;
  });
}
exports.snapshot=snapshot;exports.scope=scope;exports.organize=organize;
exports.collect=collect;exports.exportAssets=exportAssets;exports.formatsFor=formatsFor;

// Adapted from Automate-Sketch Slice/Auto_Slice.js: enclose a leaf resource
// with its Slice and restrict the Slice to that group (layerOptions = 2).
// Unlike the upstream command, match by source ID and refresh existing Slices.
function createSlices(document,candidates,options) {
  var opts=Object.assign({scales:[1,2,3],svg:true,iconSize:'auto'},options||{});
  if(['auto',0,16,24,32,48,64].indexOf(opts.iconSize)<0)throw new Error('图标画布请选择 16、24、32、48 或 64 px');
  if((candidates.some(function(a){return !(opts.svg&&a.kind==='icon');})&&!opts.scales.length)||opts.scales.some(function(s){return [1,2,3].indexOf(s)<0;}))throw new Error('请选择 PNG 切片倍率');
  emit(opts,{stage:'正在检查文字间距',name:'读取可见文字与已有切片'});
  var selected=Array.from(document.selectedLayers.layers),scopeIds={};
  var textRects=Array.from(sketch.find('Text',document.selectedPage)).filter(function(t){for(var a=t;a&&a.type!=='Document';a=a.parent)if(a.hidden||a.type==='SymbolMaster')return false;return true;}).map(function(t,i){if(i%16===0)emit(opts,{stage:'正在检查文字间距',name:'已读取 '+i+' 个文字图层'});return new sketch.Rectangle(snapshot(t).paintBounds).changeBasis({from:t.parent,to:document.selectedPage});});

  var scanned=0;function includeScope(l){if((++scanned)%32===0)emit(opts,{stage:'正在读取选区',name:'已检查 '+scanned+' 层'});if(ancestorBlocked(l,false))return;scopeIds[l.id]=true;children(l).forEach(includeScope);}scope(document).roots.forEach(includeScope);
  var key='layerpilot.sliceSource.v1',index={};
  function scan(layer){if((++scanned)%32===0)emit(opts,{stage:'正在检查已有切片',name:'已检查 '+scanned+' 层'});if(layer.type==='Slice'){var id=setting(layer,key);if(id)index[id]=layer;}children(layer).forEach(scan);}
  scan(document.selectedPage);
  var report={created:0,updated:0,unchanged:0,retired:0,presetsRetired:0,errors:[],sliceIds:[]};
  try{return withFeedback(opts,report,function(){return withUndo(document,'LayerPilot 自动创建切片',function(){
    candidates.forEach(function(asset,i){
      emit(opts,{stage:'正在创建 / 更新切片',name:(i+1)+' / '+candidates.length+' · '+asset.node.name,done:i,total:candidates.length},report);
      var layer=document.getLayerWithID(asset.node.id),createdWrapper=null,slice=null,createdSlice=false,compound=null,compoundSaved=null;
      if(!layer||ancestorBlocked(layer,false)){report.errors.push({id:asset.node.id,name:asset.node.name,error:'资源已移除、隐藏或锁定'});return;}
      try {
        if(asset.members&&asset.members.length>1){
          var parts=asset.members.map(function(id){return document.getLayerWithID(id);}),parent=parts[0].parent;
          if(parts.some(function(p){return !p||!p.parent||p.parent.id!==parent.id;}))throw new Error('图标碎片不在同一容器内');
          var slot=regions.insertion(snapshot(parent).children,asset.members);if(slot===null)throw new Error('图标碎片与其他图层存在遮挡冲突');
          compoundSaved=parts.map(function(p){return {layer:p,parent:parent,frame:new sketch.Rectangle(p.frame),index:p.index};});
          compound=new sketch.Group({parent:parent,name:'图标',frame:{x:0,y:0,width:1,height:1},layers:[]});compound.index=slot;
          compoundSaved.sort(function(a,b){return a.index-b.index;}).forEach(function(p){p.layer.parent=compound;p.layer.frame=new sketch.Rectangle(p.frame);});compound.adjustToFit();
          settings.setLayerSettingForKey(compound,'layerpilot.glyph.v1',true);layer=compound;
        }
        var container,frame;
        if(layer.layers&&layer.type!=='SymbolInstance') {
          if(layer.stackLayout||layer.smartLayout)throw new Error('自动布局容器请先手动设置切片');
          container=layer;frame={x:0,y:0,width:layer.frame.width,height:layer.frame.height};
        } else {
          if(layer.parent&&setting(layer.parent,'layerpilot.sliceWrapper.v1'))container=layer.parent;
          else {
            if(ancestorBlocked(layer,true))throw new Error('Stack 内的单层资源请先手动设置切片，以保留自动布局');
            if(layer.style&&layer.style.blendingMode&&layer.style.blendingMode!=='Normal')throw new Error('使用混合模式的单层资源请先编组后再切片');
            var oldParent=layer.parent,oldIndex=layer.index,oldFrame=new sketch.Rectangle(layer.frame);
            createdWrapper=new sketch.Group({parent:oldParent,name:layer.name,frame:{x:0,y:0,width:1,height:1},layers:[]});
            createdWrapper.index=oldIndex;
            settings.setLayerSettingForKey(createdWrapper,'layerpilot.sliceWrapper.v1',true);
            settings.setLayerSettingForKey(createdWrapper,GENERATED,true);
            layer.parent=createdWrapper;layer.frame=new sketch.Rectangle(oldFrame);createdWrapper.adjustToFit();container=createdWrapper;
          }
          // Use Sketch's own Slice bounds to include rotation, borders and shadows.
          // The native factory requires an attached layer and inserts a measuring
          // Slice; remove it immediately, then create/update the linked Slice below.
          var measured=sketch.fromNative(MSSliceLayer.sliceLayerFromLayer(layer.sketchObject));
          try{var bounds=measured.frame;frame={x:bounds.x,y:bounds.y,width:bounds.width,height:bounds.height};}
          finally{measured.remove();}
        }
        if(asset.kind==='icon'&&opts.iconSize){
          // Use the visible artwork bounds rather than the old button/group bounds.
          var measuring=layer,copy=null,ink=null;
          try {
            if(layer.layers){
              // Existing Slice canvases must never enlarge the next measurement.
              copy=sketch.fromNative(layer.sketchObject.copy());copy.parent=layer.parent;copy.frame=new sketch.Rectangle(layer.frame);
              function strip(l){children(l).forEach(function(c){if(c.type==='Slice')c.remove();else strip(c);});}
              strip(copy);copy.adjustToFit();measuring=copy;
            }
            ink=sketch.fromNative(MSSliceLayer.sliceLayerFromLayer(measuring.sketchObject));
            var ir=ink.frame,localRect=layer.id===container.id?new sketch.Rectangle(ir).changeBasis({from:layer.parent,to:container}):ir;
            frame={x:localRect.x,y:localRect.y,width:localRect.width,height:localRect.height};
          } finally {if(ink)ink.remove();if(copy)copy.remove();}
          var obstacles=textRects.map(function(r){return new sketch.Rectangle(r).changeBasis({from:document.selectedPage,to:container});});
          var artwork=glyphs.artwork(snapshot(layer)),chosen=canvas.choose(frame,Math.max(artwork.width,artwork.height),opts.iconSize,obstacles);
          if(chosen.error)throw new Error(chosen.error);
          frame=chosen.frame;
        }
        slice=index[layer.id];
        if(slice&&(slice.hidden||slice.locked))throw new Error('已有关联切片被隐藏或锁定，请先检查该切片');
        var name=core.filename(layer.name,layer.id);
        var formats=formatsFor(asset,opts),desired=JSON.stringify(formats.map(function(f){return {fileFormat:f.fileFormat,size:f.size,suffix:f.suffix||'',prefix:''};}));
        var current=slice?JSON.stringify(Array.from(slice.exportFormats||[]).map(function(f){return {fileFormat:f.fileFormat,size:f.size,suffix:f.suffix||'',prefix:f.prefix||''};})):'';
        var changed=!slice||slice.parent.id!==container.id||slice.name!==name||current!==desired||slice.breaksMaskChain||Number(slice.sketchObject.exportOptions().layerOptions())!==2||['x','y','width','height'].some(function(k){return Math.abs(slice.frame[k]-frame[k])>.001;});
        if(!slice){slice=new sketch.Slice({parent:container,name:name,frame:frame});createdSlice=true;index[layer.id]=slice;}
        if(changed) {
          slice.parent=container;slice.frame=new sketch.Rectangle(frame);slice.name=name;slice.exportFormats=formats;
          // Preserve transparency: ignore unrelated layers behind this resource group.
          slice.sketchObject.exportOptions().setLayerOptions(2);
          slice.sketchObject.exportOptions().setShouldTrim(false);
          slice.index=0;slice.breaksMaskChain=false;
          settings.setLayerSettingForKey(slice,key,layer.id);
          if(createdSlice)report.created++;else report.updated++;
        }else report.unchanged++;
        // Migrate only our own earlier button/background Slices, never manual ones.
        var redundant=[];function nestedSources(l){children(l).forEach(function(c){if(index[c.id])redundant.push(c.id);nestedSources(c);});}nestedSources(layer);
        (asset.supersedes||[]).concat(asset.members||[],redundant).forEach(function(id){
          var old=index[id];if(old&&old.id!==slice.id&&!old.hidden&&!old.locked){old.remove();delete index[id];report.retired++;}
          var source=document.getLayerWithID(id);if(source&&source.id!==layer.id&&source.type!=='Slice'&&!source.hidden&&!source.locked&&source.exportFormats.length){
            if(!setting(source,'layerpilot.previousExportFormats.v1'))settings.setLayerSettingForKey(source,'layerpilot.previousExportFormats.v1',Array.from(source.exportFormats).map(function(f){return {fileFormat:f.fileFormat,size:f.size,prefix:f.prefix||'',suffix:f.suffix||''};}));
            source.exportFormats=[];report.presetsRetired++;
          }
        });
        report.sliceIds.push(slice.id);
      }catch(error){
        if(createdSlice&&slice)slice.remove();
        if(createdWrapper){layer.parent=oldParent;layer.frame=new sketch.Rectangle(oldFrame);layer.index=oldIndex;createdWrapper.remove();}
        if(compound){compoundSaved.forEach(function(p){p.layer.parent=p.parent;p.layer.frame=p.frame;});compound.remove();compoundSaved.forEach(function(p){p.layer.index=p.index;});}
        report.errors.push({id:asset.node.id,name:asset.node.name,error:String(error.message||error)});
      }
    });
    if(candidates.length)Object.keys(index).forEach(function(id){
      var old=index[id],source=document.getLayerWithID(id);
      if(!scopeIds[id]||!source||!old.parent||old.hidden||old.locked||ancestorBlocked(source,false))return;
      var n=snapshot(source);
      // Retire only a plugin-created Slice whose source is now a layout layer.
      // Deselected valid assets and all hand-made Slices are retained.
      if(!n.sliceWrapper&&!n.stack&&!n.isFrame&&n.type!=='SymbolInstance'&&!core.resourceKind(n)){
        old.remove();delete index[id];report.retired++;
      }
    });
    emit(opts,{stage:'切片处理完成',name:'正在汇总结果',done:candidates.length,total:candidates.length},report);
    return report;
  });});}finally{restoreSelection(document,selected);}
}
exports.createSlices=createSlices;

exports.compareProof=compareProof;
