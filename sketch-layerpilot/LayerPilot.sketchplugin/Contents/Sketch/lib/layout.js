'use strict';
// Deterministic geometric inference. No model, network, OCR or learned weights.
var core=require('./core');
function area(n){return n.width*n.height;}
function valid(n){return n&&[n.x,n.y,n.width,n.height].every(Number.isFinite)&&n.width>0&&n.height>0;}
function inside(a,b,t){t=t||0;return b.x>=a.x-t&&b.y>=a.y-t&&b.x+b.width<=a.x+a.width+t&&b.y+b.height<=a.y+a.height+t;}
function has(n,type){return n.type===type||(n.children||[]).some(function(c){return has(c,type);});}
function image(n){return n.imageFill||has(n,'Image');}
function text(n){return has(n,'Text');}
function resource(n){if(n.sliceWrapper){var cs=(n.children||[]).filter(function(c){return c.type!=='Slice';});return cs.length===1?core.resourceKind(cs[0]):null;}return core.resourceKind(n);}
function movable(n){return valid(n)&&!n.hidden&&!n.locked&&!n.mask&&!n.breakMask&&!n.inMask&&!n.compositing&&!n.isFrame&&!n.stack&&['Slice','HotSpot','SymbolMaster','Page','Artboard'].indexOf(n.type)<0;}
function background(n){return n.type==='ShapePath'&&!n.customPath&&!n.imageFill&&(!n.shapeType||n.shapeType==='Rectangle')&&n.painted!==false;}
function similarity(a,b){return Math.abs(a-b)<=Math.max(2,Math.max(a,b)*.15);}
function title(nodes){
  var texts=[];
  function walk(n,ox,oy){if(n.hidden)return;if(n.type==='Text'&&n.text&&!/^[\s\d.,，。…+\-/%：:]+$/.test(n.text))texts.push({text:n.text,size:n.fontSize||12,x:ox+n.x,y:oy+n.y});(n.children||[]).forEach(function(c){walk(c,ox+n.x,oy+n.y);});}
  nodes.forEach(function(n){walk(n,0,0);});
  texts.sort(function(a,b){return b.size-a.size||a.y-b.y||a.x-b.x;});
  return texts.length?texts[0].text.replace(/\s+/g,' ').trim().slice(0,18):'';
}
// Backgrounds must enclose actual content and remain smaller than their parent.
// This accepts a single card, wide form rows and desktop grids without a column count.
function containers(parent,nodes){
  var candidates=nodes.filter(function(n){
    if(n.region||!movable(n)||n.width<48||n.height<28||area(n)>area(parent)*.85)return false;
    if(n.type==='Group'&&text(n)&&image(n))return true;
    if(!background(n))return false;
    var content=nodes.filter(function(c){return c.id!==n.id&&movable(c)&&inside(n,c,1)&&area(c)<area(n)*.98;});
    return content.some(function(c){return text(c)||image(c)||resource(c);});
  });
  // Outermost useful panels own their contents. Nested controls can be handled
  // within that panel, without stealing labels from adjacent panels.
  candidates=candidates.filter(function(n){return !candidates.some(function(o){return o.id!==n.id&&area(o)>area(n)*1.02&&inside(o,n,1);});});
  return candidates.sort(function(a,b){return a.y-b.y||a.x-b.x;});
}
// Rows without backgrounds require at least three aligned, similarly sized visual
// anchors. Nearby text is assigned to the unique closest row, never by a flood fill.
function repeatedRows(parent,nodes,gap){
  function role(n){return n.type==='Text'?'text':image(n)?'image':'icon';}
  var anchors=nodes.filter(function(n){return movable(n)&&(!n.generated||n.sliceWrapper)&&(n.type==='Text'||image(n)||resource(n)==='icon'||n.type==='SymbolInstance')&&n.width>=12&&n.width<=(n.type==='Text'?parent.width*.6:Math.min(96,parent.width*.25))&&n.height>=8&&n.height<=96;});
  var families=[],used={};
  anchors.forEach(function(a){if(used[a.id])return;
    var family=anchors.filter(function(b){return !used[b.id]&&Math.abs(a.x-b.x)<=3&&role(a)===role(b)&&(role(a)==='text'?similarity(a.fontSize||12,b.fontSize||12):similarity(a.width,b.width))&&similarity(a.height,b.height);}).sort(function(a,b){return a.y-b.y;});
    if(family.length<3)return;
    var deltas=family.slice(1).map(function(n,i){return n.y-family[i].y;}).sort(function(a,b){return a-b;});
    var pitch=deltas[Math.floor(deltas.length/2)];
    if(pitch<family[0].height*1.2||pitch>Math.max(160,family[0].height*4)||deltas.some(function(d){return Math.abs(d-pitch)>pitch*.22;}))return;
    family.forEach(function(n){used[n.id]=true;});families.push({anchors:family,pitch:pitch});
  });
  var candidates=[];
  families.forEach(function(f){
    f.anchors.forEach(function(a,i){
      // Midlines prevent adjacent rows from borrowing each other's subtitle.
      var top=i?(f.anchors[i-1].y+f.anchors[i-1].height+a.y)/2:a.y-Math.min(f.pitch*.25,Math.max(gap,8));
      var next=f.anchors[i+1],bottom=next?(a.y+a.height+next.y)/2:a.y+a.height+Math.min(f.pitch*.25,Math.max(gap,8));
      var members=nodes.filter(function(n){return movable(n)&&(!n.generated||n.sliceWrapper)&&n.y>=top-.5&&n.y+n.height<=bottom+.5&&n.x>=a.x-2&&n.x+n.width<=parent.width+1&&n.height<f.pitch*.8&&(!background(n)||n.width<parent.width*.6&&n.height<f.pitch*.55);});
      // One visual anchor plus at least one label; exclude competing image columns.
      var near=members.filter(function(n){return n.id!==a.id&&(n.type==='Text'||role(a)==='text'&&resource(n)==='icon')&&n.x>=a.x+a.width-1&&(role(a)==='text'||n.x-(a.x+a.width)<=Math.max(gap*3,32));});
      if(!near.length||members.some(function(n){return n.id!==a.id&&image(n)&&n.width>a.width*.75;}))return;
      if(members.length>=2&&members.length<=16)candidates.push({ids:members.map(function(n){return n.id;}),kind:'row',reason:'至少三行元素对齐、尺寸或文字样式相近，行间距稳定',title:role(a)==='text'?title([a]):title(near)});
    });
  });
  return candidates;
}
// Mutual-nearest icon/label pairs avoid the chaining failure of distance-only
// connected components (an entire toolbar/list becoming one giant group).
function pairs(parent,nodes,gap){
  var icons=nodes.filter(function(n){return movable(n)&&(!n.generated||n.sliceWrapper)&&!text(n)&&!image(n)&&n.width<=96&&n.height<=96&&resource(n)==='icon';});
  var labels=nodes.filter(function(n){return movable(n)&&n.type==='Text'&&!n.generated;});
  var edges=[];
  icons.forEach(function(a){labels.forEach(function(b){
    var dx=b.x-(a.x+a.width),dy=b.y-(a.y+a.height),cx=Math.abs(a.x+a.width/2-b.x-b.width/2),cy=Math.abs(a.y+a.height/2-b.y-b.height/2);
    var horizontal=dx>=-1&&dx<=gap&&cy<=Math.min(a.height,b.height)*.45;
    var vertical=dy>=-1&&dy<=gap&&cx<=Math.max(3,Math.min(a.width,b.width)*.25);
    if(horizontal||vertical)edges.push({a:a,b:b,distance:horizontal?dx+cy:dy+cx});
  });});
  edges.sort(function(a,b){return a.distance-b.distance||String(a.a.id).localeCompare(String(b.a.id));});
  var nearestIcon={},nearestLabel={};
  edges.forEach(function(e){if(!nearestIcon[e.a.id])nearestIcon[e.a.id]=e;if(!nearestLabel[e.b.id])nearestLabel[e.b.id]=e;});
  return edges.filter(function(e){
    if(nearestIcon[e.a.id]!==e||nearestLabel[e.b.id]!==e)return false;
    // Reject tied alternatives instead of deciding by incidental layer IDs.
    return !edges.some(function(o){return o!==e&&(o.a.id===e.a.id||o.b.id===e.b.id)&&Math.abs(o.distance-e.distance)<2;});
  }).map(function(e){return {ids:[e.a.id,e.b.id],kind:'pair',reason:'图标与文字互为最近邻，且中心线对齐',title:title([e.b])};});
}
exports.valid=valid;exports.inside=inside;exports.movable=movable;exports.containers=containers;
exports.repeatedRows=repeatedRows;exports.pairs=pairs;exports.title=title;exports.background=background;
