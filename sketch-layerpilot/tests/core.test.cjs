const assert = require('node:assert/strict');
const c = require('../LayerPilot.sketchplugin/Contents/Sketch/lib/core');
module.exports = function run() {
  let passed=0;
  function test(name,fn){fn();passed++;}
  function n(id,x,y,width=20,height=20,extra={}){return Object.assign({id,name:id,type:'ShapePath',x,y,width,height,children:[]},extra);}
  test('painter order for overlapping shapes is preserved',()=>{
    const nodes=[n('a',0,0,40,40),n('b',20,20,40,40),n('c',0,150)];
    const order=c.sortedOrder(nodes);assert(order.indexOf('a')<order.indexOf('b'));assert.equal(order[0],'c');
  });
  test('mask chains are never reordered',()=>{
    const nodes=[n('a',0,0,20,20,{mask:true}),n('b',0,150)];assert.deepEqual(c.sortedOrder(nodes),['a','b']);
  });
  test('artboard mask-break flags do not suppress descendant resources',()=>{
    const image=n('photo',0,0,50,50,{type:'Image'});
    const page=n('page',0,0,500,500,{type:'Page',children:[n('board',0,0,100,100,{type:'Artboard',isFrame:true,breakMask:true,exportable:true,children:[image]})]});
    assert.deepEqual(c.discover([page]).assets.map(a=>a.node.id),['photo']);
  });
  test('mask chains affect only following siblings until a break',()=>{
    const nodes=[n('before',0,0,10,10,{type:'Image'}),n('mask',0,0,40,40,{mask:true}),n('masked',0,0,50,50,{type:'Image'}),n('after',0,0,50,50,{type:'Image',breakMask:true}),n('last',0,0,50,50,{type:'Image'})];
    assert.deepEqual(c.maskedSiblings(nodes),[false,true,true,false,false]);
    const parent=n('layout',0,0,400,400,{type:'Group',children:nodes.concat(n('label',0,100,50,20,{type:'Text'}))});
    assert.deepEqual(c.discover([parent]).assets.map(a=>a.node.id),['before','after','last']);
  });
  test('locked layers form reorder barriers',()=>{
    const nodes=[n('a',0,0),n('b',0,50,20,20,{locked:true}),n('c',0,100)];assert.deepEqual(c.sortedOrder(nodes),['a','b','c']);
  });
  test('two cards are grouped independently',()=>{
    const nodes=[n('bg1',0,0,150,100),n('label1',10,10,100,20,{type:'Text'}),n('bg2',180,0,150,100),n('label2',190,10,100,20,{type:'Text'})];
    assert.deepEqual(c.planGroups({width:400,height:300,children:nodes},16),[['bg1','label1'],['bg2','label2']]);
  });
  test('noncontiguous group cannot cross an unrelated painter',()=>{
    const nodes=[n('a',0,0),n('outside',200,200),n('b',25,0)];assert.equal(c.planGroups({width:400,height:400,children:nodes},16).length,0);
  });
  test('stack and generated groups are not regrouped',()=>{
    const nodes=[n('a',0,0),n('b',25,0),n('c',300,300)];
    assert.equal(c.planGroups({width:400,height:400,stack:true,children:nodes},16).length,0);
    nodes[0].generated=true;assert.equal(c.planGroups({width:400,height:400,children:nodes},16).length,0);
  });
  test('asset recognition excludes text, layout, ordinary rectangles',()=>{
    assert.equal(c.resourceKind(n('x',0,0,24,24,{type:'Text',name:'icon/text'})),null);
    assert.equal(c.resourceKind(n('x',0,0,24,24,{name:'Rectangle 1'})),null);
    assert.equal(c.resourceKind(n('x',0,0,24,24,{name:'button',children:[]})),null);
    assert.equal(c.resourceKind(n('x',0,0,24,24,{name:'icon/home'})),'icon');
    assert.equal(c.resourceKind(n('x',0,0,24,24,{name:'icon/home',exportable:true})),'icon');
    assert.equal(c.resourceKind(n('x',0,0,200,200,{type:'Image'})),'image');
    assert.equal(c.resourceKind(n('x',0,0,100,100,{imageFill:true})),'image');
  });
  test('parent resources suppress duplicate child exports',()=>{
    const group=n('g',0,0,24,24,{type:'Group',name:'icon/home',children:[n('path',0,0)]});assert.equal(c.discover([group]).assets.length,1);
  });
  test('masked images export enclosing group, not unclipped child',()=>{
    const mask=n('mask',0,0,100,100,{mask:true});const image=n('photo',0,0,100,100,{type:'Image'});
    const group=n('g',0,0,100,100,{type:'Group',children:[mask,image]});assert.equal(c.discover([group]).assets[0].node.id,'g');
    image.ancestorMask=true;assert.equal(c.discover([image]).assets.length,0);
  });
  test('business names and exported filenames are preserved',()=>{
    assert.equal(c.rename(n('x',0,0,10,10,{name:'确认支付',type:'Text',text:'付钱'})),'确认支付');
    assert.equal(c.rename(n('x',0,0,10,10,{name:'Text 1',type:'Text',text:'确认支付'})),'文本 / 确认支付');
    assert.equal(c.rename(n('x',0,0,10,10,{name:'Text 1',type:'Text',exportable:true,text:'确认支付'})),'Text 1');
  });
  test('clipping and rounded corners cannot leak uncropped assets',()=>{
    const image=n('photo',-20,-20,80,80,{type:'Image'});
    const clip=n('clip',0,0,40,40,{type:'Group',isFrame:true,clipsContents:true,children:[image]});
    assert.equal(c.discover([clip]).assets[0].node.id,'clip');
    clip.children.push(n('title',0,0,30,10,{type:'Text'}));
    assert.equal(c.discover([clip]).assets.length,0);
    assert(c.cropRisk({width:100,height:100,clipsContents:true,cornerRadius:20},n('x',0,0,10,10)));
    assert(!c.cropRisk({width:100,height:100,clipsContents:true,cornerRadius:20},n('x',30,30,10,10)));
  });
  test('generated layout groups stay layouts and photo symbols stay raster',()=>{
    assert.equal(c.resourceKind(n('g',0,0,50,50,{type:'Group',generated:true,children:[n('a',0,0),n('b',25,0)]})),null);
    assert.equal(c.resourceKind(n('a',0,0,50,50,{name:'avatar/user',type:'SymbolInstance'})),'image');
  });
  test('safe filenames retain Chinese and stable full IDs',()=>{
    const result=c.filename('../../图 标:foo/CON','A-B-C');assert(!result.includes('/'));assert(!result.startsWith('.'));assert(result.includes('图_标'));assert(result.endsWith('_abc'));
    assert.notEqual(c.filename('x','ABCDEFGH-1'),c.filename('x','ABCDEFGH-2'));
  });
  test('sorting is idempotent across random overlaps',()=>{
    let state=31;const rand=()=>{state=(state*1664525+1013904223)>>>0;return state/4294967296;};
    for(let k=0;k<100;k++){
      const nodes=Array.from({length:20},(_,i)=>n(String(i),Math.floor(rand()*100),Math.floor(rand()*100)));
      const sorted=c.sortedOrder(nodes);const again=c.sortedOrder(sorted.map(id=>nodes.find(n=>n.id===id)));assert.deepEqual(again,sorted);
      for(let i=0;i<nodes.length;i++)for(let j=i+1;j<nodes.length;j++)if(c.intersects(nodes[i],nodes[j]))assert(sorted.indexOf(nodes[i].id)<sorted.indexOf(nodes[j].id));
    }
  });
  return {passed};
};
