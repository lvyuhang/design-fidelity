'use strict';
// Find a filled, simple button surface around a smaller centred glyph. Stroke
// outlines, masks and arbitrary silhouettes never count as button backgrounds.
function contains(a,b,t){return b.x>=a.x-t&&b.y>=a.y-t&&b.x+b.width<=a.x+a.width+t&&b.y+b.height<=a.y+a.height+t;}
function safe(n){return !n.hidden&&!n.locked&&!n.mask&&!n.breakMask&&!n.compositing&&!n.stack;}
function vector(n){if(n.type==='ShapePath'||n.type==='Shape')return !n.imageFill;var cs=(n.children||[]).filter(function(c){return c.type!=='Slice';});return cs.length>0&&cs.every(vector);}
function artwork(n){
  var cs=(n.children||[]).filter(function(c){return c.type!=='Slice'&&!c.hidden;});
  if(!cs.length||n.type!=='Group')return n;
  var parts=cs.map(artwork),x=Math.min.apply(null,parts.map(function(c){return c.x;})),y=Math.min.apply(null,parts.map(function(c){return c.y;}));
  return Object.assign({},n,{x:n.x+x,y:n.y+y,width:Math.max.apply(null,parts.map(function(c){return c.x+c.width;}))-x,height:Math.max.apply(null,parts.map(function(c){return c.y+c.height;}))-y});
}
function surfaces(nodes){
  nodes=nodes.map(artwork);
  return nodes.filter(function(bg){
    if(!safe(bg)||!bg.buttonSurface||bg.width<12||bg.height<12||bg.width>96||bg.height>96)return false;
    return nodes.some(function(n){return n.id!==bg.id&&safe(n)&&vector(n)&&!n.buttonSurface&&contains(bg,n,0.5)&&
      n.width*n.height<bg.width*bg.height*.55&&Math.max(n.width/bg.width,n.height/bg.height)<.79&&
      Math.abs(n.x+n.width/2-bg.x-bg.width/2)<bg.width*.18&&Math.abs(n.y+n.height/2-bg.y-bg.height/2)<bg.height*.18;});
  }).map(function(n){return n.id;});
}
// Attach contained vector accents (e.g. the second stroke of a heart) to their
// enclosing glyph, while retaining separate adjacent toolbar icons.
function clusters(nodes,kind){
  var bg=surfaces(nodes),available=nodes.filter(function(n){return safe(n)&&!n.region&&vector(n)&&bg.indexOf(n.id)<0;}),claimed={},out=[];
  available.slice().sort(function(a,b){return b.width*b.height-a.width*a.height;}).forEach(function(a){
    if(claimed[a.id]||kind(a)!=='icon'||a.width>96||a.height>96)return;
    var parts=available.filter(function(b){return !claimed[b.id]&&b.id!==a.id&&contains(a,b,.75)&&b.width*b.height<a.width*a.height*.45;});
    if(parts.length){var members=[a].concat(parts);members.forEach(function(n){claimed[n.id]=true;});out.push(members);}
  });
  return {backgrounds:bg,clusters:out};
}
exports.surfaces=surfaces;exports.clusters=clusters;exports.vector=vector;

exports.artwork=artwork;
