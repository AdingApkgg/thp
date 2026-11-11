import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const source = readFileSync(new URL('../runtimes/th12/th12_web/sdl-runtime/shell.mjs', import.meta.url), 'utf8');
const declaration = source.split('\n').find(line => line.startsWith('const coreError='));
assert.ok(declaration, 'Use the production error reader');
for (const shared of [false, true]) {
  for (const message of ['', 'TH14: 音楽の読み込みに失敗しました']) {
    const memory = new Uint8Array(shared ? new SharedArrayBuffer(512) : new ArrayBuffer(512));
    memory.set(new TextEncoder().encode(message), 16);
    const readError = vm.runInNewContext(declaration + '\ncoreError', {
      Module: {HEAPU8: memory}, core: {th11_error: () => 16}, TextDecoder,
    });
    assert.equal(readError(), message);
  }
}
console.log(JSON.stringify({passed: true, cases: 4, sharedAndOrdinaryMemory: true, browserExecuted: false}));
