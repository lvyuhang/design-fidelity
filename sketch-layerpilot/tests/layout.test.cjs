const assert=require('node:assert/strict');
const regions=require('../LayerPilot.sketchplugin/Contents/Sketch/lib/regions');
const layout=require('../LayerPilot.sketchplugin/Contents/Sketch/lib/layout');
module.exports=function(){
 let passed=0;const checks=[];
 function test(name,fn){fn();passed++;checks.push(name);}
 function n(id,x,y,w,h,extra={}){return Object.assign({id,name:id,type:'ShapePath',x,y,width:w,height:h,children:[]},extra);}
 function text(id,x,y,w=80,h=20,extra={}){return n(id,x,y,w,h,{type:'Text',text:id,fontSize:16,...extra});}
 function board(cs,w=375,h=812){return {isFrame:true,width:w,height:h,children:cs};}
 function together(plans,...ids){return plans.some(p=>ids.every(id=>p.ids.includes(id)));}
 test('a single full-width card is recognized',()=>{
  const cs=[n('bg',12,120,351,240),text('标题',30,160),n('image',30,210,100,100,{type:'Image'})];
  assert(together(regions.plans(board(cs)),'bg','标题','image'));
 });
 test('four-column desktop cards do not depend on mobile proportions',()=>{
  const cs=[];for(let i=0;i<4;i++)cs.push(n('bg'+i,20+i*250,100,230,260));
  for(let i=0;i<4;i++)cs.push(text('title'+i,36+i*250,300),n('img'+i,36+i*250,116,198,160,{type:'Image'}));
  const plans=regions.plans(board(cs,1040,800));
  for(let i=0;i<4;i++)assert(together(plans,'bg'+i,'title'+i,'img'+i));
 });
 test('single-column list cards enclose their own rows',()=>{
  const cs=[];for(let i=0;i<4;i++)cs.push(n('bg'+i,12,80+i*130,351,110));
  for(let i=0;i<4;i++)cs.push(text('title'+i,80,90+i*130),n('img'+i,24,90+i*130,40,40,{type:'Image'}));
  const plans=regions.plans(board(cs));for(let i=0;i<4;i++)assert(together(plans,'bg'+i,'title'+i,'img'+i));
 });
 test('image-fill backgrounds are never treated as layout panels',()=>{
  const cs=[n('photo',12,120,351,240,{imageFill:true}),text('caption',30,160)];
  assert.equal(layout.containers(board(cs),cs).length,0);
 });
 test('borderless repeated rows collect title, subtitle and trailing icon',()=>{
  const cs=[];for(let i=0;i<4;i++)cs.push(n('avatar'+i,16,80+i*80,40,40,{type:'Image'}));
  for(let i=0;i<4;i++)cs.push(text('用户'+i,68,80+i*80),text('副标题'+i,68,104+i*80,150,16,{fontSize:12}),n('arrow'+i,332,91+i*80,16,16,{customPath:true}));
  const plans=regions.plans(board(cs));
  for(let i=0;i<4;i++)assert(together(plans,'avatar'+i,'用户'+i,'副标题'+i,'arrow'+i));
  assert.equal(plans.filter(p=>p.kind==='row').length,4);
 });
 test('text-only settings rows with distant values remain separate',()=>{
  const cs=[];for(let i=0;i<4;i++)cs.push(text('设置'+i,16,80+i*60,60+i*8),text('值'+i,260,80+i*60,60));
  const plans=regions.plans(board(cs));for(let i=0;i<4;i++)assert(together(plans,'设置'+i,'值'+i));
  assert(plans.every(p=>p.ids.length===2));
 });
 test('irregular anchors do not invent repeated list rows',()=>{
  const cs=[0,30,220].flatMap((y,i)=>[n('img'+i,16,y,24,24,{type:'Image'}),text('label'+i,48,y)]);
  assert.equal(layout.repeatedRows(board(cs),cs,16).length,0);
 });
 test('mutual-nearest pairs do not swallow a whole toolbar',()=>{
  const cs=[text('页面标题',10,10,100,24)];
  for(let i=0;i<4;i++)cs.push(n('icon'+i,20+i*80,90,24,24,{customPath:true}),text('操作'+i,18+i*80,122,28,16));
  const plans=regions.plans(board(cs));for(let i=0;i<4;i++)assert(together(plans,'icon'+i,'操作'+i));
  assert(plans.filter(p=>p.kind==='pair').every(p=>p.ids.length===2));
 });
 test('ambiguous equidistant labels are left for manual grouping',()=>{
  const cs=[n('icon',50,50,24,24,{customPath:true}),text('a',82,48,40,20),text('b',82,56,40,20)];
  assert.equal(layout.pairs(board(cs),cs,16).length,0);
 });
 test('Chinese captions drive names, default-copy variants do not leak',()=>{
  assert.equal(layout.title([text('用户名',0,0),text('动态内容',0,50,100,24,{fontSize:20}),text('98',100,80)]),'动态内容');
  const c=require('../LayerPilot.sketchplugin/Contents/Sketch/lib/core');
  assert.equal(c.rename(text('文本备份 4',0,0,80,20,{text:'真实内容'})),'文本 / 真实内容');
 });
 test('ordinary content groups can be analyzed without requiring a frame',()=>{
  const cs=[n('bg',10,10,180,180),text('label',20,30),n('outside',300,300,20,20)];
  assert(together(regions.plans({type:'Group',width:400,height:400,children:cs}),'bg','label'));
 });
 return {passed,checks};
};
