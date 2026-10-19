const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
const source=fs.readFileSync(require('node:path').join(__dirname,'../static/app.js'),'utf8');
const code=source.slice(source.indexOf('async function acceptRun('),source.indexOf('function render(){'));
const old={id:'old',issues:[{id:'old-pin'}]},state={run:old};let fail=false,resolveImage;
const elements=new Map(['bubble-layer','pin-layer','bubble-lines'].map(id=>[id,{children:['old'],replaceChildren(){this.children=[];}}]));
elements.set('settings-dialog',{close(){}});
const context=vm.createContext({state,bubbles:new Map([['old-pin',{}]]),bubbleRun:old,$:id=>elements.get(id),Image:class{decode(){return fail?Promise.reject(Error('image failed')):new Promise(r=>resolveImage=r);}},loadDesign:async()=>{},rememberSelection(){},leaveLive(){},rememberRun(){},rememberLocation(){},history:{replaceState(){}},render(){},revealSlide(){}});
vm.runInContext(code,context);
(async()=>{
 const next={id:'new',design_id:'design',original_url:'/new.png',issues:[]};const pending=context.acceptRun(next);
 assert.equal(state.run,old,'do not commit a record before its image is ready');resolveImage();await pending;
 assert.equal(state.run,next);assert.equal(state.run.issues.length,0);assert.equal(context.bubbles.size,0);
 for(const id of ['pin-layer','bubble-layer','bubble-lines'])assert.equal(elements.get(id).children.length,0,id);
 fail=true;await assert.rejects(context.acceptRun({id:'broken'}),/image failed/);assert.equal(state.run,next,'failed capture must preserve the last committed record');
 console.log('Capture scene regression passed: decoded image, record and annotations commit together');
})().catch(e=>{console.error(e);process.exitCode=1;});
