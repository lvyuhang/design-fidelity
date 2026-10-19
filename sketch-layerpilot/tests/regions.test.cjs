const assert=require('node:assert/strict');
const r=require('../LayerPilot.sketchplugin/Contents/Sketch/lib/regions');
const core=require('../LayerPilot.sketchplugin/Contents/Sketch/lib/core');
module.exports=function(){
 let passed=0;
 function test(name,fn){fn();passed++;}
 function n(id,x,y,width=40,height=40,extra={}){return Object.assign({id,name:id,type:'ShapePath',x,y,width,height,children:[]},extra);}
 test('disjoint interleaved siblings can be contracted',()=>{
  assert.notEqual(r.insertion([n('a',0,0),n('outside',200,0),n('b',0,50)],['a','b']),null);
 });
 test('overlapping outsiders keep painter order',()=>{
  assert.equal(r.insertion([n('a',0,0),n('outside',10,10),n('b',0,0)],['a','b']),null);
 });
 test('shadow extents and compositing are considered',()=>{
  const a=n('a',0,0,40,40,{paintBounds:{x:0,y:0,width:100,height:100}});
  assert.equal(r.insertion([a,n('outside',70,70),n('b',70,70)],['a','b']),null);
  assert.equal(r.insertion([n('a',0,0),n('blend',200,0,40,40,{compositing:true}),n('b',0,50)],['a','b']),null);
 });
 test('mask chains cannot be crossed even when spatially distant',()=>{
  assert.equal(r.insertion([n('a',0,0),n('mask',200,200,20,20,{mask:true}),n('b',0,50)],['a','b']),null);
 });
 test('two interleaved cards group their own labels and images',()=>{
  const cs=[n('bg1',0,80,160,220),n('bg2',200,80,160,220),n('text1',10,250,100,20,{type:'Text'}),n('image2',210,90,140,140,{type:'Image'}),n('image1',10,90,140,140,{type:'Image',risk:true}),n('text2',210,250,100,20,{type:'Text'})];
  const p=r.plans({isFrame:true,width:375,height:812,children:cs});
  assert(p.some(p=>['bg1','text1','image1'].every(id=>p.ids.includes(id))));
  assert(p.some(p=>['bg2','text2','image2'].every(id=>p.ids.includes(id))));
 });
 test('ambiguous shadows require an explicit native pixel proof',()=>{
  const cs=[n('bg1',0,80,160,220,{paintBounds:{x:-30,y:50,width:220,height:280}}),n('bg2',170,80,160,220,{paintBounds:{x:140,y:50,width:220,height:280}}),n('text1',10,250,145,20,{type:'Text'}),n('image1',10,90,145,140,{type:'Image'}),n('text2',180,250,140,20,{type:'Text'}),n('image2',180,90,140,140,{type:'Image'})];
  const p=r.plans({isFrame:true,width:375,height:812,children:cs});
  assert(p.some(p=>p.ids.includes('text1')&&p.ids.includes('image1')&&p.ids.includes('bg1')&&p.verifyPixels));
  p.forEach(p=>assert(r.insertion(cs,p.ids)!==null||p.verifyPixels));
 });
 test('protected layers remain outside; previous content regions can acquire a background',()=>{
  const cs=[n('bg1',0,80,160,220),n('bg2',200,80,160,220),n('text',10,250,100,20,{type:'Text'}),n('locked',10,100,40,40,{locked:true}),n('slice',10,100,40,40,{type:'Slice'}),n('done',10,160,40,40,{region:true})];
  const plans=r.plans({isFrame:true,width:375,height:812,children:cs});
  assert(plans.length);plans.forEach(p=>['locked','slice'].forEach(id=>assert(!p.ids.includes(id))));
  assert(plans.some(p=>p.ids.includes('done')&&p.ids.includes('bg1')));
  assert.equal(r.plans({isFrame:true,stack:true,width:375,height:812,children:cs}).length,0);
 });
 test('random valid contractions preserve all intersecting painter pairs',()=>{
  let seed=81;const rnd=()=>((seed=(seed*1664525+1013904223)>>>0)/4294967296);
  for(let trial=0;trial<300;trial++){
   const cs=Array.from({length:18},(_,i)=>n(String(i),rnd()*500,rnd()*500));
   const ids=cs.filter(()=>rnd()<.3).map(n=>n.id);if(!ids.length)continue;
   const slot=r.insertion(cs,ids);if(slot===null)continue;
   const next=cs.slice();next.splice(slot,0,{id:'GROUP'});
   const flattened=next.flatMap(n=>n.id==='GROUP'?cs.filter(n=>ids.includes(n.id)):ids.includes(n.id)?[]:[n]);
   for(let i=0;i<cs.length;i++)for(let j=i+1;j<cs.length;j++)if(core.intersects(cs[i],cs[j]))assert(flattened.indexOf(cs[i])<flattened.indexOf(cs[j]));
  }
 });
 test('overlay contents never borrow underlying card containers',()=>{
  const cs=[n('card',10,500,170,260),n('old-label',20,520,100,20,{type:'Text'}),n('dim',0,0,375,812),n('sheet',0,540,375,272),n('male',140,600,30,20,{type:'Text'}),n('female',270,600,30,20,{type:'Text'})];
  const plans=r.plans({type:'Artboard',width:375,height:812,children:cs});
  assert.equal(plans.length,1);assert(plans[0].overlay);assert.deepEqual(plans[0].ids,['dim','sheet','male','female']);
 });
 test('locked overlay is preserved rather than guessed across layers',()=>{
  const cs=[n('card',10,500,170,260),n('dim',0,0,375,812),n('sheet',0,540,375,272,{locked:true}),n('label',140,600,30,20,{type:'Text'})];
  assert.deepEqual(r.plans({type:'Artboard',width:375,height:812,children:cs}),[]);
 });
 return {passed};
};
