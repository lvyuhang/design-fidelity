const a=require('node:assert/strict'),c=require('../LayerPilot.sketchplugin/Contents/Sketch/lib/canvas');
module.exports=function(){let passed=0;function test(n,f){f();passed++;}
const r=(w,h=w)=>({x:0,y:0,width:w,height:h});
test('small play has a 16 canvas',()=>a.equal(c.choose(r(8),8,'auto',[]).size,16));
test('stroke heart fits 16',()=>a.equal(c.choose(r(14.4,12.7),12,'auto',[]).size,16));
test('navigation uses 24',()=>a.equal(c.choose(r(20),20,'auto',[]).size,24));
test('larger icon uses 32',()=>a.equal(c.choose(r(26),26,'auto',[]).size,32));
test('heart does not touch 98',()=>{const v=c.choose({x:-1.2,y:-1.2,width:14.4,height:12.7},12,'auto',[{x:17,y:-2,width:12,height:14}]);a.equal(v.size,16);a(!c.overlap(v.frame,{x:17,y:-2,width:12,height:14}));});
test('automatic drops one tier to avoid text',()=>a.equal(c.choose(r(15),15,'auto',[{x:17,y:0,width:20,height:15}]).size,16));
test('fixed canvas collision rejected',()=>a(c.choose(r(12),12,24,[{x:17,y:0,width:20,height:15}]).error));
test('no tier fits without collision',()=>a(c.choose(r(20),20,'auto',[{x:21,y:0,width:20,height:15}]).error));
test('oversize ink rejected',()=>a(c.choose(r(18),18,16,[]).error));
test('touching edges is not overlapping',()=>a(!c.overlap(r(16),{x:16,y:0,width:2,height:2})));
return {passed};};
