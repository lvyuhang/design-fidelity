// Run with node tests/test_workflow_ui.cjs.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const app=fs.readFileSync(require('node:path').join(__dirname,'../static/app.js'),'utf8');
const section=(a,b)=>app.slice(app.indexOf(a),app.indexOf(b,app.indexOf(a)));
const storage=new Map(),elements=new Map(),listeners=new Map();
const $=id=>{if(!elements.has(id))elements.set(id,{value:'',textContent:'',hidden:false,disabled:false,style:{},classList:{toggle(){},remove(){},add(){}},setAttribute(){},addEventListener(event,handler){listeners.set(id+':'+event,handler);},querySelector(){return null;}});return elements.get(id);};
const state={source:'physical',devices:[],runs:[],projects:[],selections:new Map(),design:{id:'d',name:'page'},catalog:{id:'p'},busy:false};
let devices=[],requests=[],deferred;
const ctx=vm.createContext({state,live:{view:false},$,window:{},document:{querySelectorAll:()=>[],querySelector:()=>({classList:{toggle(){}}})},localStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v)},navigationChoices:()=>[],currentDesignRuns:()=>[],savePromise:null,esc:x=>x,displayDevice(){},persist:async()=>{},toast(){},render(){},revealSlide(){},leaveLive(){},history:{replaceState(){}},renderDesignBrowser(){},designChoices:()=>state.catalog.id==='p'?[{id:'d',kind:'design'}]:[{id:'other',kind:'design'}],loadDesign:async id=>state.design={id},api:async(path,body)=>{requests.push({path,body});if(path==='/api/devices')return {devices};if(path==='/api/projects/preview')return deferred;if(path.startsWith('/api/runs/'))return state.runs.find(r=>r.id===path.split('/').at(-1));},startLive:async()=>{},setTimeout,clearTimeout});
vm.runInContext(section('function ready()','async function bootstrap(')+section('async function refreshDevices()','function displayDevice(')+section('function rememberSelection()','async function acceptRun(')+section('let projectPreviewVersion=0;',"$('project-form').onsubmit="),ctx);
(async()=>{
 // Reload restores the explicit source and exact device, and never falls back to another USB phone.
 state.source='virtual';state.captureDevice='emulator-5582';ctx.rememberCaptureSource();state.source='physical';state.captureDevice='';ctx.restoreCaptureSource();assert.equal(state.source,'virtual');assert.equal(state.captureDevice,'emulator-5582');
 state.source='physical';state.captureDevice='missing-usb';devices=[{id:'other-usb',kind:'usb',state:'device'}];await ctx.refreshDevices();assert.equal($('device').value,'');assert.equal(ctx.ready(),false);
 state.captureDevice='';await ctx.refreshDevices();assert.equal($('device').value,'other-usb');
 // Switching locks all competing navigation and capture entry points.
 state.switching=true;ctx.updateButtons();for(const id of ['live-toggle','review-toggle','capture','project-select','device'])assert.equal($(id).disabled,true,id);assert.equal($('live-pause').textContent,'暂停','switching must not expand the pause button');state.switching=false;
 // A screenshot deep link remembers its exact record across project round trips.
 state.projects=[{id:'p',items:[{design_key:'d'}]},{id:'q',items:[{design_key:'other'}]}];state.runs=[{id:'older',design_id:'d',issues:[],capture:{device:{id:'emulator-5582',kind:'emulator'}}},{id:'newer',design_id:'d',issues:[]}];
 ctx.projectForDesign=id=>state.projects.find(p=>p.items.some(i=>i.design_key===id));ctx.setCatalog=p=>state.catalog=p;
 await ctx.openRun('older');await ctx.selectProject('q');await ctx.selectProject('p');assert.equal(state.design.id,'d');assert.equal(state.run.id,'older');
 storage.delete('review-capture-source');ctx.inferCaptureSource(state.run);assert.equal(state.source,'virtual');state.source='physical';state.captureDevice='chosen-usb';ctx.rememberCaptureSource();ctx.inferCaptureSource(state.run);assert.equal(state.source,'physical','opening old records must preserve an explicit source choice');
 // Changing a link invalidates an in-flight response. Closing/reopening does likewise.
 ctx.busy=async fn=>fn();$('project-url').value='link-A';let resolve;deferred=new Promise(r=>resolve=r);const pending=$('inspect-project').onclick();$('project-url').value='link-B';$('project-url').oninput();resolve({source_url:'link-A',project_name:'A',total_designs:10});await pending;assert.equal($('project-url').value,'link-B');assert.equal(state.projectPreview,null);assert.equal($('project-preview').hidden,true);
 deferred=Promise.resolve({source_url:'link-B',project_name:'B',total_designs:12});await $('inspect-project').onclick();assert.equal(state.projectPreview.project_name,'B');assert.equal($('project-preview').hidden,false);
 deferred=new Promise(r=>resolve=r);const closed=$('inspect-project').onclick();listeners.get('project-dialog:close')();resolve({source_url:'link-A',project_name:'A',total_designs:10});await closed;assert.equal(state.projectPreview,null,'closed dialogs must reject late results');
 console.log('Workflow regressions passed: source persistence, no device fallback, switch locks, exact project location, stale MCP response');
})().catch(e=>{console.error(e);process.exitCode=1;});
