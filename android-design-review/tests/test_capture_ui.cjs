// Run with node tests/test_capture_ui.cjs; no browser or connected device needed.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require('node:path').join(__dirname, '../static/app.js'), 'utf8');
const section = (start, end) => source.slice(source.indexOf(start), source.indexOf(end, source.indexOf(start)));
const elements = new Map();
const $ = id => {
  if (!elements.has(id)) elements.set(id, {value: '', classList: {toggle() {}}, setAttribute() {}});
  return elements.get(id);
};
const events = [];
const state = {source: 'physical', devices: [{id: 'usb', state: 'device'}], design: {id: 'design', name: '页面'}, busy: false};
const live = {view: true, playing: false, session: null, frame: null};
let failure = false;
const context = vm.createContext({state, live, $, savePromise: null, document: {querySelectorAll: () => []},
  navigationChoices: () => [], currentDesignRuns: () => [],
  window: {flushVirtualControl: async () => events.push('flush')},
  persist: async () => events.push('save'),
  refreshDevices: async () => events.push('devices'),
  renderPins: () => {}, renderViewer: () => {},
  pauseLive: () => {events.push('pause'); live.playing = false;},
  api: async (path, body) => {
    assert.equal(state.capturing, true, 'old annotation overlays must be hidden while capture is pending');
    assert.equal($('capture-loading').hidden, false);
    events.push({path, body});
    if (failure) throw Error('采集失败');
    return {id: 'new-screenshot'};
  },
  acceptRun: async run => {events.push(run.id); live.view = false;}, toast: () => {}
});
$('device').value = 'usb';
vm.runInContext(section('function ready()', 'async function bootstrap(') +
  section('async function captureScreen()', 'function renderSlides()'), context);
(async () => {
  for (const playing of [false, true]) {
    live.playing = playing;
    context.updateButtons();
    assert.equal($('capture').disabled, false, 'preview playback/frame must not gate ADB screenshots');
  }
  state.devices = [];
  context.updateButtons();
  assert.equal($('capture').disabled, true, 'disconnected device must disable capture');
  state.devices = [{id: 'usb', state: 'device'}];
  await context.captureScreen();
  assert.equal(state.capturing, false);assert.equal($('capture-loading').hidden, true);
  const request = events.find(e => e.path);
  assert.equal(request.path, '/api/capture');
  assert.equal(request.body.device, 'usb');
  assert.equal(request.body.preview_session, undefined, 'expired preview session must not break capture');
  assert.equal(events.at(-1), 'new-screenshot');
  assert.deepEqual(events.slice(0, 3), ['save', 'devices', 'pause']);
  live.view = true; failure = true;
  await assert.rejects(context.captureScreen(), /采集失败/);
  assert.equal(state.capturing, false, 'capture failure must leave the old record usable');
  context.updateButtons();
  assert.equal($('capture').disabled, false, 'failed capture must remain retryable without reconnecting preview');
  failure = false; state.source = 'virtual'; events.length = 0;
  await context.captureScreen();
  assert.equal(events[0], 'flush', 'queued emulator input must finish before capture');
  console.log('Capture UI regression checks passed');
})().catch(error => {console.error(error); process.exitCode = 1;});
