'use strict';
var settings=require('sketch/settings');
function preferences(key){return settings.settingForKey('layerpilot.ui.'+key)||{};}
function save(key,value){settings.setSettingForKey('layerpilot.ui.'+key,value);}
function button(title,x,y,fn){var b=NSButton.alloc().initWithFrame(NSMakeRect(x,y,76,28));b.setTitle(title);b.setBezelStyle(1);b.setCOSJSTargetFunction(fn);return b;}
function label(text,rect,size) {
  var field=NSTextField.alloc().initWithFrame(NSMakeRect(rect[0],rect[1],rect[2],rect[3]));
  field.setStringValue(text);field.setEditable(false);field.setSelectable(false);
  field.setBezeled(false);field.setDrawsBackground(false);field.setFont(NSFont.systemFontOfSize(size||12));
  return field;
}
function checkbox(text,on,y) {
  var b=NSButton.alloc().initWithFrame(NSMakeRect(0,y,440,24));
  b.setButtonType(3);b.setTitle(text);b.setState(on?1:0);return b;
}
function alert(title,description,button) {
  var a=NSAlert.alloc().init();a.setMessageText(title);a.setInformativeText(description);
  a.addButtonWithTitle(button);a.addButtonWithTitle('取消');return a;
}
function buildOrganize(scope) {
  var pref=preferences('organize');
  var a=alert('自动整理图层 · 0.5.7',scope+'\n按空间关系整理结构，完成后可用 ⌘Z 撤销。','开始整理');
  var v=NSView.alloc().initWithFrame(NSMakeRect(0,0,460,274));
  var fields=[checkbox('规范默认图层名（保留已有业务命名）',true,240),checkbox('清理无内容、无样式的空组',true,208),checkbox('按阅读顺序排列图层列表',true,176),checkbox('自动归拢区域，并细分列表项和图标文字',true,144),checkbox('优先完整卡片（允许极轻微阴影色差）',true,112),checkbox('显示归组过程（临时轮廓高亮，不移动设计稿）',true,80)];
  fields.forEach(function(f,i){var key=['rename','cleanup','sort','group','allowSubtleShadows','visualize'][i];if(typeof pref[key]==='boolean')f.setState(pref[key]?1:0);v.addSubview(f);});
  v.addSubview(label('相邻元素最大间距', [0,40,170,24]));
  var gap=NSPopUpButton.alloc().initWithFrame_pullsDown(NSMakeRect(180,40,110,26),false);
  gap.addItemsWithTitles(['8 px','16 px','24 px','32 px']);gap.selectItemAtIndex([8,16,24,32].indexOf(pref.gap)>=0?[8,16,24,32].indexOf(pref.gap):1);v.addSubview(gap);
  v.addSubview(label('纯本地整理，不联网；取消优先完整卡片可要求像素完全一致。',[0,0,460,28],11));
  a.setAccessoryView(v);
  return {alert:a,read:function(){return {rename:Number(fields[0].state())===1,cleanup:Number(fields[1].state())===1,sort:Number(fields[2].state())===1,group:Number(fields[3].state())===1,allowSubtleShadows:Number(fields[4].state())===1,visualize:Number(fields[5].state())===1,gap:[8,16,24,32][Number(gap.indexOfSelectedItem())]};}};
}
function buildAssets(result,onProgress) {
  var count=result.assets.length,pref=preferences('assets');
  var a=alert('自动切片 · 0.5.7 · '+count+' 个资源',result.scope+'\n在 Sketch 内创建切片，之后通过蓝湖插件上传画板。','创建 / 更新切片');
  var v=NSView.alloc().initWithFrame(NSMakeRect(0,0,480,428));
  var scroll=NSScrollView.alloc().initWithFrame(NSMakeRect(0,226,480,200));scroll.setHasVerticalScroller(true);
  var content=NSView.alloc().initWithFrame(NSMakeRect(0,0,460,Math.max(200,count*28)));
  var assetFields=result.assets.map(function(asset,i){
    if(onProgress&&i%16===0)onProgress({stage:'正在准备资源列表',name:i+' / '+count+' 项'});
    var text=(asset.kind==='image'?'图片 · ':asset.kind==='icon'?'图标 · ':'已标记 · ')+asset.node.name;
    var b=checkbox(text,true,Number(content.frame().size.height)-(i+1)*28);b.setToolTip(asset.node.name+' · '+asset.node.width+' × '+asset.node.height);content.addSubview(b);return b;
  });
  scroll.setDocumentView(content);v.addSubview(scroll);
  content.scrollPoint(NSMakePoint(0,Math.max(0,Number(content.frame().size.height)-200)));
  v.addSubview(label('图片 PNG 倍率',[0,148,80,24]));
  var scales=[1,2,3].map(function(n,i){var b=checkbox(n+'x',!Array.isArray(pref.scales)||pref.scales.indexOf(n)>=0,148);b.setFrame(NSMakeRect(110+i*80,148,70,24));v.addSubview(b);return b;});
  var svg=checkbox('矢量图标使用 SVG（图片仍使用 PNG）',pref.svg!==false,116);v.addSubview(svg);
  v.addSubview(label('图标画布',[0,80,120,24]));
  var iconSize=NSPopUpButton.alloc().initWithFrame_pullsDown(NSMakeRect(115,80,190,26),false);iconSize.addItemsWithTitles(['自动（16 / 24 / 32…）','16 × 16','24 × 24','32 × 32','48 × 48','64 × 64']);iconSize.selectItemAtIndex(Math.max(0,['auto',16,24,32,48,64].indexOf(pref.iconSize)));v.addSubview(iconSize);
  v.addSubview(label('避开邻近文字',[320,80,150,24],11));
  v.addSubview(label('仅创建文档内切片，不导出本地文件。',[0,48,470,24],12));
  var validation=label('',[0,12,470,28],11),selection=label('',[0,192,290,24],12);v.addSubview(validation);v.addSubview(selection);
  function read(){return {candidates:result.assets.filter(function(_,i){return Number(assetFields[i].state())===1;}),scales:[1,2,3].filter(function(_,i){return Number(scales[i].state())===1;}),svg:Number(svg.state())===1,iconSize:['auto',16,24,32,48,64][Number(iconSize.indexOfSelectedItem())]};}
  function update(){var value=read(),message=validateAssets(value);selection.setStringValue('已选 '+value.candidates.length+' / '+count+' 个资源');validation.setStringValue(message||'完成后保存文档，再通过蓝湖上传。');a.buttons()[0].setEnabled(!message);}
  assetFields.concat(scales,[svg]).forEach(function(b){b.setCOSJSTargetFunction(update);});
  var all=button('全选',300,190,function(){assetFields.forEach(function(b){b.setState(1);});update();}),none=button('全不选',390,190,function(){assetFields.forEach(function(b){b.setState(0);});update();});v.addSubview(all);v.addSubview(none);
  a.setAccessoryView(v);update();
  return {alert:a,read:read,update:update,fields:{assets:assetFields,scales:scales,svg:svg,all:all,none:none},validation:validation};
}
function validateAssets(value){
 if(!value.candidates.length)return '请至少选中一个资源。';
 if(value.candidates.some(function(a){return !(value.svg&&a.kind==='icon');})&&!value.scales.length)return '所选资源需要 PNG，请至少选择一种倍率。';
 return '';
}
function organize(scope){var panel=buildOrganize(scope);while(Number(panel.alert.runModal())===1000){var value=panel.read();if(!value.rename&&!value.cleanup&&!value.sort&&!value.group){panel.alert.setInformativeText(scope+'\n请至少开启一项整理功能，当前设置已保留。');continue;}save('organize',value);return value;}return null;}
function assets(result,prepared){var panel=prepared||buildAssets(result);while(Number(panel.alert.runModal())===1000){var value=panel.read(),error=validateAssets(value);if(error){panel.validation.setStringValue(error);continue;}save('assets',{scales:value.scales,svg:value.svg,iconSize:value.iconSize});return value;}return null;}
function buildResult(title,summary,errors,document){
 var a=NSAlert.alloc().init();a.setMessageText(title);a.setInformativeText(summary);a.addButtonWithTitle('好');
 var ids=(errors||[]).map(function(e){return e.id;}).filter(function(id){return id&&document.getLayerWithID(id);});
 if(ids.length)a.addButtonWithTitle('选中未处理图层');
 if(errors&&errors.length){
  var full=errors.map(function(e,i){return (i+1)+'. '+e.name+'\n'+e.error;}).join('\n\n'),scroll=NSScrollView.alloc().initWithFrame(NSMakeRect(0,0,480,190)),text=NSTextView.alloc().initWithFrame(NSMakeRect(0,0,460,190));
  text.setString(full);text.setEditable(false);text.setSelectable(true);text.setFont(NSFont.systemFontOfSize(12));text.setVerticallyResizable(true);text.setHorizontallyResizable(false);text.textContainer().setWidthTracksTextView(true);text.setMinSize(NSMakeSize(460,190));text.setMaxSize(NSMakeSize(460,1000000));text.textContainer().setContainerSize(NSMakeSize(460,1000000));text.sizeToFit();scroll.setHasVerticalScroller(true);scroll.setDocumentView(text);a.setAccessoryView(scroll);a.addButtonWithTitle('复制完整结果');
 }
 return {alert:a,ids:ids,full:full||'',textView:text};
}
function locate(document,ids){var layers=ids.map(function(id){return document.getLayerWithID(id);}).filter(Boolean);if(!layers.length)return;document.selectedPage=layers[0].getParentPage();document.selectedLayers.layers=layers;document.centerOnLayer(layers[0]);}
function showResult(title,summary,errors,document){
 var panel=buildResult(title,summary,errors,document),a=panel.alert,ids=panel.ids,owner=document.sketchObject.windowForSheet(),app=NSApplication.sharedApplication(),previousKey=app.keyWindow(),window,attached=false;
 if(owner.attachedSheet())throw new Error('请先关闭当前文档的其他弹窗。');
 var fiber=require('sketch/async').createFiber();
 fiber.onCleanup(function(){if(attached)owner.endSheet(window);if(window)window.orderOut(null);});
 function close(){fiber.cleanup();}
 try{
  a.layout();window=a.window();window.setReleasedWhenClosed(false);
  a.buttons()[0].setCOSJSTargetFunction(close);
  if(ids.length)a.buttons()[1].setCOSJSTargetFunction(function(){close();locate(document,ids);});
  if(errors&&errors.length){var copy=a.buttons()[ids.length?2:1];copy.setCOSJSTargetFunction(function(){var clipboard=NSPasteboard.generalPasteboard();clipboard.clearContents();clipboard.setString_forType(title+'\n'+summary+'\n\n'+panel.full,'public.utf8-plain-text');copy.setTitle('已复制');});}
  owner.beginSheet_completionHandler(window,null);attached=true;
  if(previousKey&&previousKey!==owner&&previousKey!==window)previousKey.makeKeyWindow();
  return {close:close,panel:panel,window:window};
 }catch(error){close();throw error;}
}

exports.organize=organize;exports.assets=assets;exports.showResult=showResult;exports.validateAssets=validateAssets;
exports.buildOrganize=buildOrganize;exports.buildAssets=buildAssets;exports.buildResult=buildResult;exports.locate=locate;
