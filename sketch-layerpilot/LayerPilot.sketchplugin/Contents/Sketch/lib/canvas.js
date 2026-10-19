'use strict';
var sizes=[16,24,32,48,64];
function overlap(a,b){return a.x<b.x+b.width&&a.x+a.width>b.x&&a.y<b.y+b.height&&a.y+a.height>b.y;}
function choose(ink,artSize,preferred,texts){
  var extent=Math.max(ink.width,ink.height);
  function frame(size){return {x:ink.x+(ink.width-size)/2,y:ink.y+(ink.height-size)/2,width:size,height:size};}
  function clear(size){return !(texts||[]).some(function(t){return overlap(frame(size),t);});}
  var automatic=preferred==='auto',wanted=automatic?sizes.find(function(s){return s>=Math.max(artSize+4,extent)-.01;}):preferred;
  if(!wanted||wanted<extent-.01)return {error:'图标超出所选画布，请选择更大尺寸'};
  if(clear(wanted))return {size:wanted,frame:frame(wanted)};
  // Never enlarge a colliding canvas, move the glyph, or clip its painted bounds.
  if(automatic){var smaller=sizes.filter(function(s){return s<wanted&&s>=extent+1-.01&&clear(s);}).pop();if(smaller)return {size:smaller,frame:frame(smaller)};}
  return {error:'标准画布会与邻近文字重叠，请单独调整间距或切片尺寸'};
}
exports.choose=choose;exports.overlap=overlap;
