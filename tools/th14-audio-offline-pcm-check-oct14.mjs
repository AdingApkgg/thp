import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {existsSync, mkdirSync, readFileSync, statSync, writeFileSync} from 'node:fs';
import {dirname, resolve} from 'node:path';

// A new private run only. No browser, Native child, Node WASI, SDL library,
// preopened directory, OS audio API, AudioContext, or playable media output.
const root = resolve(import.meta.dirname, '..');
const prepDir = resolve(root, 'artifacts/th14/audio-offline-source-prep-oct14');
const preparedPath = resolve(prepDir, 'prepared.json');
const expectedPreparation = 'ed1ab1624a46cb030d17d276fbc1e9e8b795a0ca42595d2ac556771043ec3674';
const runDir = resolve(prepDir, 'run-oct14');
const publicPath = resolve(root, 'docs/porting/th14-audio-offline-pcm-observed-oct14.json');
const privatePath = resolve(runDir, 'report.json');
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const bind = path => ({path: resolve(path).replaceAll('\\', '/'), bytes: statSync(path).size,
                       sha256: sha(readFileSync(path))});
const readJson = path => JSON.parse(readFileSync(path, 'utf8').replace(/^\uFEFF/, ''));
const writeNewJson = (path, object) => writeFileSync(path, JSON.stringify(object, null, 2) + '\n', {flag: 'wx'});
assert.equal(existsSync(runDir), false, 'Private run directory must be new');
assert.equal(existsSync(publicPath), false, 'Public receipt must be new');
assert.equal(bind(preparedPath).sha256, expectedPreparation, 'Frozen preparation changed');
const prep = readJson(preparedPath);
assert.equal(prep.prepared, true);
assert.equal(prep.executed, false);
assert.equal(prep.nativeComCases.length, 15);
assert.deepEqual(prep.futureChecks.blockPartitions, [[4096], [1,31,127,512,1024,2401]]);

// Re-read every current production binding before compiling. The object list
// comes from the recorded 141 sources, never readdir or an older engine.
const currentBindings = [];
for (const expected of [...prep.fileBindings, ...prep.currentEngine.sources,
                         ...prep.currentEngine.objects, prep.currentEngine.report,
                         prep.plannedBuild.compiler, prep.inputBindings.originalDataArchive,
                         prep.inputBindings.originalExecutable]) {
    const actual = bind(expected.path);
    assert.equal(actual.bytes, expected.bytes, `Binding size changed: ${expected.path}`);
    assert.equal(actual.sha256, expected.sha256, `Binding changed: ${expected.path}`);
    currentBindings.push(actual);
}
const engine = readJson(prep.currentEngine.report.path);
assert.equal(engine.title, 14);
assert.equal(engine.sources.length, 141);
assert.equal(Object.keys(engine.sourceHashes).length, 267);
assert.equal(prep.currentEngine.objects.length, 141);
for (const [index, name] of engine.sources.entries()) {
    assert.equal(prep.currentEngine.objects[index].path,
        resolve(dirname(prep.currentEngine.report.path), 'objects-th14', name.replaceAll('/', '_') + '.o').replaceAll('\\','/'));
}
const audioSource = readFileSync(resolve(root, 'runtimes/th12/th12_web/cpp/sdl/AudioDevice.cpp'), 'utf8');
assert.match(audioSource, /^#define MA_NO_DEVICE_IO\s*$/m);
assert.match(audioSource, /engine\.noDevice=MA_TRUE/);
assert.match(audioSource, /engine\.defaultVolumeSmoothTimeInPCMFrames=0/);
const shimPath = resolve(prepDir, 'silent-sdl/SDL3/SDL.h');
const shimSource = readFileSync(shimPath, 'utf8');
assert.match(shimSource, /#define TH14_OFFLINE_AUDIO_SHIM 1/);
assert.match(shimSource, /SDL_PutAudioStreamData[\s\S]*?return false/);
const buildArgs = [...prep.plannedBuild.arguments];
const wasmPath = resolve(runDir, 'pcm-offline.wasm');
assert.equal(buildArgs.at(-2), '-o');
assert.equal(buildArgs.filter(x => x.startsWith('-I')).length, 1);
assert.equal(buildArgs.find(x => x.startsWith('-I')), '-I' + resolve(prepDir, 'silent-sdl').replaceAll('\\','/'));
assert.equal(buildArgs.filter(x => x.endsWith('.o')).length, 141);
assert.equal(buildArgs.filter(x => x.endsWith('.cpp')).length, 2);
assert.deepEqual(prep.plannedBuild.linkedSdlLibraries, []);
assert.ok(!buildArgs.some(x => /(^-l|\.lib$|\.a$|\.dll$|\.so$)/i.test(x)), 'No library/audio linkage');
buildArgs[buildArgs.length - 1] = wasmPath;
mkdirSync(runDir);
writeNewJson(resolve(runDir, 'bindings-before.json'), {prepared: bind(preparedPath), files: currentBindings});
writeNewJson(resolve(runDir, 'compile-command.json'), {compiler: prep.plannedBuild.compiler, arguments: buildArgs});
console.log('PREP current source 267 / explicit objects 141; private silent AudioDevice compile');

const report = {
    kind: 'th14-private-offline-audio-pcm-observation', startedAt: new Date().toISOString(),
    executionCompleted: false, completeGame: false, nativeEquivalent: false,
    prepared: bind(preparedPath), tool: bind(import.meta.filename),
    actualNativeProcessesStarted: 0, originalInstructionsExecuted: 0,
    browserAudioContextsCreated: 0, audioHardwareDevicesOpened: 0, audioPlayed: false,
    gameReplayCallbacksExecuted: 0, productionSourceChanged: false,
    currentSourceBindings: 267, explicitObjectBindings: 141,
    audioFramesMixed: 0, pcmWordsMixed: 0, imports: [], importedCalls: {},
    nativeIntegerInputCases: 15, mandatoryComparisons: [], specModelComparisons: [],
    compileExecuted: false,
    sdlBoundaryCounterNames: ['stubInit','stubOpen','stubResume','stubPause','stubDestroy',
                              'rejectedPutCalls','rejectedPutBytes','invalidSpec'],
    scope: 'Actual unchanged production AudioDevice/miniaudio, original archive samples, private '
        + 'non-playing SDL shim and closed memory-only WASI imports. Whole-buffer vs split and '
        + 'queued path vs 15 saved original COM integer commands. Attenuation controls are an '
        + 'independent documented-semantics float model, not original DirectSound PCM. No Native '
        + 'audio/device/resampling/physical latency or whole-game 1:1 claim.'
};
let c;
let memory;
const abiCalls = Object.create(null);
try {
    const compilerOutput = execFileSync(prep.plannedBuild.compiler.path, buildArgs, {
        cwd: root, windowsHide: true, env: {...process.env, TEMP: runDir, TMP: runDir, TMPDIR: runDir},
        encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], timeout: 180000, maxBuffer: 16*1024*1024
    });
    writeFileSync(resolve(runDir, 'compiler-stdout.txt'), compilerOutput, {flag: 'wx'});
    report.compileExecuted = true;
    report.wasm = bind(wasmPath);
    const module = new WebAssembly.Module(readFileSync(wasmPath));
    report.imports = WebAssembly.Module.imports(module);
    const allowed = new Set(['fd_close','fd_fdstat_get','fd_fdstat_set_flags','fd_prestat_get',
        'fd_prestat_dir_name','fd_read','fd_seek','fd_write','path_open','proc_exit']);
    for (const entry of report.imports) {
        assert.equal(entry.module, 'wasi_snapshot_preview1', 'Unexpected import module');
        assert.equal(entry.kind, 'function', 'Unexpected non-function import');
        assert.ok(allowed.has(entry.name), `Rejected OS/audio/unknown import: ${entry.name}`);
    }
    const call = name => { abiCalls[name] = (abiCalls[name] ?? 0) + 1; };
    const put32 = (p, value) => {
        assert.ok(memory && Number.isInteger(p) && p >= 0 && p + 4 <= memory.buffer.byteLength);
        new DataView(memory.buffer).setUint32(p, value, true);
    };
    // All file/device access fails closed in this host. No imported operation
    // calls Node/fs, WASI, an OS device, a subprocess, or a playback API.
    const closed = Object.fromEntries([...allowed].map(name => [name, (...args) => {
        call(name);
        if (name === 'proc_exit') throw new Error(`Guest requested proc_exit(${args[0]})`);
        if (name === 'fd_read' || name === 'fd_write') put32(args[3], 0);
        if (name === 'path_open') { put32(args[8], 0xffffffff); return 76; }
        return 8;
    }]));
    const instance = await WebAssembly.instantiate(module, {wasi_snapshot_preview1: closed});
    c = instance.exports; memory = c.memory;
    assert.ok(memory instanceof WebAssembly.Memory);
    assert.ok(!('pump' in c), 'No pump export permitted');
    for (const name of ['_initialize','allocate','open_archive','audio_reset','command',
                         'queued_positioned','mix','mixed_frames','sample_data',
                         'sample_bytes','sample_metadata','silent_boundary_counter'])
        assert.equal(typeof c[name], 'function', `Missing export ${name}`);
    c._initialize();
    const dat = readFileSync(prep.inputBindings.originalDataArchive.path);
    const archivePointer = c.allocate(dat.length) >>> 0;
    assert.ok(archivePointer && archivePointer + dat.length <= memory.buffer.byteLength);
    new Uint8Array(memory.buffer, archivePointer, dat.length).set(dat);
    assert.equal(c.open_archive(archivePointer, dat.length), 1, 'Original archive/audio initialize');

    const savePcm = (name, data) => {
        const path = resolve(runDir, name + '.f32');
        writeFileSync(path, Buffer.from(data.buffer, data.byteOffset, data.byteLength), {flag: 'wx'});
        return bind(path);
    };
    const mix = frames => {
        assert.ok(frames > 0 && frames <= 4096);
        const pointer = c.mix(frames) >>> 0;
        assert.ok(pointer && pointer + frames * 8 <= memory.buffer.byteLength, 'PCM memory bound');
        assert.equal(c.mixed_frames(), frames);
        const data = new Float32Array(memory.buffer, pointer, frames * 2).slice();
        assert.ok(data.every(Number.isFinite), 'Actual PCM must be finite');
        report.audioFramesMixed += frames; report.pcmWordsMixed += data.length;
        return data;
    };
    const reset = () => { assert.equal(c.audio_reset(), 1); c.stop_all(); };
    const commands = row => { for (const [kind, voice, value] of row.fixtureCommands)
        assert.equal(c.command(kind, voice, value), 1, 'Saved native integer command accepted'); };
    const stats = data => {
        const channelEnergy = [0, 0]; let peak = 0, nonzero = 0;
        for (const [index, value] of data.entries()) {
            channelEnergy[index & 1] += value * value;
            peak = Math.max(peak, Math.abs(value)); if (value !== 0) ++nonzero;
        }
        return {words: data.length, nonzeroWords: nonzero, peak, channelEnergy};
    };
    const compare = (name, actual, expected) => {
        assert.equal(actual.length, expected.length);
        const a = new Uint32Array(actual.buffer, actual.byteOffset, actual.length);
        const b = new Uint32Array(expected.buffer, expected.byteOffset, expected.length);
        const unequal = []; let maxAbsoluteError = 0;
        for (let index = 0; index < a.length; ++index) if (a[index] !== b[index]) {
            unequal.push({word: index, actual: a[index], expected: b[index]});
            maxAbsoluteError = Math.max(maxAbsoluteError, Math.abs(actual[index] - expected[index]));
        }
        const differencePath = resolve(runDir, name + '-difference.json');
        writeNewJson(differencePath, {allComparedWords: a.length, unequal, maxAbsoluteError});
        return {name, words: a.length, equal: unequal.length === 0, unequalWords: unequal.length,
            maxAbsoluteError, actualSha256: sha(Buffer.from(a.buffer, a.byteOffset, a.byteLength)),
            expectedSha256: sha(Buffer.from(b.buffer, b.byteOffset, b.byteLength)),
            difference: bind(differencePath)};
    };
    const samples = new Map();
    for (const selected of prep.selectedSamples) {
        const pointer = c.sample_data(selected.voice) >>> 0;
        const length = c.sample_bytes();
        assert.ok(pointer && pointer + length <= memory.buffer.byteLength);
        const bytes = Buffer.from(new Uint8Array(memory.buffer, pointer, length));
        assert.equal(sha(bytes), selected.binding.sha256, 'Actual archive sample matches original WAV');
        const metaPointer = c.sample_metadata() >>> 0;
        const metadata = Array.from(new Uint32Array(memory.buffer, metaPointer, 12));
        const fields = selected.fields;
        assert.deepEqual(metadata.slice(0,8), [selected.definition.sample, fields.format, fields.channels,
            fields.sampleRate, fields.blockAlign, fields.bitsPerSample, fields.dataBytes, fields.sourceFrames]);
        assert.equal(metadata[9], fields.dataOffset);
        assert.equal(metadata[10], selected.definition.loop);
        samples.set(selected.voice, {bytes, fields, metadata});
    }
    writeNewJson(resolve(runDir, 'native-inputs-private.json'), prep.nativeComCases);
    for (const [index, row] of prep.nativeComCases.entries()) {
        const label = `case-${String(index).padStart(2,'0')}`;
        reset(); commands(row); const whole = mix(4096);
        reset(); commands(row); const split = new Float32Array(8192); let offset = 0;
        for (const frames of prep.futureChecks.blockPartitions[1]) {
            const part = mix(frames); split.set(part, offset); offset += part.length;
        }
        assert.equal(offset, 8192);
        reset(); assert.equal(c.queued_positioned(row.voice, row.queuedPositionedX, row.master), 1);
        const queued = mix(4096);
        assert.ok(stats(whole).nonzeroWords > 0, 'Actual original sample prefix must produce nonzero PCM');
        const buffers = {whole: savePcm(label + '-whole', whole), split: savePcm(label + '-split', split),
                         queued: savePcm(label + '-queued', queued)};
        const splits = compare(label + '-split', split, whole);
        const queue = compare(label + '-queued', queued, whole);
        report.mandatoryComparisons.push({index, inputSha256: sha(Buffer.from(JSON.stringify(row))),
            buffers, stats: stats(whole), split: splits, queued: queue});
    }

    // Original voice3 is stereo PCM16/44100, so this bounded semantic model
    // needs no resampler. It is deliberately not a DirectSound PCM oracle.
    const controlVoice = prep.futureChecks.formatControlVoice;
    const sample = samples.get(controlVoice);
    assert.equal(sample.fields.format, 1); assert.equal(sample.fields.channels, 2);
    assert.equal(sample.fields.bitsPerSample, 16); assert.equal(sample.fields.sampleRate, 44100);
    const controlCases = [
        ...prep.futureChecks.controlPanDb100.map(pan => ({pan, db: 0})),
        ...prep.futureChecks.controlVolumeDb100.filter(db => db !== 0).map(db => ({pan: 500, db}))
    ];
    const gain = db => Math.fround(10 ** Math.fround(db / 2000));
    for (const [index, row] of controlCases.entries()) {
        reset(); for (const command of [[0,0],[1,0],[2,row.pan],[3,row.db],[4,0]])
            assert.equal(c.command(command[0], controlVoice, command[1]), 1);
        const actual = mix(4096), expected = new Float32Array(8192);
        for (let frame = 0; frame < 4096 && frame < sample.fields.sourceFrames; ++frame) {
            for (let channel = 0; channel < 2; ++channel) {
                const decoded = Math.fround(sample.bytes.readInt16LE(sample.fields.dataOffset + frame * 4 + channel * 2) / 32768);
                const attenuate = row.pan > 0 ? channel === 0 : row.pan < 0 ? channel === 1 : false;
                const withVolume = Math.fround(decoded * gain(row.db));
                expected[frame * 2 + channel] = Math.fround(withVolume * (attenuate ? gain(-Math.abs(row.pan)) : 1));
            }
        }
        const label = `semantic-${String(index).padStart(2,'0')}`;
        const buffers = {actual: savePcm(label + '-actual', actual), expected: savePcm(label + '-model', expected)};
        const result = compare(label, actual, expected);
        report.specModelComparisons.push({index, inputSha256: sha(Buffer.from(JSON.stringify(row))),
            reference: 'Independent original PCM16 decode and documented attenuation float model; not Native PCM',
            buffers, stats: stats(actual), comparison: result});
    }
    report.sdlBoundaryCounters = Array.from({length:8}, (_, index) => c.silent_boundary_counter(index));
    assert.equal(report.sdlBoundaryCounters[5], 0, 'SDL Put call count must stay zero');
    assert.equal(report.sdlBoundaryCounters[6], 0, 'SDL Put bytes must stay zero');
    assert.equal(report.sdlBoundaryCounters[7], 0, 'All initialization specs must be valid');
    report.importedCalls = {...abiCalls};
    assert.equal(abiCalls.path_open ?? 0, 0, 'No guest file open');
    assert.equal(abiCalls.fd_write ?? 0, 0, 'No guest output write');
    assert.equal(abiCalls.fd_read ?? 0, 0, 'No guest input read');
    assert.equal(abiCalls.proc_exit ?? 0, 0, 'No guest process exit');
    report.sourceBindingsAfter = currentBindings.map(before => {
        const after = bind(before.path); assert.equal(after.sha256, before.sha256, 'Bound source/object changed during run');
        return after;
    });
    report.executionCompleted = true;
    report.requiredControlsPassed = report.mandatoryComparisons.every(row => row.split.equal && row.queued.equal);
    report.semanticModelRawWordEquality = report.specModelComparisons.every(row => row.comparison.equal);
    report.passed = report.requiredControlsPassed && report.semanticModelRawWordEquality;
    report.negativeComparisonsRetained = report.mandatoryComparisons.filter(row => !row.split.equal || !row.queued.equal).length
        + report.specModelComparisons.filter(row => !row.comparison.equal).length;
    report.completedAt = new Date().toISOString();
} catch (error) {
    report.importedCalls = {...abiCalls};
    report.passed = false; report.failure = {name:error.name, message:error.message, stack:error.stack};
    if (error.stdout) writeFileSync(resolve(runDir, 'compiler-failed-stdout.txt'), error.stdout, {flag:'wx'});
    if (error.stderr) writeFileSync(resolve(runDir, 'compiler-failed-stderr.txt'), error.stderr, {flag:'wx'});
    report.completedAt = new Date().toISOString();
}
writeNewJson(privatePath, report);
const summaryComparison = comparison => ({words:comparison.words, equal:comparison.equal,
    unequalWords:comparison.unequalWords, maxAbsoluteError:comparison.maxAbsoluteError,
    actualSha256:comparison.actualSha256, expectedSha256:comparison.expectedSha256,
    differenceSha256:comparison.difference.sha256});
const publicReport = {...report,
    privateReport: bind(privatePath), currentBindingsSha256: bind(resolve(runDir,'bindings-before.json')).sha256,
    mandatoryComparisons: report.mandatoryComparisons.map(row => ({index:row.index, inputSha256:row.inputSha256,
        bufferHashes:Object.fromEntries(Object.entries(row.buffers).map(([name,value])=>[name,value.sha256])),
        stats:row.stats, split:summaryComparison(row.split), queued:summaryComparison(row.queued)})),
    specModelComparisons: report.specModelComparisons.map(row => ({index:row.index, inputSha256:row.inputSha256,
        reference:row.reference, stats:row.stats, comparison:summaryComparison(row.comparison)}))
};
delete publicReport.sourceBindingsAfter;
if (publicReport.failure) publicReport.failure = {name:publicReport.failure.name, message:publicReport.failure.message};
writeNewJson(publicPath, publicReport);
console.log(JSON.stringify({executionCompleted:report.executionCompleted, passed:report.passed,
    requiredControlsPassed:report.requiredControlsPassed, semanticModelRawWordEquality:report.semanticModelRawWordEquality,
    negativeComparisonsRetained:report.negativeComparisonsRetained,
    audioHardwareDevicesOpened:0, pcmWordsMixed:report.pcmWordsMixed,
    publicReceipt:bind(publicPath), privateReceipt:bind(privatePath)}));
if (!report.executionCompleted || !report.requiredControlsPassed) process.exitCode = 1;
