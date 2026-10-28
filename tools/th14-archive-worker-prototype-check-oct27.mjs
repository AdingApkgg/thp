import {readFile, writeFile} from 'node:fs/promises';
import {Worker} from 'node:worker_threads';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {resolve, sep} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';

const root = fileURLToPath(new URL('../', import.meta.url));
const args = process.argv.slice(2);
assert.equal(args.length, 2, 'Usage: node tools/th14-archive-worker-prototype-check-oct27.mjs --home BUILD');
assert.equal(args[0], '--home');
const home = resolve(args[1]);
assert.ok(home.startsWith(resolve(root, 'artifacts/th14')+sep));
const local = name => pathToFileURL(resolve(home, name));
const checker = await readFile(fileURLToPath(import.meta.url));
await writeFile(local('run-check.mjs'), checker, {flag:'wx'});
const {default:createModule} = await import(local('archive-decoder.mjs'));
const {ArchiveDecodeClient} = await import(local('archive-decode-client.mjs'));
const build = JSON.parse(await readFile(local('build.json'), 'utf8'));

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const openedWorkers = new Set();
function client() {
  const worker = new Worker(local('archive-decode-worker.mjs'), {type:'module'});
  const value = new ArchiveDecodeClient(worker);openedWorkers.add(value);return value;
}
const begin = performance.now();let report;
const deadline = setTimeout(() => {for (const worker of openedWorkers) worker.close();}, 60000);
try {
  assert.equal(sha(await readFile(local('archive-decoder.wasm'))), build.wasmSha256);
  assert.equal(sha(await readFile(local('archive-decoder.mjs'))), build.loaderSha256);
  const archive = new Uint8Array(await readFile('H:/Games/th/14/th14.dat'));
  assert.equal(archive.byteLength, 90776747);
  assert.equal(sha(archive), '57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233');
  const direct = await createModule();
  const input = direct._malloc(archive.length);direct.HEAPU8.set(archive, input);
  const count = direct._decoder_open(input, archive.length);assert.equal(count, 227);
  const names = Array.from({length:count}, (_, i) => direct.UTF8ToString(direct._decoder_name(i)));
  const worker = client();assert.equal(await worker.open(archive), count);
  assert.equal(archive.byteLength, 90776747, 'Original buffer must not be detached');
  const comparisons = [];let responsivePulses = 0, totalPulses = 0, decodedBytes = 0;
  for (let index = 0; index < names.length; index += 4) {
    const batch = names.slice(index, index+4);let pulses = 0;
    const interval = setInterval(() => {pulses++;totalPulses++;}, 1);
    let entries;
    try {entries = await worker.decode(batch);} finally {clearInterval(interval);}
    responsivePulses += Number(pulses > 0);
    for (const entry of entries) {
      const name = new TextEncoder().encode(entry.name), p = direct._malloc(name.length);
      direct.HEAPU8.set(name, p);
      const pointer = direct._decoder_read(p, name.length);direct._free(p);
      assert.ok(pointer, entry.name);
      const size = direct._decoder_size();assert.equal(size, entry.bytes.length);
      assert.equal(Buffer.compare(Buffer.from(direct.HEAPU8.subarray(pointer, pointer+size)),
        Buffer.from(entry.bytes)), 0, entry.name);
      comparisons.push({name:entry.name, bytes:size, sha256:sha(entry.bytes)});decodedBytes += size;
    }
  }
  assert.ok(totalPulses > 0 && responsivePulses > 0, 'Main event loop must keep running during real worker decoding');
  const intact = await worker.decode(['st03enm.anm']);
  const before = sha(intact[0].bytes);intact[0].bytes.fill(0);
  assert.equal(sha((await worker.decode(['st03enm.anm']))[0].bytes), before, 'Reply buffers must not alias the codec output');
  await assert.rejects(worker.decode(['__missing__']), /Entry rejected/);
  await assert.rejects(worker.decode([]), /Invalid decode batch/);
  assert.equal(sha((await worker.decode(['st03enm.anm']))[0].bytes), before, 'A rejected request must not wedge later jobs');
  // A fresh worker has a different codec history. Every raw archive entry
  // must remain equal even when the requests arrive in reverse table order.
  const reverse = client();assert.equal(await reverse.open(archive), count);
  let reverseComparisons = 0;
  const expectedByName = new Map(comparisons.map(entry => [entry.name, entry]));
  for (let index = names.length; index > 0; index -= 4) {
    const batch = names.slice(Math.max(0, index-4), index).reverse();
    for (const entry of await reverse.decode(batch)) {
      const expected = expectedByName.get(entry.name);
      assert.equal(entry.bytes.length, expected.bytes);assert.equal(sha(entry.bytes), expected.sha256);
      reverseComparisons++;
    }
  }
  reverse.close();assert.equal(reverseComparisons, 227);
  const invalid = client();await assert.rejects(invalid.open(new Uint8Array([0])), /Archive rejected/);invalid.close();
  const pending = worker.decode(['st03enm.anm']);
  const cancelled = assert.rejects(pending, /cancelled/);worker.close();await cancelled;
  await assert.rejects(worker.decode(['st03enm.anm']), /not ready/);
  const resumed = client();assert.equal(await resumed.open(archive), 227);
  assert.equal(sha((await resumed.decode(['st03enm.anm']))[0].bytes), before);
  resumed.close();direct._decoder_close();direct._free(input);
  assert.equal(sha(archive), '57d84a5cbe82460931cca26f090a0fde7aef180889ce5bfe8315851fc97b0233');
  const sourceBindings = {};
  for (const name of ['archive-decoder.cpp','archive-decode-client.mjs','archive-decode-endpoint.mjs',
      'archive-decode-worker.mjs','archive-decoder.wasm','archive-decoder.mjs','run-check.mjs','build-tool.py','storage-tool.py','build.json']) {
    const raw = await readFile(local(name));sourceBindings[name] = {bytes:raw.length, sha256:sha(raw)};
  }
  for (const [name, row] of Object.entries(build.sourceBindings)) {
    // Core inputs come from the published snapshot. In particular, the
    // unrelated local ResourceCrypt.cpp must never replace that input.
    const path = name.startsWith('runtimes/th12/th12_web/cpp/game/') ? resolve(home, 'source', name.split('/').at(-1)) :
      name.startsWith('runtimes/th12/portable/sdl/') ? resolve(home,name.split('/').at(-1)) : resolve(root, name);
    const raw = await readFile(path);assert.equal(sha(raw), row.sha256, name);
  }
  assert.ok(performance.now()-begin < 60000, 'Worker prototype wall budget exhausted');
  report = {passed:true, actualIndependentWorkerThread:true, archiveEntries:227, directByteComparison:true,
    comparedDecodedBytes:decodedBytes, comparisons, reverseOrderComparisons:reverseComparisons,
    reverseOrderComparedBytesViaSavedDigests:decodedBytes, reverseOrderIsDirectByteComparison:false,
    responsiveBatches:responsivePulses,
    mainEventLoopPulsesDuringWorkerRequests:totalPulses, immutableInputUnchanged:true,
    distinctTransferredOutputBuffers:true, malformedArchiveRejected:true, missingResourceRejected:true,
    emptyBatchRejected:true, subsequentJobAfterRejectionPassed:true, cancellationRejectedPendingJob:true,
    freshWorkerAfterCancellationPassed:true, sourceBindings, elapsedSeconds:(performance.now()-begin)/1000,
    productionIntegrated:false, browserAcceptance:false, actualGameWorkerScheduleAcceptance:false,
    completeGame:false, nativeEquivalent:false};
} catch (error) {
  report = {passed:false, error:String(error.stack ?? error), elapsedSeconds:(performance.now()-begin)/1000,
    productionIntegrated:false, browserAcceptance:false, completeGame:false, nativeEquivalent:false};
  process.exitCode = 1;
} finally {
  clearTimeout(deadline);
  for (const worker of openedWorkers) worker.close();
}
await writeFile(local('check.json'), JSON.stringify(report, null, 2)+'\n', {flag:'wx'});
const {comparisons, sourceBindings, ...summary} = report;console.log(JSON.stringify(summary));
