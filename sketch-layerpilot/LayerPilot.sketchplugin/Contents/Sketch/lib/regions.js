'use strict';
var core=require('./core');
var layout=require('./layout');
function inside(a,b,t){t=t||0;return b.x>=a.x-t&&b.y>=a.y-t&&b.x+b.width<=a.x+a.width+t&&b.y+b.height<=a.y+a.height+t;}
function clip(n,p){var x=Math.max(0,n.x),y=Math.max(0,n.y),right=Math.min(p.width,n.x+n.width),bottom=Math.min(p.height,n.y+n.height);return {x:x,y:y,width:Math.max(0,right-x),height:Math.max(0,bottom-y)};}
function has(n,type){return n.type===type||(n.children||[]).some(function(c){return has(c,type);});}
function image(n){return n.imageFill||has(n,'Image');}
var movable=layout.movable;
// Contract a set of siblings only when every overlapping outside layer can keep
// its original painter order. Masks remain barriers, even when geometrically disjoint.
function insertion(nodes,ids,preferred){
  var set={};ids.forEach(function(id){set[id]=true;});var low=0,high=nodes.length;
  var flags=core.maskedSiblings(nodes);
  nodes.forEach(function(a,i){if(!set[a.id]||a.hidden)return;
    nodes.forEach(function(b,j){if(set[b.id]||b.hidden)return;
      if(b.mask||b.breakMask||flags[j]||a.compositing||b.compositing||core.intersects(a.paintBounds||a,b.paintBounds||b)) {
        if(i<j)high=Math.min(high,j);else low=Math.max(low,j+1);
      }
    });
  });
  if(low>high)return null;
  var first=typeof preferred==='number'?preferred:nodes.findIndex(function(n){return set[n.id];});
  return Math.max(low,Math.min(high,first));
}
// A later full-frame painted rectangle separates an overlay from the page behind it.
// Do not infer ownership across this painter-order boundary.
function overlayIndex(parent){
 if(!(parent.isFrame||parent.type==='Artboard'))return -1;
 var cs=parent.children||[];
 for(var i=1;i<cs.length-2;i++){
  var n=cs[i];
  if(movable(n)&&layout.background(n)&&n.x<=1&&n.y<=1&&n.width>=parent.width-2&&n.height>=parent.height-2)return i;
 }
 return -1;
}
exports.overlayIndex=overlayIndex;
function plans(parent,options){
  var opts=Object.assign({gap:16},options||{});
  if(!(parent.isFrame||parent.type==='Artboard'||parent.type==='Group')||parent.generated&&!parent.region||parent.stack||parent.children.length>500)return [];
  var boundary=overlayIndex(parent);
  if(boundary>=0){
    var upper=parent.children.slice(boundary);
    // Keep masks/locked structures intact; declining is safer than mixing strata.
    if(upper.every(movable))return [{name:'弹窗区域',ids:upper.map(function(n){return n.id;}),kind:'container',reason:'全画板遮罩上方的独立界面',overlay:true}];
    return [];
  }
  var cs=parent.children,flags=core.maskedSiblings(cs),used={},result=[];
  cs=cs.map(function(n,i){return Object.assign({},n,{inMask:flags[i]});});
  var w=parent.width,h=parent.height;
  var footer=cs.filter(function(n){return movable(n)&&layout.background(n)&&n.width>w*.75&&n.height>=35&&n.height<h*.14&&n.y>h*.8&&cs.filter(function(c){return c.type==='Text'&&!c.hidden&&inside(n,c,1);}).length>=3;}).sort(function(a,b){return b.width-a.width;})[0];
  var cards=layout.containers(parent,cs).filter(function(n){return !footer||n.id!==footer.id;});
  var firstY=Math.min.apply(null,cards.map(function(n){return n.y;}));
  function add(name,area,anchor,filter,metadata){
    var members=cs.filter(function(n){return !used[n.id]&&movable(n)&&inside(clip(area,parent),clip(n,parent),2)&&(!filter||filter(n));});
    if(!members.length)return;
    if(members.length===1&&members[0].region)return;
    // A full-card candidate can be retried by the native renderer when only
    // conservative effect bounds block contraction. No geometric guess is applied.
    if(anchor&&layout.background(anchor)&&members.length>1&&insertion(cs,members.map(function(n){return n.id;}))===null){
      var plain=cs.map(function(n){return Object.assign({},n,{paintBounds:n});});
      var tentative=insertion(plain,members.map(function(n){return n.id;}));
      if(tentative!==null){
        result.push({name:name+(layout.title(members)?' · '+layout.title(members):''),ids:members.map(function(n){return n.id;}),kind:'container',reason:'背景包含内容，通过渲染差异检查后合并',verifyPixels:true,slot:tentative,anchor:anchor.id});
        members.forEach(function(n){used[n.id]=true;});return;
      }
    }
    // Split only at genuine painter-order conflicts. This lets card contents
    // become useful groups even when their shadowed backgrounds must stay below
    // neighboring cards. Each part still satisfies all outside-layer constraints.
    var parts=[],part=[];
    members.forEach(function(n){
      var next=part.concat(n);
      if(part.length&&insertion(cs,next.map(function(c){return c.id;}))===null){parts.push(part);part=[n];}
      else part=next;
    });
    if(part.length)parts.push(part);
    parts.forEach(function(group,i){
      if(group.length===1&&(group[0].type!=='Group'||group[0].region))return;
      var suffix=parts.length>1?' / '+(i+1):'';
      if(parts.length>1&&/^内容卡片/.test(name))suffix=group.some(function(c){return c.id===(anchor&&anchor.id);})?' / 背景':' / 内容';
      group.forEach(function(n){used[n.id]=true;});
      var heading=layout.title(group);
      result.push({name:name+suffix+(heading&&/^(内容卡片|内容区|导航项)/.test(name)?' · '+heading:''),ids:group.map(function(n){return n.id;}),anchor:anchor&&anchor.id,rect:area,kind:metadata&&metadata.kind||'container',reason:metadata&&metadata.reason||'背景包围内容或明确的页面区域'});
    });
  }
  // Identify the floating action separately so it is not swallowed by a card.
  cs.filter(function(n){return movable(n)&&!n.region&&n.type==='Group'&&n.exportable&&n.x>w*.6&&n.y>h*.55&&n.width>=40&&n.width<=96&&Math.abs(n.width-n.height)<8;}).forEach(function(n){add('悬浮操作',n,n,function(c){return c.id===n.id;});});
  if(footer)add('底部导航',footer,footer);
  if(cards.length>=2&&firstY>40&&firstY<h*.3)add('顶部导航',{x:0,y:0,width:w,height:firstY+1},null);
  cards.forEach(function(n,i){
    var label=parent.region&&/导航/.test(parent.name)?'导航项':parent.region?'内容区':'内容卡片',above=[];
    // A repeated short control may have its caption immediately above its surface.
    // Only accept a unique, horizontally contained label outside all other cards.
    var peers=cards.filter(function(c){return Math.abs(c.y-n.y)<=2&&Math.abs(c.height-n.height)<=2&&Math.abs(c.width-n.width)<=4;});
    if(layout.background(n)&&n.height<=72&&n.width<=w*.5&&peers.length>=2&&!cs.some(function(c){return has(c,'Text')&&inside(n,c,1);})){
      above=cs.filter(function(c){return !used[c.id]&&movable(c)&&c.type==='Text'&&c.x>=n.x+4&&c.x+c.width<=n.x+n.width-4&&n.y-(c.y+c.height)>=0&&n.y-(c.y+c.height)<=24&&!cards.some(function(other){return other.id!==n.id&&inside(other,c,1);});});
    }
    if(above.length===1){var caption=above[0];add(label+' / '+String(i+1).padStart(2,'0'),core.union([n,caption]),n,function(c){return c.id===caption.id||inside(n,c,2);});}
    else add(label+' / '+String(i+1).padStart(2,'0'),n,n);
  });
  function available(){return cs.filter(function(n){return !used[n.id];});}
  function infer(plan,index){
    var set={};plan.ids.forEach(function(id){set[id]=true;});
    var members=cs.filter(function(n){return set[n.id]&&!used[n.id];});
    if(members.length!==plan.ids.length||members.length===cs.length||insertion(cs,plan.ids)===null)return;
    var label=(plan.kind==='row'?'列表项':'图标文字')+' / '+String(index+1).padStart(2,'0')+(plan.title?' · '+plan.title:'');
    add(label,core.union(members),null,function(n){return !!set[n.id];},plan);
  }
  layout.repeatedRows(parent,available(),opts.gap).forEach(infer);
  layout.pairs(parent,available(),opts.gap).forEach(infer);
  return result;
}
exports.plans=plans;exports.insertion=insertion;
