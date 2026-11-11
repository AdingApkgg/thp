import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {Th14AsyncRuntime} from '../runtimes/th12/portable/sdl/Th14AsyncRuntime.mjs';

// Exercise the shipped callback, stop/save/sync functions and actual Asyncify
// queue together. No browser, audio context, game assets or replay is opened.
const source = readFileSync(new URL('../runtimes/th12/th12_web/sdl-runtime/shell.mjs', import.meta.url), 'utf8');
const line = prefix => {
  const value = source.split('\n').find(value => value.trimStart().startsWith(prefix));
  assert.ok(value, prefix);
  return value;
};
const block = (start, end) => {
  const a = source.indexOf(start), b = source.indexOf(end, a);
  assert.ok(a >= 0 && b > a, start);
  return source.slice(a, b);
};
const production = [line('function clearKeyboard()'), line('const sync='),
  line('const coreError='), block('async function callCore(', 'const save='),
  line('const save='), block('async function closeAudio()', 'async function stop()'),
  line('async function stop()'), line('Module.onGameFrame=')].join('\n');

async function scenario({ok = 0, phase = 4, game = 'th14', saveResult = 1,
  syncFailure = false, closeFailure = false, twice = false, message = ''} = {}) {
  const calls = [], events = [], errors = [];
  const memory = new Uint8Array(new SharedArrayBuffer(1024));
  memory.set(new TextEncoder().encode(message), 32);
  const sharedAudioContext = {};
  const Module = {HEAPU8: memory, SDL3: {audioContext: sharedAudioContext}, FS: {syncfs(populate, done) {
    calls.push('sync');
    queueMicrotask(() => done(syncFailure ? new Error('IDB write failed') : null));
  }}, ccall(name) { calls.push(name); return saveResult; }};
  const runtime = Module.th14AsyncRuntime = new Th14AsyncRuntime(Module);
  const raw = {th11_phase: () => phase, th11_error: () => 32,
    th11_keys_clear: () => calls.push('clear'),
    th11_loop_stop: () => calls.push('stop'),
    th11_audio_close: () => {
      calls.push('close');
      assert.equal(Module.SDL3.audioContext, undefined, 'Do not close the launcher-owned context');
      if (closeFailure) throw new Error('close failed');
    }};
  const core = runtime.bindCore(raw);
  const context = vm.createContext({Module, core, game, TextDecoder,
    keyboard: {clear: () => calls.push('keyboard')}, parent: {__touhouAudioContext: sharedAudioContext}, window: {},
    performance: {now: () => 10}, emit: (...args) => events.push(args),
    error: error => errors.push(error.message), u32: () => new Int32Array(9)});
  vm.runInContext('let stopping=false,launched=true,storageSync=Promise.resolve(),first=false,last=0,ticks=0;\n' + production, context);
  // onGameFrame is invoked *inside* the active async frame ccall. A save must
  // wait until that callback has returned, rather than reentering Asyncify.
  await runtime.run(async () => {
    calls.push('frame');
    Module.onGameFrame(ok, 1, 1);
    if (twice) Module.onGameFrame(ok, 1, 1);
    calls.push('frame-return');
  });
  await new Promise(resolve => setImmediate(resolve));
  await runtime.tail;
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(Module.SDL3.audioContext, sharedAudioContext, 'Restore borrowed context after cleanup, including failure');
  return {calls, events: JSON.parse(JSON.stringify(events)), errors, launched: vm.runInContext('launched', context)};
}

for (const ok of [0, 1]) {
  const result = await scenario({ok, twice: true});
  assert.deepEqual(result.errors, [], 'Normal TH14 exit must not report an empty core error');
  assert.deepEqual(result.events.filter(([name]) => name === 'exit'), [['exit', {code: 0, status: 'success'}]]);
  assert.deepEqual(result.calls, ['frame', 'keyboard', 'frame-return', 'clear', 'stop', 'th11_save_scores', 'sync', 'close']);
  assert.equal(result.launched, false);
}
for (const phase of [0, 1, 2, 3, 5, 6]) {
  const result = await scenario({phase, message: 'TH14: 描画失敗'});
  assert.deepEqual(result.errors, ['TH14: 描画失敗']);
  assert.deepEqual(result.events, []);
  assert.deepEqual(result.calls, ['frame', 'frame-return']);
  assert.equal(result.launched, true);
}
// The shared shell also serves older titles; keep their false-frame handling.
const legacy = await scenario({game: 'th11', message: 'legacy failure'});
assert.deepEqual(legacy.errors, ['legacy failure']);
assert.deepEqual(legacy.events, []);
for (const [options, expected] of [
  [{saveResult: 0, message: 'score write failed'}, 'score write failed'],
  [{syncFailure: true}, 'IDB write failed'],
  [{closeFailure: true}, 'close failed'],
]) {
  const result = await scenario(options);
  assert.deepEqual(result.errors, [expected]);
  assert.deepEqual(result.events.filter(([name]) => name === 'exit'), [], 'Failed persistence/cleanup cannot claim successful exit');
  assert.equal(result.launched, true);
}
console.log(JSON.stringify({passed: true, cases: 12, actualAsyncRuntime: true, audioDevicesOpened: 0, fullGameRun: false}));
