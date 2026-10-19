'use strict';
var upstream = require('./upstream');
var glyphs=require('./glyphs');
var GENERIC = /^(group|编组|组合|rectangle|矩形|rounded rectangle|圆角矩形|shape|形状|path|路径|oval|椭圆|椭圆形|text|文本|image|bitmap|位图|图片|vector|矢量)(?:[\s_-]*\d+|\s*(?:copy|副本|备份))*$/i;
var ICON = /(?:^|[\s/_-])(icon|ic|ico)(?:$|[\s/_-])|图标/i;
var PHOTO = /(?:^|[\s/_-])(image|img|photo|avatar|banner|logo)(?:$|[\s/_-])|图片|照片|头像|插画/i;
var LAYOUT = /(?:^|[\s/_-])(background|bg|container|layout|card|button|section|divider)(?:$|[\s/_-])|背景|容器|布局|卡片|按钮|分割线/i;
function area(r) { return r.width * r.height; }
function valid(r) { return r && [r.x,r.y,r.width,r.height].every(Number.isFinite) && r.width > 0 && r.height > 0; }
function intersects(a,b) { return a.x < b.x+b.width && a.x+a.width > b.x && a.y < b.y+b.height && a.y+a.height > b.y; }
function contains(a,b) { return b.x >= a.x-.1 && b.y >= a.y-.1 && b.x+b.width <= a.x+a.width+.1 && b.y+b.height <= a.y+a.height+.1; }
function union(nodes) {
  var x=Math.min.apply(null,nodes.map(function(n){return n.x;}));
  var y=Math.min.apply(null,nodes.map(function(n){return n.y;}));
  return {x:x,y:y,width:Math.max.apply(null,nodes.map(function(n){return n.x+n.width;}))-x,height:Math.max.apply(null,nodes.map(function(n){return n.y+n.height;}))-y};
}
function descendants(n) { return (n.children||[]).reduce(function(a,c){return a.concat([c],descendants(c));},[]); }
function hasText(n) { return n.type==='Text'||(n.children||[]).some(hasText); }
function hasImage(n) { return n.type==='Image'||n.imageFill||(n.children||[]).some(hasImage); }
function visible(n) { return !n.hidden && !n.locked && valid(n); }
function namedResource(n) { return ICON.test(n.name)||PHOTO.test(n.name); }
function vectorOnly(n) {
  if (n.type==='Shape'||n.type==='ShapePath') return !hasImage(n);
  return (n.children||[]).length>0 && n.children.every(vectorOnly);
}
function resourceKind(n) {
  if(n.sliceWrapper)return null;
  var artwork=(n.children||[]).filter(function(c){return c.type!=='Slice';});
  if(artwork.length!==(n.children||[]).length)return resourceKind(Object.assign({},n,{children:artwork}));
  if (!visible(n)||n.type==='Text'||n.type==='HotSpot'||n.type==='Slice'||n.type==='Page'||n.type==='SymbolMaster') return null;
  // Screen export presets are common in imported files; scan inside them for assets.
  if(n.type==='Artboard'||n.isFrame&&!n.isGraphic) {
    if(n.stack||hasText(n))return null;
    if(!namedResource(n)&&!(n.clipsContents&&(n.children||[]).length===1&&hasImage(n)))return null;
  }
  if (n.exportable) return resourceKind(Object.assign({},n,{exportable:false}))||(hasImage(n)&&!hasText(n)?'image':null);
  if (n.type==='Image'||n.imageFill) return 'image';
  // Spatial layout groups are not automatically reclassified as icon assets.
  if(n.glyph)return hasImage(n)?'image':'icon';
  if (n.generated&&!namedResource(n)) return null;
  if (n.stack||hasText(n)) return null;
  if (LAYOUT.test(n.name)&&!namedResource(n)) return null;
  if (n.type==='SymbolInstance') return PHOTO.test(n.name)?'image':ICON.test(n.name)?'icon':null;
  if (namedResource(n)) return hasImage(n)?'image':vectorOnly(n)?'icon':PHOTO.test(n.name)?'image':'icon';
  if (n.clipsContents&&(n.children||[]).length===1&&hasImage(n)&&!hasText(n)) return 'image';
  if (n.isFrame&&!n.isGraphic) return null;
  if ((n.children||[]).some(function(c){return c.mask;})&&hasImage(n)) return 'image';
  if (n.width>128||n.height>128||n.width<4||n.height<4) return null;
  if (n.type==='Shape') return 'icon';
  if (n.type==='ShapePath'&&(n.customPath||n.shapeType&&['Rectangle','Oval'].indexOf(n.shapeType)<0)) return 'icon';
  if ((n.children||[]).length>=1 && vectorOnly(n)) {
    // Avoid treating a toolbar containing several already named icons as one icon.
    if (n.children.filter(namedResource).length>1) return null;
    return 'icon';
  }
  return null;
}
function discover(nodes) {
  var found=[],skipped=0;
  function siblings(cs,masked,clips,ox,oy,supersedes){
    var flags=maskedSiblings(cs),analysis=glyphs.clusters(cs,resourceKind),claimed={};
    analysis.clusters.forEach(function(parts){
      // Compound grouping is performed by the engine after its painter-order check.
      if(masked||parts.some(function(p){return flags[cs.indexOf(p)];}))return;
      var rect=union(parts),absolute={x:ox+rect.x,y:oy+rect.y,width:rect.width,height:rect.height};
      if(clips.some(function(c){return cropRisk(c,{x:absolute.x-c.x,y:absolute.y-c.y,width:rect.width,height:rect.height});}))return;
      var node=Object.assign({},parts[0],rect,{name:parts[0].name,id:parts[0].id});
      found.push({node:node,kind:'icon',members:parts.map(function(p){claimed[p.id]=true;return p.id;}),supersedes:supersedes||[]});
    });
    cs.forEach(function(c,i){if(analysis.backgrounds.indexOf(c.id)<0&&!claimed[c.id]){
      var old=(supersedes||[]).slice();cs.filter(function(bg){return analysis.backgrounds.indexOf(bg.id)>=0&&contains(bg,c);}).forEach(function(bg){old.push(bg.id);descendants(bg).forEach(function(n){old.push(n.id);});});
      walk(c,masked||flags[i],clips,ox,oy,old);
    }});
  }
  function walk(n,masked,clips,ox,oy,supersedes) {
    if(n.hidden||n.locked||n.type==='SymbolMaster') {skipped++;return;}
    var rect={x:ox+n.x,y:oy+n.y,width:n.width,height:n.height};
    var cropped=clips.some(function(c){return cropRisk(c,{x:rect.x-c.x,y:rect.y-c.y,width:rect.width,height:rect.height});});
    var cs=n.children||[],backgrounds=glyphs.surfaces(cs);
    var kind=resourceKind(n);
    if(kind&&!masked&&!cropped&&!backgrounds.length) {found.push({node:n,kind:kind,supersedes:(supersedes||[]).concat(n.supersedes||[])});return;}
    if(kind&&(masked||cropped))skipped++;
    var next=clips.slice();
    if(n.clipsContents)next.push({x:rect.x,y:rect.y,width:n.width,height:n.height,clipsContents:true,cornerRadius:n.cornerRadius});
    siblings(cs,masked,next,rect.x,rect.y,backgrounds.length?(supersedes||[]).concat(n.id):supersedes);
  }
  nodes.forEach(function(n){walk(n,!!n.ancestorMask,[],0,0,[]);});
  return {assets:found,skipped:skipped};
}
// A break ends the preceding mask chain; it does not turn the container into a mask.
function maskedSiblings(nodes) {
  var active=false;
  return nodes.map(function(n){
    if(n.breakMask)active=false;
    if(n.mask)active=true;
    return active;
  });
}
function cropRisk(parent,rect) {
  if(!parent.clipsContents)return false;
  if(!contains({x:0,y:0,width:parent.width,height:parent.height},rect))return true;
  var r=parent.cornerRadius||0;
  // Conservatively skip any resource touching the bounding boxes of rounded corners.
  return r>0&&(rect.x<r||rect.x+rect.width>parent.width-r)&&(rect.y<r||rect.y+rect.height>parent.height-r);
}
function rename(n) {
  if(!GENERIC.test(n.name||'')||n.exportable||n.type==='SymbolMaster') return n.name;
  if(n.type==='Text') return '文本 / '+String(n.text||'').replace(/\s+/g,' ').trim().slice(0,28);
  var kind=resourceKind(n);
  if(kind==='image') return '图片';
  if(kind==='icon') return '图标';
  if(n.type==='Group') {
    var t=descendants(n).find(function(c){return c.type==='Text'&&c.text&&!c.hidden;});
    return t ? '内容 / '+t.text.replace(/\s+/g,' ').trim().slice(0,24) : n.name;
  }
  return n.name;
}
function groupName(nodes) {
  var t=[];
  nodes.forEach(function(n){t=t.concat(n.type==='Text'?[n]:descendants(n).filter(function(c){return c.type==='Text';}));});
  t.sort(function(a,b){return a.y-b.y||a.x-b.x;});
  if(t.length) return '内容 / '+String(t[0].text||'').replace(/\s+/g,' ').trim().slice(0,24);
  return nodes.some(hasImage)?'图文组':'元素组';
}
function safeNode(n) { return visible(n)&&!n.risk&&!n.mask&&!n.inMask&&!n.breakMask&&!n.isFrame&&n.type!=='SymbolMaster'&&n.type!=='Slice'&&n.type!=='HotSpot'&&!n.exportable&&!n.flow; }
function close(a,b,gap) {
  if(intersects(a,b)) return true;
  var ox=Math.min(a.x+a.width,b.x+b.width)-Math.max(a.x,b.x);
  var oy=Math.min(a.y+a.height,b.y+b.height)-Math.max(a.y,b.y);
  var dx=Math.max(a.x-b.x-b.width,b.x-a.x-a.width,0);
  var dy=Math.max(a.y-b.y-b.height,b.y-a.y-a.height,0);
  return (oy>=Math.min(a.height,b.height)*.6&&dx<=gap)||(ox>=Math.min(a.width,b.width)*.6&&dy<=gap);
}
function planGroups(parent,gap) {
  var cs=parent.children||[],used={},groups=[];
  if(parent.stack||parent.generated||cs.length>300) return [];
  var masked=maskedSiblings(cs);cs=cs.map(function(n,i){return Object.assign({},n,{inMask:!!n.inMask||masked[i]});});
  function accept(indices) {
    if(indices.length<2||indices.length===cs.length) return false;
    var lo=Math.min.apply(null,indices),hi=Math.max.apply(null,indices);
    // Only contiguous painter-order ranges may be reparented. Nothing can cross them.
    if(hi-lo+1!==indices.length||indices.some(function(i){return used[i]||cs[i].generated||!safeNode(cs[i]);})) return false;
    indices.forEach(function(i){used[i]=true;});
    groups.push(indices.map(function(i){return cs[i].id;}));return true;
  }
  // First identify a background and the content it encloses.
  cs.forEach(function(n,i){
    if(!safeNode(n)||n.type!=='ShapePath'||n.customPath||area(n)>=area(parent)*.85) return;
    var inside=[];
    cs.forEach(function(c,j){if(j>i&&contains(n,c)&&safeNode(c)) inside.push(j);});
    if(inside.length) accept([i].concat(inside));
  });
  // Then proximity clusters for remaining loose labels/icons.
  var seen={};
  cs.forEach(function(n,i){
    if(used[i]||seen[i]||!safeNode(n)) return;
    if(cs.filter(function(c,j){return j!==i&&contains(n,c);}).length>1) return;
    var ids=[i],queue=[i];seen[i]=true;
    while(queue.length) {
      var k=queue.shift();
      cs.forEach(function(c,j){
        if(!used[j]&&!seen[j]&&safeNode(c)&&close(cs[k],c,gap)) {
          if(cs.filter(function(d,z){return z!==j&&contains(c,d);}).length>1) return;
          seen[j]=true;ids.push(j);queue.push(j);
        }
      });
    }
    ids.sort(function(a,b){return a-b;});
    if(ids.length<=24) accept(ids);
  });
  return groups;
}
function sortedOrder(nodes) {
  var out=nodes.slice();
  if(out.length>300) return out.map(function(n){return n.id;});
  var masked=maskedSiblings(out);out=out.map(function(n,i){return Object.assign({},n,{inMask:!!n.inMask||masked[i]});});
  function compare(a,b){return b.y-a.y||b.x-a.x;}
  // Adjacent swaps only. Every overlapping pair keeps its original painter order.
  for(var pass=0;pass<out.length;pass++) {
    var changed=false;
    for(var i=0;i<out.length-1;i++) {
      var a=out[i],b=out[i+1];
      if(safeNode(a)&&safeNode(b)&&!intersects(a,b)&&compare(a,b)>0) {
        out[i]=b;out[i+1]=a;changed=true;
      }
    }
    if(!changed) break;
  }
  return out.map(function(n){return n.id;});
}
function filename(name,id) {
  var clean=upstream.nameParts(String(name||'asset')).map(upstream.formatNameUnderLine).join('_')
    .replace(/[\x00-\x1f\x7f<>:"|?*]/g,'_').replace(/^[.\s_]+|[.\s_]+$/g,'').slice(0,64)||'asset';
  return clean+'_'+String(id).replace(/[^a-zA-Z0-9]/g,'').toLowerCase();
}
exports.resourceKind=resourceKind;exports.discover=discover;exports.rename=rename;
exports.groupName=groupName;exports.planGroups=planGroups;exports.sortedOrder=sortedOrder;
exports.filename=filename;exports.intersects=intersects;exports.contains=contains;exports.union=union;
exports.cropRisk=cropRisk;
exports.maskedSiblings=maskedSiblings;
