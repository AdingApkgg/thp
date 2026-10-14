// Bind ordinary browser save/reload/playback observations to the frozen release.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),sha=b=>createHash('sha256').update(b).digest('hex'),evidence={};
const read=path=>{const bytes=readFileSync(resolve(root,path));evidence[path]={bytes:bytes.length,sha256:sha(bytes)};return bytes;};
const load=path=>JSON.parse(read(path));
const build=load('runtimes/th14/th14_web/artifacts/sdl3-release/build.json');
assert.equal(build.title,14);assert(build.releaseProfile&&!build.completeGame);
for(const [name,digest] of Object.entries({...build.headers,...build.sources}))assert.equal(sha(read('runtimes/th12/'+name)),digest,name);
const wasm=read('runtimes/th14/th14_web/artifacts/sdl3-release/th11.wasm');assert.equal(sha(wasm),build.sha256);
const exports=WebAssembly.Module.exports(new WebAssembly.Module(wasm)).map(row=>row.name);
assert(!exports.some(name=>/^th11_(?:probe_|audio_probe|audio_samples|tick$)/.test(name)));
const runtimePath='docs/porting/th14-launcher-runtime-prepared-focused-growth-oct14.json';
const runtime=load(runtimePath);assert.equal(runtime.build.sha256,build.sha256);
assert.deepEqual(runtime.build.sources,build.sources);assert.deepEqual(runtime.build.headers,build.headers);
const preview=load('docs/porting/th14-launcher-preview-prepared-focused-growth-oct14.json');
assert(preview.passed&&!preview.completeGame&&!preview.nativeEquivalent);
assert.equal(preview.runtimeManifestSha256,evidence[runtimePath].sha256);
for(const [name,row] of Object.entries(preview.files)){const bytes=readFileSync(resolve(preview.site,name));assert.equal(bytes.length,row.bytes);assert.equal(sha(bytes),row.sha256,name);}
const base='artifacts/th14/browser-focused-growth-oct14/';
const screenshots=['normal-reimua-paused.jpg','replay-saved-slot01.jpg','replay-after-reload.jpg','replay-game-list-after-reload.jpg','replay-playing-after-reload.jpg','replay-returned-after-playback.jpg'];
for(const path of screenshots)assert.equal(read(base+path).subarray(0,3).toString('hex'),'ffd8ff');
assert.deepEqual(load(base+'console.json'),[]);
const consoleEntries=load(base+'console-after-playback.json');
assert.equal(consoleEntries.filter(row=>row.level==='error').length,0);
assert.equal(consoleEntries.length,1);
assert.equal(consoleEntries[0].level,'warn');
assert(consoleEntries[0].message.startsWith('App Shell update check unavailable'));
const codec=load('docs/porting/th14-browser-saved-replay-native-codec-oct14.json');
assert(codec.passed&&!codec.completeGame&&!codec.nativeEquivalent&&codec.files===1);
const row=codec.rows[0];assert(row.actualNativeCodecVerified);
assert.deepEqual([row.character,row.subtype,row.difficulty,row.stageCount],[0,0,1,1]);
assert.deepEqual([row.stages[0].stage,row.stages[0].frames],[1,468]);
assert.equal(sha(read(base+'browser-normal-recording.rpy')),row.sha256);
assert.equal(sha(read(base+'browser-normal-recording-decoded.bin')),row.decodedSha256);
assert.equal(sha(read('tools/th14-browser-saved-replay-native-codec-check.py')),codec.toolSha256);
const report={observedBrowserFlowVerified:true,completeGame:false,nativeEquivalent:false,url:'http://localhost:8207/?game=th14',
 build,filesVerified:Object.keys(preview.files).length,screenshots:screenshots.map(path=>base+path),evidence,
 replay:{bytes:row.bytes,sha256:row.sha256,frames:468,actualNativeCodecVerified:true},consoleWarnings:1,consoleErrors:0,consoleEntries,
 observations:['Ordinary attract demo -> Escape -> title -> Game Start -> Normal -> Reimu ->妖器使用 A -> stage1.',
 'Ordinary Shift+Z shooting, actual death and Escape pause.',
 'Ordinary pause Save Replay and Return to Title, confirm Yes, slot01, name A, End.',
 'Page reload retained th14_01.rpy in Launcher replay management; the downloaded bytes passed original4028e0/465840 codec comparison.',
 'A later fresh tab on the same origin retained the installed original data and slot01 A in the actual game Replay list.',
 'Ordinary Replay -> slot01 -> Stage1 played the468 recorded frames without further gameplay input and naturally returned to the game Replay list.',
 'One Launcher App Shell service-worker update-check warning retained; no captured errors. No state injection or diagnostic exports used.'],
 toolSha256:sha(readFileSync(import.meta.filename)),scope:'CUA-observed ordinary short recording, menu save, page reload, later fresh-tab persistence, selection, playback and natural return, bound to current146 sources/144 headers and127 frozen site files. Screenshots record observations and do not independently prove every intermediate action. The original codec validates file bytes, not original executable playback. Full browser clear, score persistence, whole native menus/ending, pixels/audio and whole-game1:1 remain separate. Original data/replay and screenshots remain private/local.'};
writeFileSync(resolve(root,'docs/porting/th14-focused-growth-browser-flow-verified-oct14.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({observedBrowserFlowVerified:true,sha256:build.sha256,filesVerified:report.filesVerified,replayFrames:468,consoleWarnings:1,consoleErrors:0}));
