const a=require('node:assert/strict'),p=require('../LayerPilot.sketchplugin/Contents/Sketch/lib/pixels');
module.exports=function(){let passed=0;function test(n,f){f();passed++;}function im(){return {width:100,height:100,channels:4,alpha:2,data:new Uint8Array(40000)};}
test('exact pixels pass',()=>a(p.compare(im(),im()).ok));
test('one-level differences below 0.05% are reported',()=>{const b=im();b.data[0]=1;const r=p.compare(im(),b);a(r.ok&&r.subtle&&r.changed===1);});
test('two-level difference fails',()=>{const b=im();b.data[0]=2;a(!p.compare(im(),b).ok);});
test('alpha change fails',()=>{const b=im();b.data[3]=1;a(!p.compare(im(),b).ok);});
test('broad one-level changes fail',()=>{const b=im();for(let i=0;i<6;i++)b.data[i*4]=1;a(!p.compare(im(),b).ok);});
test('unknown TIFF fails closed',()=>a.throws(()=>p.decode(new Uint8Array(32))));test('chunk checkpoints preserve pixel comparison result',()=>{let ticks=0;const v={width:512,height:512,channels:4,alpha:2,data:new Uint8Array(512*512*4)};a.deepEqual(p.compare(v,v,()=>ticks++),p.compare(v,v));a(ticks>=16);});return {passed};};
